import socket
import json
import os
import time
import ipaddress
import threading as thread

sharedFolder = "Now is empty"
global close
close = 0

peers = []
queryhitip = []
flagqueryhit = 0
pongip = []
flagpong = 0

def initialize():
    global udpsocket
    udpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    global host
    host = socket.gethostname()
    global udpport 
    udpport = 20000
    udpsocket.bind((socket.gethostbyname(host), udpport))
    
    global tcpsocket 
    tcpsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    global tcpport 
    tcpport = 10000
    tcpsocket.bind((socket.gethostbyname(host), tcpport))

def isValidIP(string):
    try:
        ipaddress.ip_address(ip)
        return True
    except:
        return False
    
def numberToByte(n):
    result = bytearray()
    result.append(n & 255)
    for i in range(3):
        n = n >> 8
        result.append(n & 255)
    return result

def byteToNumber(b):
    result = 0
    for i in range(4):
        result += b[i] << (i*8)
    return result

def sendFile(connection):
    try:
        existing = connection.recv(4) #Receive size of existing file
        existing = byteToNumber(existing)
        
        filename = connection.recv(4096).decode() #Receive searched file name
        if os.path.exists(filename):
            currentLength = 0
            length = os.path.getsize(filename) - existing #Compute the difference in the size between existing file and actual file
            connection.send(numberToByte(length)) #Send the measure

            with open(filename, 'rb') as file:
                d = file.read(1024)
                    
                while d:
                    currentLength += 1024
                    if(currentLength > existing): #Skip in case that the file has the chunk (the chunks have size of 1024 Byte)
                        connection.send(d)
                        
                    d = file.read(1024)
        else:
            connection.send(numberToByte(0)) #File not existing on machine (length = 0)
    except:
        pass

def downloadFile():
    if(len(queryhitip) > 0):
        if(input("Found what you really need? Type Y for YES\n") == "Y"):
            try:
                selectedIP = input("Enter the IP address from where you want to download:\n")
                selectedSong = input("Enter the name of the file you want to download:\n")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((selectedIP, tcpport))
                
                if(os.path.isfile(selectedSong)): #If file searched still existing on the machine (may be partial), send his size
                    sock.send(numberToByte(os.path.getsize(selectedSong)))
                else:
                    sock.send(numberToByte(0)) #If not existing, send size = 0
                    
                sock.send(selectedSong.encode())
                completePath = os.path.join(sharedFolder, selectedSong)

                file = open(completePath, 'ab') #Open file in append modality
                size = sock.recv(4) #Receive the size of the chunks that will be sent
                size = byteToNumber(size)
                
                if(size == 0): #File not found on Server machine
                    raise Exception()
                    
                currentSize = 0
                while currentSize < size:
                    data = sock.recv(1024)
                    currentSize += len(data)
                    file.write(data)

                file.close()
                print("\nData has been received successfully!")

            except:
                print("\nNot able to retrieve file..")

            finally:
                try:
                    file.close()
                except:
                	pass
    else:
        print("No peer sent a response to your Query..")
    
    th = thread.Thread(target = query)
    th.start()
        
def UDPListener():
    while close == 0:
        try:
            data, ip = udpsocket.recvfrom(8192)
            data = data.decode()

            message = json.loads(data)
        
            if(message["Command"] == 1): #PING
                if(message["IP"] != socket.gethostbyname(host) and message["IP"] != "127.0.0.1"):
                    pong(message["IP"])
                    if(message["IP"] not in peers):
                        peers.append(message["IP"])
                    if(message["TTL"] > 0):
                        message["TTL"] = message["TTL"] - 1
                        message = json.dumps(message)
                        for peer in peers:
                            udpsocket.sendto(message.encode(), (peer, udpport))
                    
            elif(message["Command"] == 2 and flagpong == 0): #PONG
                pongip.append(message["IP"])
                if(message["IP"] not in peers):
                    peers.append(message["IP"])                    
                
            elif(message["Command"] == 3): #Query
                if(message["IP"] not in peers):
                    peers.append(message["IP"])

                songName = message["Contents"]
                arr = []
                for file in os.listdir():
                    if(songName.lower() in file.lower() and "." in file):
                        arr.append(file)

                data = json.dumps({"Command": 4, "Contents":arr, "IP":socket.gethostbyname(host)}) #Send QueryHit JSON file
                udpsocket.sendto(data.encode(), ip)

            elif(message["Command"] == 4 and flagqueryhit == 0): #QueryHit
                queryhitip.append(message["IP"])

                print("--------------------")
                print("| IP " + message["IP"] + " |")
                print("--------------------")
                for j in range (0, len(message["Contents"])):
                    print(str(j) + "  " + message["Contents"][j])
        except:
            pass

def TCPListener():
    tcpsocket.listen(1)
    print("Host: " + host)

    try:
        while close == 0:
            connection, address = tcpsocket.accept()
            th = thread.Thread(target = sendFile, args = (connection, ))
            th.start()
        tcpsocket.close()
    except:
        pass

def removeUnreachable():
    for val in peers:
        if(val not in pongip):
            peers.remove(val)

def timeoutPong():
    limit = 5
    start = time.perf_counter()
    
    while(time.perf_counter() - start <= limit):
        pass
    
    global flagpong
    flagpong = 1
    
    removeUnreachable()
    
def timeoutQueryHit():   
    limit = 5
    start = time.perf_counter()
    
    while(time.perf_counter() - start <= limit):
        pass
    
    global flagqueryhit
    flagqueryhit = 1
        
    th = thread.Thread(target = downloadFile)
    th.start()
       
def query():
    if(input("Do you want to continue? Type Y for YES\n") == "Y"):
        song = input(str("Enter file name:\n"))
        data = json.dumps({"Command": 3, "Contents":song, "IP": socket.gethostbyname(socket.gethostname())})
        
        global queryhitip
        queryhitip = []
        
        global flagqueryhit
        flagqueryhit = 0
    
        for peer in peers:
            udpsocket.sendto(data.encode(), (peer, udpport))
            
        th = thread.Thread(target = timeoutQueryHit)
        th.start()
    else:
        global close
        close = 1
        tcpsocket.close()
        udpsocket.close()
        
def ping():
    while close == 0:
        global pongip
        pongip = []
        
        global flagpong
        flagpong = 0
        
        for peer in peers:
            data = json.dumps({"Command": 1, "IP": socket.gethostbyname(socket.gethostname()), "TTL":1}) #Send PING JSON file
            udpsocket.sendto(data.encode(), (peer, udpport))
            
        th = thread.Thread(target = timeoutPong)
        th.start()
        time.sleep(20)

def pong(ip):
    data = json.dumps({"Command":2, "IP": socket.gethostbyname(socket.gethostname())}) #Send Pong JSON file
    udpsocket.sendto(data.encode(), (ip, udpport))


print(
" .--.          .      . .        .--.  .-. .--.    .-.   .           .                         \n"
":             _|_     | |        |   )(   )|   )   |  o  |           |             o           \n"
"| --..--. .  . |  .-. | | .-.    |--'   .' |--'   -|- .  | .-.   .--.|--. .-.  .--..  .--. .-..\n"
":   ||  | |  | | (.-' | |(   )   |     /   |       |  |  |(.-'   `--.|  |(   ) |   |  |  |(   |\n"
" `--''  `-`--`-`-'`--'`-`-`-'`-  '    '---''       '-' `-`-`--'  `--''  `-`-'`-' -' `-'  `-`-`|\n"
"                                                                                           ._.'\n")
                                                                                                
initialize()                                                                                       
th2 = thread.Thread(target = TCPListener)    
th1 = thread.Thread(target = UDPListener)

th2.start()
th1.start()

time.sleep(1)

while(not(os.path.exists(sharedFolder))):
    sharedFolder = input(str("Enter the shared folder path:\n"))

os.chdir(sharedFolder)

ip = ""

while(isValidIP(ip)  == False):
    ip = input("IP where you want to connect:\n")
    
if(ip not in peers):
    peers.append(ip)

th3 = thread.Thread(target = ping)
th3.start()

th4 = thread.Thread(target = query)
th4.start()
    
th1.join()
th2.join()


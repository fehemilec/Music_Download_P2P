import socket
import json
import os
import _thread as thread

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

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 0, length = 100, fill = '█', printEnd = "\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = printEnd)
    if iteration >= total: 
        print("\nData has been transmitted successfully!")

def client_thread():
    host = input(str("Enter the host name: "))
    while(not(host == "Quit")):
        receiverSocket = socket.socket()
        port = 10000
        receiverSocket.connect((host, port))
        print("Connected")
        sharedFolder = input(str("Enter the shared folder path: "))
        song = input(str("Enter song name: "))
        receiverSocket.send(song.encode('ascii'))
        songList = receiverSocket.recv(1024).decode('utf-8')
        parsedList = json.loads(songList)
        print("Songs found on IP " + parsedList["IP"])
        for j in range (0, len(parsedList["Contents"])):
            print(str(j) + "  " + parsedList["Contents"][j])
        selectedSong = int(input("Enter the number ID of the song you want to download: "))
        receiverSocket.send(parsedList["Contents"][selectedSong].encode('ascii'))
        filename = input(str("Enter a filename for the incoming file (without extension): "))
        completePath = os.path.join(sharedFolder, filename + "." + parsedList["Contents"][selectedSong].split(".")[1])
        file = open(completePath, 'wb')
        size = receiverSocket.recv(4) 
        size = byteToNumber(size)
        currentSize = 0
        buffer = b""
        while currentSize < size:
            data = receiverSocket.recv(1024)
            if not data:
                break
            buffer += data
            currentSize += len(data)
        file.write(buffer)
        file.close()
        print("Data has been received successfully!")

def server_thread(connection):
    songName = connection.recv(30).decode('utf-8')
    arr = []
    
    for file in os.listdir():
        if(songName in file):
            arr.append(file)
            
    data = json.dumps({"Contents":arr, "IP":socket.gethostbyname(host)})
    connection.send(data.encode())
    filename = connection.recv(30).decode('utf-8')
    if os.path.exists(path):
        currentLength = 0
        length = os.path.getsize(filename)
        printProgressBar(0, length, prefix = 'Progress:', suffix = 'Complete', length = 50)	
        connection.send(numberToByte(length))
        
        with open(filename, 'rb') as file:
            d = file.read(1024)
            while d:
                currentLength += 1024
                connection.send(d)
                d = file.read(1024)
                printProgressBar(currentLength, length, prefix = 'Progress:', suffix = 'Complete', length = 50)

ThreadCount = 0

senderSocket = socket.socket()
host = socket.gethostname()
port = 9500
senderSocket.bind((host, port))
senderSocket.listen(1)
path = "C:/Users/Savii/Desktop/UNI/Triennale/Z-Tesi"
os.chdir(path)
print("Host: " + host)
print("Waiting for connections...")
thread.start_new_thread(client_thread, ())

while True:
    connection, address = senderSocket.accept()
    print(address, " has connected")
    thread.start_new_thread(server_thread, (connection, ))
    ThreadCount += 1
    print('Thread Number: ' + str(ThreadCount))
senderSocket.close()





	
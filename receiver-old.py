import socket
import json
import os

def byteToNumber(b):
    result = 0
    for i in range(4):
        result += b[i] << (i*8)
    return result

receiverSocket = socket.socket()
host = input(str("Enter the host name: "))
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

import socket
import os

s = socket.socket()
host = socket.gethostname()
port = 12000
s.connect((host, port))
path = "client_data"
directory = os.listdir(path)

for files in directory:
    print(files)
    filename = files
    size = len(filename)
    size = bin(size)[2:].zfill(16) # encode filename size as 16 bit binary
    s.send(size.encode())
    s.send(filename.encode())

    filename = os.path.join(path,filename)
    filesize = os.path.getsize(filename)
    filesize = bin(filesize)[2:].zfill(32) # encode filesize as 32 bit binary
    s.send(filesize.encode())

    file_to_send = open(filename, 'rb')

    l = file_to_send.read()
    s.sendall(l)
    file_to_send.close()
    print('File Sent')

s.close()
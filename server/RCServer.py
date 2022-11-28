# Author: Soumil Datta

from socket import *
import os 
import threading

server_port = 12000
packet_size = 1024
current_dir = './'

def handleReceiveFiles(conn):
    while True:
        # Receive file name size
        size = conn.recv(16).decode()
        
        if not size:
            # stop receiving if nothing is being sent anymore
            break 

        size = int(size, 2)
        filename = conn.recv(size).decode()

        filesize = conn.recv(32).decode()
        filesize = int(filesize, 2)

        file = open(filename, 'wb')

        chunksize = packet_size
        while filesize > 0:
            if filesize < chunksize:
                chunksize = filesize
            
            data = conn.recv(chunksize)
            file.write(data)
            filesize -= len(data)

        file.close()
        print(f'File {filename} received successfully')

def handleSendFile(fileList, client_socket):
    for file in fileList:
        print(f'Sending {file}')

        # send filename size
        size = len(file)
        # encode size as 16 bit binary
        size = bin(size)[2:].zfill(16)
        client_socket.send(size.encode())
        client_socket.send(file.encode())

        filename = os.path.join(current_dir, file)
        filesize = os.path.getsize(file)
        filesize = bin(filesize)[2:].zfill(32)
        client_socket.send(filesize.encode())

        fileOpened = open(filename, 'rb')

        data = fileOpened.read()
        client_socket.sendall(data)
        fileOpened.close()
        print(f'File {file} sent')
        client_socket.recv(4).decode()
    
    client_socket.send('FINISHED'.encode())

#! Main thread function
def clientHandler(conn, addr):
    print(f'Client {addr} connected')
    conn.send(f'100@Connection with server established'.encode())

    # Receive command for what to do
    command = conn.recv(2).decode()

    # RECEIVE FILES FROM CLIENT
    if command == '01':
        handleReceiveFiles(conn)
    elif command == '02':
        dir_list = os.listdir(current_dir)
        dir_list.remove('RCServer.py')
        print(dir_list)
        handleSendFile(dir_list, conn)

    print(f'Client {addr} disconnected')


if __name__ == '__main__':
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('', server_port))
    server_socket.listen(1)

    print('Server started ✅')

    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=clientHandler, args=(conn, addr))
        thread.start()
        #! TEMPPORARY 
        # clientHandler(conn, addr)
# Author: Soumil Datta

from socket import *
import os 
import threading

server_port = 12000
packet_size = 1024

def clientHandler(conn, addr):
    print(f'Client {addr} connected')
    conn.send(f'100@Connection with server established'.encode())

    while True:
        size = conn.recv(16).decode()
        if not size:
            # stopped receiving
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
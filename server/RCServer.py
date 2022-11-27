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
        data = conn.recv(packet_size).decode()
        conn.send(f'Received command {data}'.encode())
        print(data)
        splitData = data.split('@')
        cmd = splitData[0]
        contents = splitData[1]

        if cmd == 'FILENAME':
            file = open(contents, 'w')
        elif cmd == 'DATA':
            file.write(contents)
        elif cmd == 'END':
            file.close()
        elif cmd == 'DONE':
            print(splitData[1])
            conn.send(f'Server has disconnected after completion'.encode())
            break
        else:
            pass

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
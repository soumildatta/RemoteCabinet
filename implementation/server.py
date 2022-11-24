import os 
from socket import *
import threading

server_port = 12001
packet_size = 1024
server_addr = ('', server_port)
server_path = 'server_data'

def handle_client(conn, addr):
    print(f'Client {addr} connected')
    conn.send(f'OK@Connection to server established'.encode())

    while True:
        data = conn.recv(packet_size).decode()
        data = data.split('@')
        cmd = data[0]
        
        elif cmd == 'LOGOUT':
            break

        elif cmd == 'LIST':
            files = os.listdir(server_path)
            sendData = 'OK@'
            if len(files) == 0:
                sendData += 'Server is empty'
            else:
                sendData += '\n'.join(f for f in files)
            conn.send(sendData.encode())

        elif cmd == 'UPLOAD':
            name = data[1]
            text = data[2]
            filepath = os.path.join(server_path, name)
            with open(filepath, 'w') as f:
                f.write(text)
            sendData = 'OK@File uploaded.'
            conn.send(sendData.encode())

        elif cmd == 'DELETE':
            files = os.listdir(server_path)
            sendData = 'OK@'
            filename = data[1]

            if len(files) == 0:
                sendData += 'Server is empty'
            else:
                if filename in files:
                    os.system(f'rm {server_path}/{filename}')
                    sendData += 'File deleted'

                else:
                    sendData += 'File not found'
            conn.send(sendData.encode())


    print(f'Client {addr} has disconnected')

def main():
    server = socket(AF_INET, SOCK_STREAM)
    server.bind(server_addr)
    server.listen(1)
    print('Server is listening')

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


if __name__ == '__main__':
    main()
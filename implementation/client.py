import os 
from socket import *
import threading

server_port = 12001
packet_size = 1024
server_addr = ('', server_port)
client_path = 'client_data'

def main():
    client = socket(AF_INET, SOCK_STREAM)
    client.connect(server_addr)

    while True:
        data = client.recv(packet_size).decode()
        cmd, msg = data.split('@')

        if cmd == 'OK':
            print(msg)
        elif cmd == 'DISCONNECTED':
            print(msg)
            break
    
        data = input("> ")
        data = data.split(" ")
        cmd = data[0]

        if cmd == 'LOGOUT':
            client.send(cmd.encode())
            break

        elif cmd == 'LIST':
            client.send(cmd.encode())

        elif cmd == 'UPLOAD':
            ## UPLOAD@filename@text
            path = 'client_data'
            files = os.listdir(path)
            client.send(f'LENGTH@{len(files)}'.encode())
            
            for file in files:
                print(file)

                with open(path, 'r') as f:
                    text = f.read()
            
                filename = path.split('/')[-1]
                sendData = f'{cmd}@{filename}@{text}'
                client.send(sendData.encode())

        elif cmd == 'DELETE':
            client.send(f'{cmd}@{data[1]}'.encode())

    print('Disconnected from server')
    client.close()

if __name__ == '__main__':
    main()
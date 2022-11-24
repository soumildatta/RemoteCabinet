# Author: Soumil Datta

from socket import *

if __name__ == '__main__':
    server_port = 12000
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('', server_port))
    server_socket.listen(1)

    while True:
        print('Server is ready to receive file')

        connection_socket, addr = server_socket.accept()

        #! Number of files to receive
        recvLen = connection_socket.recv(1024).decode()
        length = int(recvLen)
        #* Send response
        connection_socket.send(f'FROM SERVER: Received number of files to store ({length})'.encode())


        while True:
            #! Receive item 
            item = (connection_socket.recv(1024).decode())
            print(item)
            try:
                type, item = item.split(';')
            except:
                print('EXCEPTION')
                print(item)
            # connection_socket.send(f'FROM SERVER: Receiving file {item}'.encode())

            if type == 'FILENAME':
                file = open(item, 'w')
                #* Send resonse
                connection_socket.send(f'FROM SERVER: Created file {item}'.encode())

            if type == 'CONTENTS':
                file.write(item)
                #* Send resonse
                connection_socket.send(f'FROM SERVER: Writing to file'.encode())
            
            if type == 'FINISH':
                file.close()
                #* Send resonse
                connection_socket.send(f'FROM SERVER: {item}'.encode())

            if type == 'CLOSE':
                connection_socket.send(f'FROM SERVER: FINSHED'.encode())
                break
            # filesize = connection_socket.recv(1024).decode()
            # filesize = int(filesize)
            # print(filesize)

            # file = open(filename, 'wb')

            # # Get file  
            # filedata = connection_socket.recv(1024)
            # while filedata:
            #     file.write(filedata)
            #     filedata = connection_socket.recv(1024)

            # file.close()
        connection_socket.close()
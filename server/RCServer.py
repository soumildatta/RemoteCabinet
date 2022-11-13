# Author: Soumil Datta

from socket import *

if __name__ == '__main__':
    server_port = 12001
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('', server_port))
    server_socket.listen(1)

    while True:
        print('Server is ready to receive file')
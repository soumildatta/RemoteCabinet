# Author: Soumil Datta

from socket import *

if __name__ == '__main__':
    server_name = input('Input the server IP address/name: ');
    server_port = 12001

    try:
        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.connect((server_name, server_port))
        print('Successful connection to server ✅')
        
        # TODO: Save server name for later easy access
    except:
        print('Could not connect to server ❌')
        print('Make sure the server name/IP is correct, and the server is running')
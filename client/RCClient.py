# Author: Soumil Datta

from socket import *
import os
import sys

# from utilities import testPrint

server_port = 12000
packet_size = 1024

if __name__ == '__main__':
    #!!!!!! REINSTATE USER INPUT LATER --- REMOVED FOR TESTING
    # server_name = input('Input the server IP address/name: ')
    server_name = 'localhost'
    #!!!!!! FIX LINES ABOVE 
    

    # Obtain all items from folder 
    # current_dir = os.getcwd()
    current_dir = './'
    dir_list = os.listdir(current_dir)
    dir_list.remove('RCClient.py')
    print(dir_list)

    # TODO: Handle folder transfer later

    try:
        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.connect((server_name, server_port))
        print('Successful connection to server ✅')

        # TODO: Save server name for later easy access

        conn_msg = client_socket.recv(packet_size).decode()
        print(conn_msg)

        print(dir_list)

        for file in dir_list:
            #! Send filename 
            print(f'Sending file {file}')
            client_socket.send(f'FILENAME@{file}'.encode())
            print(client_socket.recv(1024).decode())

            #! Start sending file contents
            file = open(file, 'rb')
            data = file.read(1024)
            while data:
                msg = f'DATA@{data}'
                client_socket.send(msg.encode())
                print(client_socket.recv(1024).decode())
                data = file.read(1024)

            #! Send end signal
            msg = 'END@Finished sending file'
            client_socket.send(msg.encode())
            print(client_socket.recv(1024).decode())

        done_msg = f'DONE@Finished transferring'
        client_socket.send(done_msg.encode())

        print()
        print(client_socket.recv(1024).decode())

    except:
        print('Something went wrong ❌')
        print('Make sure the server name/IP is correct, and the server is running')


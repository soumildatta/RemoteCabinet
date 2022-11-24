# Author: Soumil Datta

from socket import *
import os
import sys

# from utilities import testPrint

if __name__ == '__main__':
    #!!!!!! REINSTATE USER INPUT LATER --- REMOVED FOR TESTING
    # server_name = input('Input the server IP address/name: ')
    server_name = 'localhost'
    #!!!!!! FIX LINES ABOVE 
    
    server_port = 12000

    # Obtain all items from folder 
    # current_dir = os.getcwd()
    current_dir = './'
    dir_list = os.listdir(current_dir)
    dir_list.remove('RCClient.py')
    print(dir_list)

    # TODO: Handle folder transfer later
    # for item in dir_list:
    #     if os.path.isdir(f'{current_dir}{item}'):
    #         print(f'{item} is a folder')
    #     else:
    #         print(f'{item} is a file')

    # sys.path.insert(0, '../utilities')
    # testPrint()

    try:
        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.connect((server_name, server_port))
        print('Successful connection to server ✅')
        
        # TODO: Save server name for later easy access

        #! Number of files to transfer
        length = str(len(dir_list))
        client_socket.send(length.encode())
        #* Receive response
        response = client_socket.recv(1024).decode()
        print(response)

        # Send each file over
        for filename in dir_list:
            # Send only if a filename is a file and not dir
            if os.path.isfile(f'{current_dir}{filename}'):                
                #! Send filename
                print('sending', filename)
                msg = f'FILENAME;{filename}'
                client_socket.send(msg.encode())
                #* Receive response
                resonse = client_socket.recv(1024).decode()
                print(response)

                #! Send file data
                file = open(filename, 'r')
                data = file.read()
                msg = f'CONTENTS;{data}'
                client_socket.send(msg.encode())
                #* Receive response
                response = client_socket.recv(1024).decode()
                print(response)

                #! Finish sending 
                msg = f'FINISH;1'
                client_socket.send(msg.encode())
                #* Receive response
                resonse = client_socket.recv(1024).decode()
                print(response)

                # Send size of file 
                # filesize = os.stat(filename)
                # client_socket.send(filesize.encode())

                

                # while data:
                #     client_socket.send(data)
                #     data = file.read(1024)
                # file.close()
                # client_socket.close()
    except:
        print('Could not connect to server ❌')
        print('Make sure the server name/IP is correct, and the server is running')
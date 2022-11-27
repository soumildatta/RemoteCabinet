# Author: Soumil Datta

from socket import *
import os
import sys

# from utilities import testPrint

server_port = 12000
packet_size = 1024

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

    # TODO: Handle folder transfer later

    try:
        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.connect((server_name, server_port))
        print('Successful connection to server ✅')

        # TODO: Save server name for later easy access

        conn_msg = client_socket.recv(packet_size).decode()
        print(conn_msg)

        # Send the files
        handleSendFile(dir_list, client_socket)

    except:
        print('Something went wrong ❌')
        print('Make sure the server name/IP is correct, and the server is running')


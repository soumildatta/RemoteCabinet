# Author: Soumil Datta

from socket import *
import os
import sys

# from utilities import testPrint

server_port = 12000
packet_size = 1024
current_dir = './'

syncedFiles = []

def handleSendFiles(fileList, client_socket):
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

def handleSyncSendFiles(fileList, client_socket):
    for file in fileList:
        if file not in syncedFiles:
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
    
    client_socket.send('FINISHED'.encode())

def handleReceiveFiles(conn):
    while True:
        # Receive file name size
        size = conn.recv(16).decode()

        # stop receiving if nothing is being sent anymore
        if not size or size == 'FINISHED':
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
        conn.send('RECV'.encode())
        print(f'File {filename} received successfully')

def handleSyncReceiveFiles(conn):
    current_files = os.listdir(current_dir)

    while True:
        # Receive file name size
        size = conn.recv(16).decode()

        # stop receiving if nothing is being sent anymore
        if not size or size == 'FINISHED':
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
        conn.send('RECV'.encode())

        syncedFiles.append(filename)

        if filename not in current_files:
            print(f'File {filename} received successfully')


if __name__ == '__main__':
    #!!!!!! REINSTATE USER INPUT LATER --- REMOVED FOR TESTING
    # server_name = input('Input the server IP address/name: ')
    server_name = 'localhost'
    #!!!!!! FIX LINES ABOVE 
    
    # Obtain all items from folder 
    # current_dir = os.getcwd()
    dir_list = os.listdir(current_dir)
    dir_list.remove('RCClient.py')

    # TODO: Handle folder transfer later

    # try:
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((server_name, server_port))

    # TODO: Save server name for later easy access

    conn_msg = client_socket.recv(packet_size).decode()
    
    if conn_msg.split('@')[0] == '100':
        print('Successful connection to server ✅')
    else:
        print('Something went wrong ❌')
        print('Make sure the server name/IP is correct, and the server is running')
        exit(0)


    #! At this point, the client is connected to server




    # TODO: Automatic initial synchronization at this point~
    #! IMPLEMENTATION WANTED IS NOT FULLY OPERATIONAL
    # For right now, sending command 02 makes server send all files so do that for syncing 
    client_socket.send('02'.encode())
    handleSyncReceiveFiles(client_socket)

    client_socket.send('01'.encode())
    handleSyncSendFiles(dir_list, client_socket)

    try:
        while True:
            something = 2
    except KeyboardInterrupt:
        client_socket.send('11'.encode())
        print('Disconnected from server')
        client_socket.close()

    # command = input('=> ')
    # # Commands: UPLOAD (01), GET (02)

    # # Send the files
    # if command == 'UPLOAD':
    #     client_socket.send('01'.encode())
    #     handleSendFile(dir_list, client_socket)
    # elif command == 'GET':
    #     client_socket.send('02'.encode())
    #     handleReceiveFiles(client_socket)

    # except:
    #     print('Something went wrong ❌')
    #     print('Make sure the server name/IP is correct, and the server is running')


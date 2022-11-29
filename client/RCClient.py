# Author: Soumil Datta

from socket import *
import os
import sys

# from utilities import testPrint

server_port = 12001
packet_size = 1024
current_dir = './'

syncedFiles = []

def calcNewModTimes(file_list):
    newModTimes = {}

    for filename in file_list:
        # print(filename)
        if os.path.exists(filename) and filename != 'RCClient.py':
            newModTimes[filename] = os.stat(filename).st_mtime

    return newModTimes

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

def handleFileDeletion(file, conn):
    size = len(file)
    size = bin(size)[2:].zfill(16)
    client_socket.send(size.encode())
    client_socket.send(file.encode())
    print(f'File {file} deleted from server')

def handleSendFileUpdate(file, conn):
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
    server_name = input('Input the server IP address/name: ')
    
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

    # Initial connection synchronization - 
    # First receive files from server
    # Second, send files that were not received from the server to the server
    client_socket.send('02'.encode())
    handleSyncReceiveFiles(client_socket)

    client_socket.send('01'.encode())
    handleSyncSendFiles(dir_list, client_socket)

    # Get file modified times
    modtimes = {}
    for file in dir_list:
        if file != 'RCClient.py':
            modtimes[file] = os.stat(file).st_mtime

    try:
        old = os.listdir(current_dir)
        # print(old)

        while True:
            new = os.listdir(current_dir)
            newModtimes = calcNewModTimes(new)

            if modtimes != newModtimes:
                # This is to notice update when a file is already 
                new = os.listdir(current_dir)

                dict1 = set(modtimes.items())
                dict2 = set(newModtimes.items())

                if len(new) > len(old):
                    client_socket.send('04'.encode())
                    newfile = list(set(new) - set(old))[0]
                    # print(newfile[0])
                    handleSendFileUpdate(newfile, client_socket)
                    old = new
                elif len(new) < len(old):
                    # file has been deleted
                    client_socket.send('03'.encode())
                    deleteFilename = list(set(old) - set(new))[0]
                    handleFileDeletion(deleteFilename, client_socket)
                    old = new
                else:
                    updateFile = list(dict2 - dict1)[0][0]
                    print('Modified: ', updateFile)
                    client_socket.send('04'.encode())
                    handleSendFileUpdate(updateFile, client_socket)

                modtimes = newModtimes

    except KeyboardInterrupt:
        client_socket.send('11'.encode())
        print('Disconnected from server')
        client_socket.close()
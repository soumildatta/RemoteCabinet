# Author: Soumil Datta

from socket import *
import os
from glob import glob
import time
import shutil

server_port = 12000
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
        directory = "."

        if len(file) > 1 and file[-1] not in syncedFiles:
            for i in range(0, len(file) - 1):
                # Send folder name size and name
                foldername = file[i]
                directory = os.path.join(directory, foldername)

                foldernameSize = len(foldername)
                foldernameSize = bin(foldernameSize)[2:].zfill(16)
                foldernameSize = 'FOLD@' + foldernameSize
                client_socket.send(foldernameSize.encode())
                client_socket.send(foldername.encode())
            
        if file[-1] not in syncedFiles:
        # if file not in syncedFiles:
            file = file[-1]

            print(f'Sending {file}')

            # send filename size
            size = len(file)
            # encode size as 16 bit binary
            size = bin(size)[2:].zfill(16)
            size = 'FILE@' + size
            client_socket.send(size.encode())
            client_socket.send(file.encode())

            filename = os.path.join(directory, file)
            filesize = os.path.getsize(filename)
            filesize = bin(filesize)[2:].zfill(32)
            client_socket.send(filesize.encode())

            fileOpened = open(filename, 'rb')

            data = fileOpened.read()
            client_socket.sendall(data)
            fileOpened.close()
            print(f'File {filename} sent')
    
    client_socket.send('FINISHED'.encode())


def handleSyncReceiveFiles(conn):
    current_files = listFiles2(current_dir)
    directory = "."
    
    while True:
        # Receive file name size
        size = conn.recv(21).decode()
        
        if not size or size == 'FINISHED':
            # stop receiving if nothing is being sent anymore
            break 
        
        cmd, size = size.split('@')
        size = int(size, 2)

        if cmd == 'FOLD':
            foldername = conn.recv(size).decode()
            # Skip if the folder already exists
            directory = os.path.join(directory, foldername)
            if not os.path.exists(directory):
                os.mkdir(directory)
            else:
                # directory = os.path.join(directory, foldername)
                continue

        elif cmd == 'FILE':
            filename = conn.recv(size).decode()
            filename = os.path.join(directory, filename)

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

            syncedFiles.append(filename.split('/')[-1])

            if filename[2:] not in current_files:
                print(f'File {filename} received successfully')

            # Reset directory
            directory = '.'


def handleFileDeletion(file, conn):
    for item in file:
        # check if the previous folder is deleted 
        if '/' in item:
            prevFolderItems = item.split('/')[:-1]
            previousFolder = '/'.join(prevFolderItems)
            if not os.path.exists(previousFolder):            
                size = len(previousFolder)
                size = bin(size)[2:].zfill(32)
                size = 'FDEL@' + size
                client_socket.send(size.encode())
                client_socket.send(previousFolder.encode())

                # this folder was deleted
                print(f'folder {previousFolder} deleted from server')
                break

        size = len(item)
        size = bin(size)[2:].zfill(32)
        size = 'FILE@' + size
        client_socket.send(size.encode())
        client_socket.send(item.encode())

        print(f'File {item} deleted from server')

    client_socket.send('FINISHED@0000000000000000000000000000'.encode())

def handleFileDeleteFromServer(conn):
    while True:
        size = conn.recv(37).decode()

        if not size or size == 'FINISHED@0000000000000000000000000000':
            break

        cmd, size = size.split('@')
        size = int(size, 2)

        if cmd == 'FDEL':
            foldername = conn.recv(size).decode()
            if os.path.exists(foldername):
                # os.rmdir(foldername)
                shutil.rmtree(foldername)
            else:
                print(f'Deletion not possible because {foldername} not found')

        elif cmd == 'FILE':
            filename = conn.recv(size).decode()
            if os.path.exists(filename):
                os.remove(filename)
            else:
                print(f'Deletion not possible because {filename} not found')

def handleSendFileUpdate(file, conn):
    directory = "."
    file = file.split('/')
    # print(file)

    if len(file) > 1 and file[-1] not in syncedFiles:
        for i in range(0, len(file) - 1):
            # Send folder name size and name
            foldername = file[i]
            directory = os.path.join(directory, foldername)

            foldernameSize = len(foldername)
            foldernameSize = bin(foldernameSize)[2:].zfill(16)
            foldernameSize = 'FOLD@' + foldernameSize
            client_socket.send(foldernameSize.encode())
            client_socket.send(foldername.encode())
        
    if file[-1] not in syncedFiles:
    # if file not in syncedFiles:
        file = file[-1]

        print(f'Sending {file}')

        # send filename size
        size = len(file)
        # encode size as 16 bit binary
        size = bin(size)[2:].zfill(16)
        size = 'FILE@' + size
        client_socket.send(size.encode())
        client_socket.send(file.encode())

        filename = os.path.join(directory, file)
        filesize = os.path.getsize(filename)
        filesize = bin(filesize)[2:].zfill(32)
        client_socket.send(filesize.encode())
        fileOpened = open(filename, 'rb')

        data = fileOpened.read()
        client_socket.sendall(data)
        fileOpened.close()
        print(f'File {filename} sent')
    
    client_socket.send('FINISHED'.encode())


def handleReceiveFileUpdate(conn):
    directory = "."

    while True:
        # Receive file name size
        size = conn.recv(21).decode()
        
        if not size:
            # stop receiving if nothing is being sent anymore
            break 
        
        cmd, size = size.split('@')
        size = int(size, 2)

        if cmd == 'NONE':
            break

        if cmd == 'FOLD':
            foldername = conn.recv(size).decode()
            directory = os.path.join(directory, foldername)
            if not os.path.exists(directory):
                os.mkdir(directory)
            else:
                continue

        elif cmd == 'FILE':
            filename = conn.recv(size).decode()
            filename = os.path.join(directory, filename)

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
            print(f'File {filename} received from server successfully')
                        
            break


def listFiles(directory):
    result = [y for x in os.walk(directory) for y in glob(os.path.join(x[0], '*.*'))]
    dir_list = []
    for file in result:
        hierarchy = file.split('/')
        hierarchy.remove('.')
        if hierarchy[0] != 'RCClient.py':
            if  (len(hierarchy) == 1 and '.' in hierarchy[0]):
                dir_list.append(hierarchy)
            elif len(hierarchy) > 1:
                dir_list.append(hierarchy)
    return dir_list


# This function preserves the / mand does not tokenize
def listFiles2(directory):
    result = [y for x in os.walk(directory) for y in glob(os.path.join(x[0], '*.*'))]
    dir_list = []
    for file in result:
        hierarchy = file.split('/')
        hierarchy.remove('.')
        if hierarchy[0] != 'RCClient.py':
            if  (len(hierarchy) == 1 and '.' in hierarchy[0]):
                dir_list.append('/'.join(hierarchy))
            elif len(hierarchy) > 1:
                dir_list.append('/'.join(hierarchy))
    return dir_list


if __name__ == '__main__':
    server_name = input('Input the server IP address/name: ')

    dir_list = listFiles(current_dir)

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

    dir_list = listFiles2(current_dir)

    # Get file modified times
    modtimes = {}
    for file in dir_list:
        if file != 'RCClient.py':
            modtimes[file] = os.stat(file).st_mtime

    try:
        old = listFiles2(current_dir)

        while True:
            new = listFiles2(current_dir)
            newModtimes = calcNewModTimes(new)

            if modtimes != newModtimes:
                # This is to notice update when a file is already 
                new = listFiles2(current_dir)

                dict1 = set(modtimes.items())
                dict2 = set(newModtimes.items())

                # Handle new file in directory
                if len(new) > len(old):
                    client_socket.send('04'.encode())
                    newfile = list(set(new) - set(old))[0]
                    handleSendFileUpdate(newfile, client_socket)
                    old = new
                # Handle file deleted from directory
                elif len(new) < len(old):
                    # file has been deleted
                    client_socket.send('03'.encode())
                    deleteFilename = list(set(old) - set(new))
                    handleFileDeletion(deleteFilename, client_socket)
                    old = new
                # Handle file modified in directory
                else:
                    updateFile = list(dict2 - dict1)[0][0]
                    client_socket.send('04'.encode())
                    handleSendFileUpdate(updateFile, client_socket)

                modtimes = newModtimes


            # TODO: UNDER CONSTRUCTION - it is stuck because it is inside the modtimes
            time.sleep(1)
            # Send message to server asking for update
            client_socket.send('05'.encode())
            serverResponse = client_socket.recv(6).decode()
            cmd, message = serverResponse.split('@')
            if cmd == 'RECV':
                handleReceiveFileUpdate(client_socket)
            elif cmd == 'DELE':
                handleFileDeleteFromServer(client_socket)

    except KeyboardInterrupt:
        # Send the break signal to the server to disconnect with this client
        client_socket.send('11'.encode())
        print('Disconnected from server')
        client_socket.close()
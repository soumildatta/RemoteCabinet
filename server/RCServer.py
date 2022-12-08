# Author: Soumil Datta

from socket import *
import os 
import threading
from glob import glob
import shutil

server_port = 12000
packet_size = 1024
current_dir = './'

# Utilize dictionary like a hashmap
# This dict will contain all files received from the client
# Key - filename, value - client address
receivedFiles = {}

def handleReceiveFiles(conn, addr):
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
            print(f'File {filename} received successfully')

            # Reset directory
            directory = '.'

            # Add file to the received files
            receivedFiles[filename] = addr

def handleReceiveFileUpdate(conn):
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
            directory = os.path.join(directory, foldername)
            if not os.path.exists(directory):
                os.mkdir(directory)
                # print(directory)
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
            print(f'File {filename} received successfully')
            
            # Add file to the received files
            receivedFiles[filename] = addr
            
            break

def handleSendFile(fileList, client_socket):
    for file in fileList:
        directory = "."
        file = file.split('/')

        if len(file) > 1:
            for i in range(0, len(file) - 1):
                # Send folder name size and name
                foldername = file[i]
                directory = os.path.join(directory, foldername)

                foldernameSize = len(foldername)
                foldernameSize = bin(foldernameSize)[2:].zfill(16)
                foldernameSize = 'FOLD@' + foldernameSize
                client_socket.send(foldernameSize.encode())
                client_socket.send(foldername.encode())
            
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

def handleSendFileUpdate(files, conn, addr):
    print('There was a new update from a client and it needs to now be sent to client')

    for file in files:
        file = './' + file
        if receivedFiles[file] != addr:
            print('gotta send update to', addr)

def handleFileDeletion(conn):
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

# This function preserves the / and does not tokenize
def listFiles2(directory):
    result = [y for x in os.walk(directory) for y in glob(os.path.join(x[0], '*.*'))]
    dir_list = []
    for file in result:
        hierarchy = file.split('/')
        hierarchy.remove('.')
        if hierarchy[0] != 'RCServer.py':
            if  (len(hierarchy) == 1 and '.' in hierarchy[0]):
                dir_list.append('/'.join(hierarchy))
            elif len(hierarchy) > 1:
                dir_list.append('/'.join(hierarchy))
    return dir_list

#! Main thread function
def clientHandler(conn, addr):
    print(f'Client {addr} connected')
    conn.send(f'100@Connection with server established'.encode())

    old_list = listFiles2(current_dir)

    while True:
        # Receive command for what to do
        command = conn.recv(2).decode()

        # RECEIVE FILES FROM CLIENT
        if command == '01':
            handleReceiveFiles(conn, addr)
        # SEND FILES TO CLIENT
        elif command == '02':
            dir_list = listFiles2(current_dir)
            handleSendFile(dir_list, conn)
        elif command == '03':
            handleFileDeletion(conn)
        elif command == '04':
            handleReceiveFileUpdate(conn)
        elif command == '11':
            break
        
        new_list = listFiles2(current_dir)

        # TODO: UNDER CONSTRUCTION SERVER SYNCING
        if len(new_list) > len(old_list):
            newfiles = list(set(new_list) - set(old_list))
            handleSendFileUpdate(newfiles, conn, addr)

    print(f'Client {addr} disconnected')
    conn.close()


if __name__ == '__main__':
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('', server_port))
    server_socket.listen(1)

    print('Server started ✅')

    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=clientHandler, args=(conn, addr))
            thread.start()
            #! TEMPPORARY 
            # clientHandler(conn, addr)
    except KeyboardInterrupt:
        server_socket.close()
        print('Server has been stopped')
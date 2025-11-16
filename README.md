# RemoteCabinet

RemoteCabinet is a client-server architecture based command-line application that does a lot of things that Dropbox is known for. It allows clients to store files on the server, and allows synchronization between clients. This implementation of RemoteCabinet shows that a Dropbox-like application can be deployed with a TCP/IP protocol to completely work on devices that are readily available to users safely and securely without relying on outside services. This program was made mainly because I wanted to convert an old laptop laying around into a remote file server.

## System Requirements

The requirements of RemoteCabinet are fairly simple and less demanding. The requirements are as follows:

- Both client and server scripts must be run on machines with a Unix operating system (macOS or Linux)
- Python 3.6 or higher must be installed on the machines running the scripts

## Development Environment

RemoteCabinet was predominantly developed and tested on a MacBook Pro running macOS Monterey 12.6. It was also developed and tested on a machine running Ubuntu 20.04 LTS (Focal Fossa). The scripts were executed with Python 3.9.5 and the code was written in Visual Studio Code with the Python extension.

## Running RemoteCabinet

Executing this program is fairly straightforward. Note that for this program to work, the server script must be started first on the server machine so that a client can connect to it. The directory that contains the server script will serve as the base directory for your storage system. There are 2 steps to starting the server script:

1. On the server machine, change directory to the folder containing the server script RCServer.py. Alternatively, move __RCServer.py__ to the folder you want to use as the base directory for your storage system. 
2. Start the server with: `python RCServer.py`  

The RemoteCabinet client or server scripts can be terminated through a regular command-line keyboard interrupt (CTRL + C / CMD + C). A server will only shut down once all client have disconnected to prevent potential issues, even after a keyboard interrupt is initiated in the server. 

## Contributions to the Project
Contributions to this project are very welcome. There is definitely room for improvement, and I welcome anyone to share their ideas or improve upon this project. You can create a new issue if you notice a problem or see room for improvement, or solve one of the existing issues.

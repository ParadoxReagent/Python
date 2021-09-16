#!/usr/bin/env python

# This program asks the user to enter their network in CIDR format and scans it for available hosts
# The user then chooses one of the available hosts for a port scan.
# The results are output to a text file for later review.


import datetime
import subprocess
import ipaddress
import socket
import threading
from queue import Queue

# define current time variable with datetime module
current_time = datetime.datetime.now()


######
# function: network_scan
# purpose: scans user input network in CIDR format
# inputs: user network address
# returns: available hosts on the network
######
def network_scan():
    network_address = input("Please enter a network address in CIDR format(ex.192.168.1.0/24): ")
    # defines the network using the ipaddress module
    network = ipaddress.ip_network(network_address)
    # Gets all hosts on network and formats as a list
    allHosts = list(network.hosts())

    # This block of code hides the technical details from subprocess from the output window
    info = subprocess.STARTUPINFO()
    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = subprocess.SW_HIDE

    # Ping scans all hosts in the subnet on Windows with a 50 millisecond delay for timeouts and an echo req of 1
    # stdout outputs the information to the screen in a clean, readable format while hiding technical info
    for l in range(len(allHosts)):
        results = subprocess.Popen(['ping', '-n', '1', '-w', '50', str(allHosts[l])], stdout=subprocess.PIPE, startupinfo=info).communicate()[0]
        # statement that searches each host after ping for Destination host unreachable.
        # if found it passes to the next host.
        if "Destination host unreachable" in results.decode('utf-8'):
            pass
        # statement that parses each host after ping for Request timed out.
        # if found it passes to the next host and determines the host to be up.
        elif "Request timed out" in results.decode('utf-8'):
            pass
        else:
            print(str(allHosts[l]), "is up.")


# runs network scan
network_scan()

# outputs current date and time of scan completion
print("Scan completed at ", current_time, ".")

print_Lock = threading.Lock()
target = input("Please type in your targets IP address: ")


######
# function: portscan
# purpose: scans desired IP address for open ports
# inputs: user enters target IP address
# returns: devices open ports
######
def portscan(port):
    # connection is created with socket module
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        con = s.connect((target, port))
        with print_Lock:
            # outputs open ports on specified target and appends to txt file and includes time of scan
            print("Port ", port, " is open on ", target, ".", file=open("Scan.txt", "a"))
            print("Port scan completed at ", current_time, ".", file=open("Scan.txt", "a"))
        # connection closed
        con.close()
    except:
        pass


######
# function: threader
# purpose: speeds up port scanning
# inputs: NA
# returns: NA
######
def threader():
    while True:
        job = que.get()
        portscan(job)
        que.task_done()


######
# function: scanSpeed
# purpose: uses loop of 500 threads to scan ports quickly on target
# inputs: NA
# returns: NA
######
def scanSpeed():
    for x in range(500):
        thread = threading.Thread(target=threader)
        thread.daemon = True
        thread.start()
    # scans ports 1-500
    for job in range(1, 501):
        que.put(job)


# defines que variable to be called upon by threader
que = Queue()
# starts scanSpeed def
scanSpeed()
# starts threading jobs
que.join()

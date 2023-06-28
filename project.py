import socket
import json
import socket

CONFIG_FILE = 'config.json'  
CACHE_EXPIRATION = 60 
EXTERNAL_DNS_SERVERS = ['1.1.1.1','8.8.8.8', '8.8.4.4'] 

HOST = 'localhost'
PORT = 53

with open('config.json') as f:
    config = json.load(f)

    dns_servers = config['servers-dns-external']

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.bind((HOST, PORT))
    print(f"Listening on {HOST}:{PORT}")
    sock.settimeout(10)
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            print(f"Received request from {addr[0]}:{addr[1]}")
            response = b'\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x5e\x00\x04\xac\xd9\x00\x0c'
            sock.sendto(response, addr)
        except socket.timeout:
            print("No data received within the timeout period. Stopping the program.")
            break
import socket
import json
import socket
import threading
import redis

CONFIG_FILE = 'config.json'  
CACHE_EXPIRATION = 60 
EXTERNAL_DNS_SERVERS = ['1.1.1.1','8.8.8.8', '8.8.4.4'] 

cache = redis.Redis(host='localhost', port=6379, db=0)

def check_cache(domain):
    return cache.get(domain)

def save_cache(domain, ip):
    cache.set(domain, ip, ex=CACHE_EXPIRATION)

def process_dns_request(domain, client_address):
    
    print(f"Received DNS request for domain: {domain}")

    cache_result = check_cache(domain)
    if cache_result:
        ip_address = cache_result.decode()
        print(f"Found in cache: {ip_address}")
    else:
        dns_response = send_dns_request(domain).encode()

        response_data = ip_address.encode()
        server_socket.sendto(response_data, client_address)


if __name__ == '__main__':
    with open('config.json') as f:
        config = json.load(f)

    dns_servers = config['servers-dns-external']

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', 35853))
    print("DNS Proxy Server is running.")


    received_data, addr = server_socket.recvfrom(1024)
    threading.Thread(target=process_dns_request, args=(received_data, addr)).start()  
import json
import socket
import threading
import redis
import ipaddress
import struct

CONFIG_FILE = 'config.json'  
CACHE_EXPIRATION = 60 
EXTERNAL_DNS_SERVERS = ['1.1.1.1','8.8.8.8', '8.8.4.4']  

cache = redis.Redis(host='localhost', port=6379, db=0)

def check_cache(domain):
    return cache.get(domain)

def save_cache(domain, ip):
    cache.set(domain, ip, ex=CACHE_EXPIRATION)

def send_dns_request(domain,dns_query_type):
    response = None
    for dns_server in dns_servers:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            sock.connect((dns_server, 53))
            dns_request_data = {
                "domain": domain.decode(),
                "dns_query_type": dns_query_type.decode()
                }
            json_request_data = json.dumps(dns_request_data).encode()
            dns_request_data = json.loads(json_request_data)
            fmt = "!16sH2s"
            packed_data = struct.pack(fmt, b"\x00" * 16, 1, b"\x00\x01")
            sock.sendto(packed_data, (dns_server, 53))
            print(domain)
            ip = socket.gethostbyname(domain)
            response=ip
            return response
        except socket.timeout:
            print(f"Request to {dns_server} timed out.")
        finally:
            if sock:
                sock.close()
    
#hgahjdfhgadfgafg
def process_dns_request(data, client_address):
    #domain = data.decode().strip()
    dns_query_type = data[-8:] 
    dns_query_type = dns_query_type[1:3]
    data = data[13:]
    lenght = len(data) - 13 + 1
    data2 = data[0:lenght]
    data1 = b'.' + data[-11:-8]
    domain =data2+data1
    print(f"Received DNS request for domain: {domain}")

    cache_result = check_cache(domain)
    if cache_result:
        ip_address = cache_result.decode()
        print(f"Found in cache: {ip_address}")
    else:
        dns_response = send_dns_request(domain,dns_query_type).encode()

        print("Dns response : ")
        print(dns_response)
        
        if dns_response:
            if dns_query_type == b'01':  
                ip_address = socket.gethostbyname(dns_response)
                print(f"Resolved IP address from external DNS: {ip_address}")
                save_cache(domain, ip_address) 
            elif dns_query_type == b'28':  
                ipv4_address = socket.gethostbyname(dns_response)
                ip_address = ipaddress.IPv6Address('2001::' + ipv4_address).compressed
                print(f"Resolved IPv6 address from external DNS: {ip_address}")
                save_cache(domain, ip_address)  

            else:
                ip_address = 'Unsupported Query Type'
                print("Unsupported DNS query type.")
        else:
            ip_address = 'No response from external DNS servers'
            print("No response from external DNS servers.")
        
        response_data = ip_address.encode()
        server_socket.sendto(response_data, client_address)


if __name__ == '__main__':

   with open('config.json') as f:
    config = json.load(f)

    dns_servers = config['servers-dns-external']

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', 35853))
    print("DNS Proxy Server is running.")

    server_socket.settimeout(10)

    while True:
        try:
            received_data, addr = server_socket.recvfrom(1024)
            threading.Thread(target=process_dns_request, args=(received_data, addr)).start()  
        except socket.timeout:
            print("No data received within the timeout period. Stopping the program.")
            break

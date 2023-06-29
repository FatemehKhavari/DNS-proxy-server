import json
import socket
import threading
import redis
import ipaddress

CONFIG_FILE = 'config.json'  
CACHE_EXPIRATION = 60 
EXTERNAL_DNS_SERVERS = ['1.1.1.1','8.8.8.8', '8.8.4.4']

cache = redis.Redis(host='localhost', port=6379, db=0)

def check_cache(domain):
    return cache.get(domain)

def save_cache(domain, ip):
    cache.set(domain, ip, ex=CACHE_EXPIRATION)

def send_dns_request(domain):
    response = None
    for dns_server in EXTERNAL_DNS_SERVERS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(10)
            sock.sendto(domain, (dns_server, 53))
            ip = socket.gethostbyname(domain)
            response=ip
            return response
        except socket.timeout:
            print(f"Request to {dns_server} timed out.")
        finally:
            if sock:
                sock.close()
    return response

def process_dns_request(data, client_address):
    domain = data.encode().strip()
    dns_query_type = domain[-2:]  
    domain = domain[:-3]  
    domain_name = domain.decode()
    print(f"Received DNS request for domain: {domain}")

    cache_result = check_cache(domain)
    if cache_result:
        ip_address = cache_result.decode()
        print(f"Found '{domain_name}' in cache: {ip_address}")
    else:
        dns_response = send_dns_request(domain)
        
        if dns_response:
            if dns_query_type == b'01':  
                ip_address = socket.gethostbyname(domain_name)
                print(f"Resolved IP address from external DNS '{domain_name} ': {ip_address}")
                save_cache(domain, ip_address) 
            elif dns_query_type == b'28':  
                ipv4_address = socket.gethostbyname(domain_name)
                ip_address = ipaddress.IPv6Address('2001::' + ipv4_address).compressed
                print(f"Resolved IPv6 address from external DNS '{domain_name}' : {ip_address}")
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

    with open('domains.txt', 'r') as f:
        domains = f.readlines()
    for domain in domains:
        threading.Thread(target=process_dns_request, args=(domain, ('0.0.0.0', 35853))).start() 


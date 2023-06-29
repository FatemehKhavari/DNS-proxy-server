import json
import socket
import threading
import redis
import ipaddress
import timeit
import dns.resolver
import matplotlib.pyplot as plt

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

    cache_result = check_cache(domain)
    if cache_result:
        ip_address = cache_result.decode()
    else:
        dns_response = send_dns_request(domain)
        
        if dns_response:
            if dns_query_type == b'01':  
                ip_address = socket.gethostbyname(domain_name)
                save_cache(domain, ip_address) 
            elif dns_query_type == b'28':  
                ipv4_address = socket.gethostbyname(domain_name)
                ip_address = ipaddress.IPv6Address('2001::' + ipv4_address).compressed
                save_cache(domain, ip_address)  

            else:
                ip_address = 'Unsupported Query Type'
        else:
            ip_address = 'No response from external DNS servers'
        
        response_data = ip_address.encode()
        server_socket.sendto(response_data, client_address)



def query(name: str, server: str, port: int, rdtype: str):
    resolver2 = dns.resolver.Resolver()
    resolver2.nameserver_ports = {server: port}
    dns_answer = dns.resolver.resolve(name, rdtype=rdtype)
    ips = [ip.address for ip in dns_answer]
    return ips


if __name__ == '__main__':

    with open('config.json') as f:
        config = json.load(f)
  

    dns_servers = config['servers-dns-external']

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', 35853))
    print("DNS Proxy Server is running.")

    server_socket.settimeout(10)

    with open('domains.txt', 'r') as f:
        domains1 = f.read().splitlines()

    with open('domains2.txt', 'r') as f:
        domains2 = f.read().splitlines()

    domain_times_without_proxy = 0
    domain_times_with_proxy = 0
    time_proxy_array = [] 
    time_no_proxy_array = []
    

    try:
        for i in range(100):
            received_data = domains1[i]
            start_time = timeit.default_timer()
            threading.Thread(target=process_dns_request, args=(received_data, ('0.0.0.0', 35853))).start()
            end_time = timeit.default_timer()
            domain_times_with_proxy =  domain_times_with_proxy + (end_time - start_time )  
            time_proxy_array.append(domain_times_with_proxy)   
    except socket.timeout:
        print("No data received within the timeout period. Stopping the program.")
  
    print("For 100 requests ( with proxy ) the time is : " )
    print(domain_times_with_proxy) 

    plt.plot(time_proxy_array)
    plt.xlabel('Iteration (with proxy)')
    plt.ylabel('Execution Time (s)(with proxy)')
    plt.show()
    

    for i in range(100):
        start_time_without = timeit.default_timer()
        query(domains2[i], '1.1.1.1', 53, 'A')
        end_time_without = timeit.default_timer()
        domain_times_without_proxy =  domain_times_without_proxy + (end_time_without - start_time_without)
        time_no_proxy_array.append(domain_times_without_proxy)

    print("For 100 requests ( without proxy ) the time is : " )
    print(domain_times_without_proxy) 

    plt.plot(time_no_proxy_array)
    plt.xlabel('Iteration (without proxy)')
    plt.ylabel('Execution Time (s)(without proxy)')
    plt.show()
    
       
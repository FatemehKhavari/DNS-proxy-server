import json
import socket
import threading
import redis
import ipaddress
import struct

cache = redis.Redis(host='localhost', port=6379, db=0)


#Check if the cache has the IP of the donmain
def check_cache(domain):
    return cache.get(domain)

#Save the domain and its IP to the cache
def save_cache(domain, ip):
    cache.set(domain, ip, ex=cache_expiration_time)


def send_dns_request(domain,dns_query_type):
    response = None
    for dns_server in dns_servers:
        try:
            #Create a UDP conncetion
            #Connect to servers in the config file 
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(cache_expiration_time)
            sock.connect((dns_server, 53))
            dns_request_data = {
                "domain": domain.decode(),
                "dns_query_type": dns_query_type.decode()
                }
            json_request_data = json.dumps(dns_request_data).encode()
            dns_request_data = json.loads(json_request_data)
            #Create the packet and send it (serialize)
            fmt = "!16sH2s"
            packed_data = struct.pack(fmt, b"\x00" * 16, 1, b"\x00\x01")
            sock.sendto(packed_data, (dns_server, 53))
            ip = socket.gethostbyname(domain)
            response=ip
            return response
        except socket.timeout:
            print(f"Request to {dns_server} timed out.")
        finally:
            if sock:
                sock.close()
    
def process_dns_request(data, client_address):
    #Parse the data
    #Seperate the domain  the type
    dns_query_type = data[-8:] 
    dns_query_type = dns_query_type[1:3]
    data = data[13:]
    lenght = len(data) - 13 + 1
    data2 = data[0:lenght]
    data1 = b'.' + data[-11:-8]
    domain =data2+data1

    cache_result = check_cache(domain)
    if cache_result:
        ip_address = cache_result.decode()
        print(f"Found in cache: {ip_address}")
    else:
        dns_response = send_dns_request(domain,dns_query_type).encode()
        #Find the IPV4 and IPV6 based on the type
        if dns_response:
            if dns_query_type == b'01':  #IPV4
                ip_address = socket.gethostbyname(dns_response)
                print("Name: {domain}")
                print(f"Address : {ip_address}")
                save_cache(domain, ip_address) 
            elif dns_query_type == b'28':  #IPV4 and IPV6
                ipv4_address = socket.gethostbyname(dns_response)
                ip_address = ipaddress.IPv6Address('2001::' + ipv4_address).compressed
                print("Name: {domain}")
                print(f"Address : {ipv4_address}")
                print("Name: {domain}")
                print(f"Address : {ip_address}")
                save_cache(domain, ip_address)  

            else:
                ip_address = 'Unsupported Query Type'
                print("Unsupported DNS query type.")
        else:
            ip_address = 'No response from external DNS servers'
            print("No response from external DNS servers.")
        #send the response to the client
        response_data = ip_address.encode()
        server_socket.sendto(response_data, client_address)


if __name__ == '__main__':

    #use the config.json file for settings of the server
    with open('config.json') as f:
        config = json.load(f)

    dns_servers = config['external-dns-servers']
    cache_expiration_time = config['cache-expiration-time']

    #create a UDP connection 
    #Proxy is running on port 35853
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', 35853))
    print("DNS Proxy Server is running.")

    server_socket.settimeout(10)

    #Recieve data until we reach time out
    while True:
        try:
            received_data, addr = server_socket.recvfrom(1024)
            #multithreading for handling several clients
            threading.Thread(target=process_dns_request, args=(received_data, addr)).start()  
        except socket.timeout:
            print("No data received within the timeout period. Stopping the program.")
            break

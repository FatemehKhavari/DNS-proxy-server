# DNS Proxy Server

This is a simple DNS proxy server that listens on port 35853 for incoming DNS requests. It forwards these requests to external DNS servers specified in the `config.json` file and caches the result for a configurable amount of time. If a request is made for a domain that is already cached, the server returns the IP address directly from the cache.

## Requirements

To run this project, you will need:

- Python 3.6 or later
- `redis` package installed (you can install it using `pip install redis`)

## Installation

1. Clone the repository: `git clone https://github.com/FatemehKhavari/DNS-proxy-server.git`
2. Navigate to the project directory: `cd DNS-proxy-server`
3. Install the required packages: `pip install -r requirements.txt`
4. Modify the `config.json` file to include a list of external DNS servers to use.

## Usage

To start the DNS proxy server, run the `project.py` script:

```bash
python project.py
```

By default, the server listens on port `35853`. You can test the server by configuring your DNS client to use the IP address of the machine running the server as the DNS server.

## Configuration

The `config.json` file contains configuration options for the server:

- `sexternal-dns-servers`: a list of external DNS server IP addresses to use.
- `cache-expiration-time`: the number of seconds to cache DNS responses.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more information.
# Author: Bennett Warner
# Last update: 4/16/2018

import sys
import socket
import json
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler

if sys.version_info < (3, 0):
    sys.stdout.write("Sorry, Claymore JSON-API requires Python 3.x\n")
    sys.exit(1)

remote_host, remote_port = '', ''


def banner():
    print("""
   _____ _                                             
  / ____| |                                            
 | |    | | __ _ _   _ _ __ ___   ___  _ __ ___        
 | |    | |/ _` | | | | '_ ` _ \ / _ \| '__/ _ \       
 | |____| | (_| | |_| | | | | | | (_) | | |  __/       
  \_____|_|\__,_|\__, |_| |_| |_|\___/|_|  \___|       
                  __/ |                                
       _  _____  |___/ _   _               _____ _____ 
      | |/ ____|/ __ \| \ | |        /\   |  __ \_   _|
      | | (___ | |  | |  \| |______ /  \  | |__) || |  
  _   | |\___ \| |  | | . ` |______/ /\ \ |  ___/ | |  
 | |__| |____) | |__| | |\  |     / ____ \| |    _| |_ 
  \____/|_____/ \____/|_| \_|    /_/    \_\_|   |_____|

    # https://github.com/bennettwarner/ClaymoreJSON-API
    """)


def parser_error(errmsg):
    banner()
    r = '\033[91m'  # red
    print(r + "Usage: python3 " + sys.argv[0] + " [Options] use -h for help")
    print(r + "Error: " + errmsg)
    sys.exit()


def parse_args():
    # parse the arguments
    parser = argparse.ArgumentParser(epilog='\tExample: \r\npython3 ' + sys.argv[0] + " -rhost miningrig.local -rport 3333")
    parser.error = parser_error
    parser._optionals.title = "OPTIONS"
    parser.add_argument('-lhost', '--local-host', help="The IP address / hostname that should be used to serve the JSON API. (Defaults to localhost)", default='localhost')
    parser.add_argument('-lport', '--local-port', help='The port that this server should bind to (Defaults to port 80)', default=80)
    parser.add_argument('-rhost', '--remote-host', help='The IP address / hostname of the machine running Claymore Dual Miner', required=True)
    parser.add_argument('-rport', '--remote-port', help='The port that Claymore Dual Miner is hosting the API on', required=True)
    return parser.parse_args()


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(get_response())


def get_response():
    global remote_host, remote_port

    try:
        request = poll_claymore(remote_host, remote_port)
        response = build_response(request)
        return response.encode()

    except TimeoutError:
        print('Error: API Timeout')
        return 'Error: API Timeout'.encode()


def poll_claymore(remote_host, remote_port):
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.connect((remote_host, remote_port))

    send = '{"id":0,"jsonrpc":"2.0","method":"miner_getstat1"}\n'

    connection.send(str.encode(send))
    data = connection.recv(1024)
    connection.close()

    return (json.loads(data))['result']


def build_response(request):

    return_json = dict()
    return_json['host'] = remote_host
    return_json['port'] = remote_port
    return_json['hashrate'] = str((str(request[2]).split(';'))[0])
    cards = str(request[3]).split(';')
    card_hashrate = dict()
    for i in range(0, len(cards)):
        card_hashrate.update({'card'+str(i): str(cards[i])})
    return_json.update({'card_hashrate': card_hashrate})
    return_json['uptime'] = request[1]
    return_json['mining_address'] = request[7]

    print(return_json)
    return json.dumps(return_json)


def main():
    args = parse_args()
    local_host = args.local_host
    local_port = int(args.local_port)
    global remote_host, remote_port
    remote_host = args.remote_host
    remote_port = int(args.remote_port)
    banner()
    httpd = HTTPServer((local_host, local_port), SimpleHTTPRequestHandler)
    print('Claymore JSON API running on '+local_host+':'+str(local_port))
    print()
    httpd.serve_forever()


if __name__ == '__main__':
    main()

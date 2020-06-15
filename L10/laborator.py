from urllib.parse import urlparse
from util import ensure_path
import socket
import os


class HTTPClient:
    def __init__(self, protocol):
        self.message = ""
        self.protocol = protocol

    def send_request(self, url, useragent, protocol=None):
        parsed = urlparse(url)
        scheme = parsed.scheme
        host = parsed.netloc
        resource = parsed.path or ""        # daca nu exista path, ia string gol in loc de None
        port = parsed.port
        dir_queue = resource.split('/')
        dir_queue = list(filter("".__ne__, dir_queue))  # filtreaza si returneaza orice element care nu e egal cu ""
        dir_queue = [host] + dir_queue
        # structura de directoare va fi:
        # scheme - /
        #          | - host - /
        #                     | - path1
        #                     | - path2
        #                     | - path3
        #                     | - path4 etc
        filename = dir_queue[-1]
        dir_queue.pop()
        location = ensure_path("output", scheme, dir_queue)     # creeaza structura de directoare si returneaza ultimul
        self.new_get_request(resource, protocol)
        self.add_header("Host", host)
        self.add_header("User-Agent", useragent)
        self.end_message()
        write_flag = False
        filename = location + "/" + filename + ".html"
        with open(filename, "w") as output:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, 80))
                s.send(self.message.encode())
                while True:
                    data = s.recv(1024).decode()
                    if write_flag is False:
                        try:
                            idx = data.index("<!DOCTYPE")
                            write_flag = True
                        except ValueError:
                            try:
                                idx = data.index("<!doctype")
                                write_flag = True
                            except ValueError:
                                idx = None
                        print(data[0:idx])
                        if idx is not None:
                            output.write(data[idx:])
                    else:
                        output.write(data)
                    if "</html>" in data or "</HTML>" in data:
                        break

    def end_message(self):
        self.message += "\r\n"

    def new_get_request(self, resource, protocol=None):
        if protocol is None:
            protocol = self.protocol
        self.message = "GET "+resource+" "+protocol+"\r\n"

    def add_header(self, header, value):
        self.message += header+": "+value+"\r\n"


if __name__ == "__main__":
    client = HTTPClient("HTTP/1.1")
    client.send_request("http://riweb.tibeica.com/crawl/", "CLIENTRIW")
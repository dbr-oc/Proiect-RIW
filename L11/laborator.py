from urllib.parse import urlparse
from util import ensure_path
from bs4 import BeautifulSoup
import socket
import os


class WebCrawler:
    def __init__(self, protocol, starting_url, user):
        self.message = ""
        self.protocol = protocol
        self.queue = [starting_url]
        self.user_agent = user
        self.links = {}

    def send_request(self, url, useragent, protocol=None):
        self.links[url] = True
        parsed = urlparse(url)
        scheme = parsed.scheme
        host = parsed.netloc
        resource = parsed.path or ""        # daca nu exista path, ia string gol in loc de None
        port = parsed.port
        dir_queue = resource.split('/')
        if dir_queue[-1] == "":
            filename = None
        else:
            filename = dir_queue[-1]
        dir_queue = list(filter("".__ne__, dir_queue))  # filtreaza si returneaza orice element care nu e egal cu ""
        dir_queue = [host] + dir_queue
        # structura de directoare va fi:
        # scheme - /
        #          | - host - /
        #                     | - path1
        #                     | - path2
        #                     | - path3
        #                     | - path4 etc
        if filename:
            dir_queue.pop()
        location = ensure_path("output", scheme, dir_queue)     # creeaza structura de directoare si returneaza ultimul
        if filename:
            self.new_get_request(resource, protocol)
            self.add_header("Host", host)
            self.add_header("User-Agent", useragent)
            self.end_message()
            write_flag = False
            if filename.endswith(".html"):
                filename = location + "/" + filename
            else:
                filename = location + "/" + filename + ".html"
            # with open(filename, "w") as output:
            file_data = ""
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
                                try:
                                    idx = data.index("<html")
                                except:
                                    idx = None
                        # print(data[0:idx])
                        if idx is not None:
                            file_data += data[idx:]
                    else:
                        file_data += data
                    if "</html>" in data or "</HTML>" in data:
                        break
            soup = BeautifulSoup(file_data, 'html.parser')
            metas = soup.find_all("meta")
            ok1 = True
            ok2 = True
            found = False
            for meta in metas:
                if meta["name"] == "robots":
                    found = True
                    if meta["content"] == "all" or meta["content"] == "index":
                        ok1 = True
                    if meta["content"] == "all" or meta["content"] == "follow":
                        ok2 = True
                if found:
                    ok1 = False
                    ok2 = False
            if ok1:
                with open(filename, "w") as output:
                    output.write(file_data)
            if ok2:
                links = soup.find_all("a", href=True)
                for link in links:
                    if link["href"] in self.links:
                        continue
                    if "http" in link["href"] or "https" in link["href"]:
                        self.queue.append(link["href"])
                    else:
                        if port:
                            to_add = scheme + "://" + host + ":" + str(port)
                            if link["href"].startswith('/'):
                                to_add += link["href"]
                            else:
                                to_add += "/" + link["href"]
                        else:
                            to_add = scheme + "://" + host
                            if link["href"].startswith('/'):
                                to_add += link["href"]
                            else:
                                to_add += "/" + link["href"]
                        self.queue.append(to_add)
            # todo: verifica robots.txt

    def crawl(self):
        i = 0
        while i < 100 and len(self.queue) > 0:
            self.send_request(self.queue.pop(0), self.user_agent, self.protocol)
            i += 1

    def end_message(self):
        self.message += "\r\n"

    def new_get_request(self, resource, protocol=None):
        if protocol is None:
            protocol = self.protocol
        self.message = "GET "+resource+" "+protocol+"\r\n"

    def add_header(self, header, value):
        self.message += header+": "+value+"\r\n"


if __name__ == "__main__":
    client = WebCrawler("HTTP/1.1", "http://riweb.tibeica.com/crawl", "RIWEB_CRAWLER")
    client.crawl()

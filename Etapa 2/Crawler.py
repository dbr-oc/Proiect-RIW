from urllib.parse import urlparse, urljoin
from util import ensure_path
from bs4 import BeautifulSoup
from SolverDNS import DNSCache
from robo import RoboFile
from HTTPRequestHandler import RequestCreator
import socket
import ssl
import os


class WebCrawler:
    def __init__(self, protocol, starting_url, user):
        self.protocol = protocol
        self.queue = [starting_url]
        self.user_agent = user
        self.links = {}
        self.cache = DNSCache()
        self.robots = dict()
        self.num = 0

    def send_request(self, url, useragent, protocol):
        self.num += 1
        print(self.num, url)
        self.links[url] = True
        parsed = urlparse(url)
        scheme = parsed.scheme
        if scheme == "http":
            implicit_port = 80
        elif scheme == "https":
            implicit_port = 443
        else:
            implicit_port = 80
        host = parsed.netloc
        resource = parsed.path or ""        # daca nu exista path, ia string gol in loc de None
        port = parsed.port
        dir_queue = resource.split('/')
        dir_queue = list(filter("".__ne__, dir_queue))  # filtreaza si returneaza orice element care nu e egal cu ""
        if len(dir_queue) == 0:
            filename = "index.html"
            dir_queue.append(filename)
        else:
            filename = dir_queue[-1]
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
            message = RequestCreator.new_get_request(resource, protocol)
            message = RequestCreator.add_header("Host", host, message)
            message = RequestCreator.add_header("User-Agent", useragent, message)
            message = RequestCreator.end_message(message)
            write_flag = False
            if filename.endswith(".html"):
                filename = location + "/" + filename
            else:
                filename = location + "/" + filename + ".html"
            # with open(filename, "w") as output:
            file_data = ""
            # daca hostul este cacheuit, doar ia IP, altfel se acceseaza robots.txt si se iau lucrurile permise
            if not self.cache.is_cached(host):
                # daca domeniul nu e in cache, se verifica robots.txt
                # get_ip cacheuieste domeniul
                domain_ip = self.cache.get_ip(host)
                if domain_ip is not None:
                    self.robots[host] = RoboFile(host, domain_ip)
                    self.robots[host].obtain(host, useragent, protocol, implicit_port)
                    if not self.robots[host].ok:
                        return
                    else:
                        # exclus din robots.txt
                        if self.robots[host].match_link(parsed.path):
                            return
                else:
                    return
            else:
                domain_ip = self.cache.get_ip(host)
                if domain_ip is None:
                    return
                else:
                    if not self.robots[host].ok:
                        return
                    else:
                        if self.robots[host].match_link(parsed.path):
                            return
            if domain_ip is not None:
                headers = ""
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    if implicit_port == 443:
                        context = ssl.create_default_context()
                        s = context.wrap_socket(s, server_hostname=host)
                    s.connect((domain_ip, implicit_port))
                    s.send(message.encode())
                    former_first = ""
                    data = bytes(0)
                    while True:
                        s.settimeout(1)
                        try:
                            try:
                                data += s.recv(1024)
                                data = data.decode()
                            except UnicodeDecodeError:
                                continue
                            firstline = data.splitlines()[0]
                            if firstline == former_first:
                                break
                            former_first = firstline
                        except socket.timeout:
                            break
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
                            headers += data[0:idx]
                            if idx is not None:
                                file_data += data[idx:]
                        else:
                            file_data += data
                        if "</html>" in data or "</HTML>" in data:
                            break
                        data = bytes(0)
                # VERIFICA HEADERELE
                code = RequestCreator.get_response_code(headers)
                redirected = False
                if code.startswith("3"):
                    # try redirect
                    tries = 5
                    location = RequestCreator.extract_location(headers)
                    if location is not None:
                        while not redirected and tries > 0:
                            data, rheaders = self.redirect(location, domain_ip, protocol, useragent)
                            code = RequestCreator.get_response_code(rheaders)
                            if code.startswith("2"):
                                redirected = True
                            elif code.startswith("3"):
                                location = RequestCreator.extract_location(rheaders)
                                if location is None:
                                    break
                                tries -= 1
                            else:   # eroare
                                break
                elif code.startswith("4") or code.startswith("5"):
                    # eroare
                    return
                if code.startswith("2") or redirected:
                    soup = BeautifulSoup(file_data, 'html.parser')
                    metas = soup.find_all("meta")
                    ok1 = False
                    ok2 = False
                    found = False
                    for meta in metas:
                        if "name" in meta:
                            if meta["name"].lower() == "robots":
                                found = True
                                if meta["content"].lower() == "all" or meta["content"].lower() == "index":
                                    ok1 = True
                                if meta["content"].lower() == "all" or meta["content"].lower() == "follow":
                                    ok2 = True
                    if not found:
                        ok1 = True
                        ok2 = True
                    if ok1:
                        with open(filename, "w", encoding="utf-8") as output:
                            output.write(file_data)
                    if ok2:
                        links = soup.find_all("a", href=True)
                        for link in links:
                            if link["href"] in self.links:
                                continue
                            if "http" in link["href"] or "https" in link["href"]:
                                to_add = link["href"]
                                if "#" in to_add:
                                    to_add = to_add[:to_add.rfind("#")]
                                if to_add not in self.queue:
                                    self.queue.append(to_add)
                            else:
                                to_add = urljoin(url, link["href"])
                                if "#" in to_add:
                                    to_add = to_add[:to_add.rfind("#")]
                                if to_add not in self.queue:
                                    self.queue.append(to_add)

    def crawl(self):
        i = 0
        # todo: paralelizeaza
        while i < 100 and len(self.queue) > 0:
            self.send_request(self.queue.pop(0), self.user_agent, self.protocol)
            i += 1

    def redirect(self, location, ip, protocol, useragent):
        url = urlparse(location)
        host = url.netloc
        if url.scheme.lower() == "https":
            port = 443
        else:
            port = 80
        message = RequestCreator.new_get_request("/robots.txt", protocol)
        message = RequestCreator.add_header("Host", host, message)
        message = RequestCreator.add_header("User-Agent", useragent, message)
        message = RequestCreator.end_message(message)
        response_headers = ""
        file_data = ""
        write_flag = False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if port == 443:
                context = ssl.create_default_context()
                s = context.wrap_socket(s, server_hostname=host)
            s.connect((ip, port))
            s.send(message.encode())
            former_first = ""
            data = bytes(0)
            while True:
                try:
                    try:
                        data += s.recv(1024)
                        data = data.decode()
                    except UnicodeDecodeError:
                        continue
                    try:
                        firstline = data.splitlines()[0]
                    except:
                        if data == "":
                            break
                        raise Exception
                    if firstline == former_first:
                        break
                    former_first = firstline
                except socket.timeout:
                    break
                if write_flag is False:
                    try:
                        idx = data.index("User-Agent:")
                        write_flag = True
                    except ValueError:
                        try:
                            idx = data.index("User-agent:")
                            write_flag = True
                        except ValueError:
                            idx = None
                    response_headers += data[0:idx]
                    if idx is not None:
                        file_data += data[idx:]
                else:
                    file_data += data
                data = bytes(0)
        return file_data, response_headers


if __name__ == "__main__":
    # client = WebCrawler("HTTP/1.1", "https://9gag.com/trending", "RIWEB_CRAWLER")
    client = WebCrawler("HTTP/1.1", "https://docs.python.org/2/library/re.html", "RIWEB_CRAWLER")
    client.crawl()
    # r = RoboFile("riweb.tibeica.com", "riweb.tibeica.com", 80)
    # r = RoboFile("www.youtube.com", "172.217.16.110")
    # r = RoboFile("www.python.org", "151.101.112.223", 443)
    # r.obtain("www.python.org", "RIWEB_CRAWLER", "HTTP/1.1", 443)
    # r.obtain("www.youtube.com", "RIWEB_CRAWLER", "HTTP/1.1", 443)

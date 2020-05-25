from HTTPRequestHandler import RequestCreator
from urllib.parse import urlparse
from urlmatch import urlmatch
import socket
import ssl
import re


class RoboFile(object):
    def __init__(self, domain, ip):
        self.domain = domain
        self.ip = ip
        self.ok = False
        self.__disallows = list()

    def obtain(self, host, useragent, protocol, port):
        robomessage = RequestCreator.new_get_request("/robots.txt", protocol)
        robomessage = RequestCreator.add_header("Host", host, robomessage)
        robomessage = RequestCreator.add_header("User-Agent", useragent, robomessage)
        robomessage = RequestCreator.end_message(robomessage)
        response_headers = ""
        file_data = ""
        write_flag = False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as robo:
            if port == 443:
                context = ssl.create_default_context()
                robo = context.wrap_socket(robo, server_hostname=host)
            robo.connect((self.ip, port))
            robo.send(robomessage.encode())
            former_first = "ok"
            data = bytes(0)
            while True:
                robo.settimeout(1)
                try:
                    try:
                        data += robo.recv(1024)
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
        parse_response, location = self.parse_response_headers(response_headers)
        if parse_response == 1:
            self.parse_disallows(file_data, useragent)
            self.ok = True
        elif parse_response == 2:
            if location is not None:
                self.try_redirect(location, protocol, useragent)
        # altfel nu se intampla nimic, si tratam ca pe o eroare
        else:   # parse_response 0 -> eroare client sau server
            self.ok = True

    def parse_response_headers(self, headers):
        headers = headers.splitlines()
        res_first = headers[0].split(" ")
        res_type = res_first[1]
        if res_type.startswith("3"):
            location = None
            for i in range(1, len(headers)):
                if headers[i].lower().startswith("location"):
                    location = headers[i].split(':', 1)
                    break
            return 2, location
        elif res_type == "200":
            return 1, None
        else:   # eroare server sau client, nu face nimic
            return 0, None

    def try_redirect(self, location, protocol, useragent):
        redirected = False
        num_tries = 5
        data = None
        while not redirected and num_tries > 0:
            data, headers = self.redirect(location, protocol, useragent)
            location = self.extract_location(headers)
            if location is None:
                redirected = True
            num_tries -= 1
        if redirected:
            self.parse_disallows(data, useragent)
            self.ok = True
        else:
            self.ok = False

    def redirect(self, location, protocol, useragent):
        url = urlparse(location)
        host = url.netloc
        if url.scheme.lower() == "https":
            port = 443
        else:
            port = 80
        robomessage = RequestCreator.new_get_request("/robots.txt", protocol)
        robomessage = RequestCreator.add_header("Host", host, robomessage)
        robomessage = RequestCreator.add_header("User-Agent", useragent, robomessage)
        robomessage = RequestCreator.end_message(robomessage)
        response_headers = ""
        file_data = ""
        write_flag = False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as robo:
            if port == 443:
                context = ssl.create_default_context()
                robo = context.wrap_socket(robo, server_hostname=host)
            robo.connect((self.ip, port))
            robo.send(robomessage.encode())
            former_first = ""
            data = ""
            while True:
                try:
                    try:
                        data += robo.recv(1024)
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
                data = ""
        return file_data, response_headers

    def parse_disallows(self, data, useragent):
        data = data.lower().splitlines()
        ua = False
        my_agent = False
        for line in data:
            if line.startswith("user-agent:"):
                found_ua = line.split("user-agent:")[1]
                found_ua = found_ua.replace(" ", "")
                if found_ua == "*":
                    if not my_agent:
                        ua = True
                elif found_ua == useragent:
                    ua = True
                    my_agent = True
                    self.__disallows = list()
                else:
                    ua = False
            else:
                if ua and line.startswith("disallow:"):
                    dis = line.split("disallow:")[1]
                    dis = dis.replace(" ", "")
                    if dis != "":
                        self.__disallows.append(dis)

    def extract_location(self, headers):
        headers = headers.splitlines()
        for header in headers:
            if header.lower().startswith("location:"):
                location = header.split(':', 1)[1]
                location = location.replace(" ", "")
                return location
        return None

    def match_link(self, path):
        try:
            self.__disallows.index(path)
            return True
        except ValueError:
            dummy = "http://www.dummy.me"
            for dis in self.__disallows:
                if "*" in dis:
                    if dis[0] != '/':
                        dis = "/" + dis
                    if urlmatch(dummy+dis, dummy+path):
                        return True
            return False



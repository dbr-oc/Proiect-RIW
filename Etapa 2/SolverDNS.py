from random import randrange
from datetime import datetime
import socket
import dns.resolver
import time


class DNSResolver(object):
    def __init__(self):
        pass

    def send_question(self, dname):
        data = bytearray(18+len(dname))    # 12 + len + 2 + 4(qtype qclass)
        data[1] = randrange(0, 10)
        data[5] = 1
        active_index = 12
        qname_list = dname.split('.')
        for part in qname_list:
            data[active_index] = len(part)
            active_index += 1
            for letter in part:
                a = ord(letter)
                data[active_index] = a
                active_index += 1
        data[active_index] = 0  # desi e deja 0
        active_index += 2
        data[active_index] = 1  # qtype lower byte
        active_index += 2
        data[active_index] = 1  # qclass lower byte
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(data, ('8.8.8.8', 53))
            while True:
                recv = sock.recvfrom(512)  # buffer de 512 bytes
                print(recv)
                break
        rdata = recv[0]
        if (rdata[3] & 0x0F) != 0:      # 0000 1111 lower byte
            raise Exception("Serverul DNS a raspuns cu codul de eroare:" + str(rdata[3] & 0x0F))
        else:
            answer_count = (rdata[6] << 8) | rdata[7]
            if answer_count < 1:
                raise Exception("Serverul DNS nu a trimis un raspuns (ANCount < 1)")
            authority_count = (rdata[8] << 8) | rdata[9]
            additional_count = (rdata[10] << 8) | rdata[11]
            active_index = 12  # dupa header
            # parcurg question name, pentru a putea incepe cu intrebarile
            cuvant, next_index = DNSResolver.recursive_search(rdata, active_index)
            active_index = next_index
            active_index += 4   # sar peste qtype qclass
            raspunsuri = list()
            index = 0
            for i in range(answer_count):
                raspuns, next_index = DNSResolver.recursive_search(rdata, active_index)
                active_index = next_index
                rtype = (rdata[active_index] << 8) | rdata[active_index + 1]
                active_index += 2
                rclass = (rdata[active_index] << 8) | rdata[active_index + 1]
                active_index += 2
                ttl = (rdata[active_index] << 24) | (rdata[active_index + 1] << 16) | \
                      (rdata[active_index + 2] << 8) | rdata[active_index + 3]
                active_index += 4
                rdatalength = (rdata[active_index] << 8) | rdata[active_index + 1]
                active_index += 2
                rezultat, next_index = DNSResolver.parse_data(rdata, active_index, rtype, rdatalength)
                raspunsuri.append(dict())
                raspunsuri[index]["name"] = raspuns
                raspunsuri[index]["rtype"] = rtype
                raspunsuri[index]["rclass"] = rclass
                raspunsuri[index]["ttl"] = ttl
                raspunsuri[index]["rdatalength"] = rdatalength
                raspunsuri[index]["rdata"] = rezultat
                active_index = next_index
                index += 1
        return raspunsuri

    @staticmethod
    def parse_data(message, index, type, length):
        output = ""
        nextidx = -1
        if type == 1:       # ipv4
            for i in range(length):
                output += str(int(message[index])) + "."
                index += 1
            output = output[:-1]
            nextidx = index
        elif type == 5:     # canonical name
            output, nextidx = DNSResolver.recursive_search(message, index)
        elif type == 28:    # ipv6
            for i in range(length):
                output += str(int(message[index])) + "."
                index += 1
            output = output[:-1]
        return output, nextidx

    @staticmethod
    def recursive_search(message, start_index):
        output = ""
        if int(message[start_index]) == 0:
            return output, (start_index + 1)
        if message[start_index] < 192:
            for i in range(start_index+1, start_index + int(message[start_index]) + 1):
                output += chr(message[i])
            start_index = start_index + int(message[start_index]) + 1
            plus, next_to = DNSResolver.recursive_search(message, start_index)
            if plus:
                output += "."
            output += plus
            if next_to < start_index + 1:
                next_to = start_index + 1
            return output, next_to
        else:   # >= 192
            point_to = ((message[start_index] & 0x3f) << 8) | (message[start_index + 1] & 0xff)
            plus, next_to = DNSResolver.recursive_search(message, point_to)
            output += plus
            if next_to < start_index + 2:
                next_to = start_index + 2
            return output, next_to


class DNSResponse(object):
    def __init__(self, answer_dict):
        self.name = answer_dict["name"]
        self.rtype = answer_dict["rtype"]
        self.rclass = answer_dict["rtype"]
        self.ttl = int(answer_dict["ttl"])
        self.start_time = datetime.now()
        self.data_length = answer_dict["rdatalength"]
        self.data = answer_dict["rdata"]

    def is_valid(self):
        now = datetime.now()
        passed = now - self.start_time
        if passed.total_seconds() >= self.ttl:
            return False
        return True


class DNSCache(object):
    def __init__(self):
        self.resolver = DNSResolver()
        self.__domains = dict()

    def __solve_domain(self, dname):
        tries = 0
        finalized = False
        answers = None
        while tries < 5 and finalized is False:
            # daca exista vreo exceptie generata de trimiterea intrebarii
            # se incearca retrimiterea ei de maxim 5 ori
            try:
                answers = self.resolver.send_question(dname)
                finalized = True
            except:
                tries += 1
                time.sleep(1)
        if finalized is True:
            real = None
            for d in answers:
                try:
                    if d["name"] == dname:
                        socket.inet_aton(d["rdata"])
                        # daca nu apare o exceptie, am gasit raspunsul
                        self.__domains[dname] = DNSResponse(d)
                        break
                    else:   # numele nu e acelasi ca domeniul
                        if d["name"] == real:
                            # dar daca este numele real, atunci am gasit raspunsul
                            self.__domains[dname] = DNSResponse(d)
                            break
                except:
                    if d["name"] == dname:
                        real = d["rdata"]
        else:
            self.__domains.pop(dname, None)

    # def get_ip(self, dname):
    #     if dname not in list(self.__domains.keys()):
    #         self.__solve_domain(dname)
    #     elif not self.__domains[dname].is_valid():
    #         self.__solve_domain(dname)
    #     # dupa eventualele cautari sau daca exista si este valid
    #     if dname in list(self.__domains.keys()):
    #         return self.__domains[dname].data
    #     return None

    def get_ip(self, dname):
        if dname in list(self.__domains.keys()):
            return self.__domains[dname]
        result = dns.resolver.query(dname, 'A')
        for ipval in result:
            self.__domains[dname] = ipval.to_text()
            return self.__domains[dname]
        return None

    def is_cached(self, dname):
        if dname in list(self.__domains.keys()):
            return True
        return False


if __name__ == "__main__":
    ds = DNSCache()
    ip = ds.get_ip("riweb.tibeica.com")
    # ip = ds.get_ip("www.youtube.com")
    print(ip)

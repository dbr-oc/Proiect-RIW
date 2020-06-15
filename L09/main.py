from random import randrange
import socket


class DNSResolver(object):
    def __init__(self, name):
        self.dname = name

    def send_question(self, dname):
        data = bytearray(18+len(self.dname))    # 12 + len + 2 + 4(qtype qclass)
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
            sock.sendto(data, ('81.180.223.1', 53))
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
            active_index = 12  # dupa header
            # parcurg question name, pentru a putea incepe cu intrebarile
            cuvant, next_index = DNSResolver.recursive_search(rdata, active_index)
            active_index = next_index
            active_index += 4   # sar peste qtype qclass
            raspunsuri = dict()
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
                raspunsuri[cuvant] = dict()
                raspunsuri[cuvant]["rtype"] = rtype
                raspunsuri[cuvant]["rclass"] = rclass
                raspunsuri[cuvant]["ttl"] = ttl
                raspunsuri[cuvant]["rdatalength"] = rdatalength 
                raspunsuri[cuvant]["rdata"] = rezultat
                active_index = next_index
            print(raspunsuri)

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

    # @staticmethod
    # def int_to_bytes(number):
    #     return number.to_bytes(2, byteorder='big')
    #
    # @staticmethod
    # def to_int(byte_data):
    #     return int.from_bytes(byte_data, byteorder='big', signed=False)


if __name__ == "__main__":
    ds = DNSResolver("www.tuiasi.ro")
    ds.send_question("www.tuiasi.ro")

from bs4 import BeautifulSoup
import os
import pymongo
from src.porter import PorterStemmer
from threading import Thread, Lock
import math


class Mapper(object):
    def __init__(self, directory_path):
        self.root_directory = directory_path
        self.file_names = []
        self.punctuation = {'"': True,
                            ',': True,
                            '.': True,
                            '!': True,
                            '?': True,
                            ';': True,
                            ':': True,
                            '{': True,
                            '}': True,
                            '+': True,
                            '(': True,
                            ')': True,
                            '[': True,
                            ']': True,
                            '$': True,
                            '=': True,
                            '*': True
                            }
        self.stop_words = Mapper.read_lines('..\\utilities\\stop_words.txt')
        self.exceptions = Mapper.read_lines('..\\utilities\\exceptions.txt')
        self.get_files()
        self.database_connection = pymongo.MongoClient("mongodb://localhost:27017/")
        self.stemer = PorterStemmer()
        self.db_lock = Lock()

    def get_files(self):
        for root, dirs, files in os.walk(self.root_directory, topdown=False):
            for name in files:
                self.file_names.append(os.path.join(root, name))

    def is_punctuation(self, caracter):
        try:
            retval = self.punctuation[caracter]
            return retval
        except KeyError:
            return False

    def is_exception(self, word):
        try:
            retval = self.exceptions[word]
            return retval
        except KeyError:
            return False

    def is_stop_word(self, word):
        try:
            retval = self.stop_words[word]
            return retval
        except KeyError:
            return False

    def input_query(self):
        query = input("Cautare: ")
        word = []
        word_to_lower = []
        word_queue = []
        operators_queue = []
        for letter in query:
            if Mapper.is_operation(letter):
                if len(word) == 0:
                    continue
                word = "".join(word)
                word_to_lower = "".join(word)
                if self.is_exception(word):
                    word_queue.append(word)
                    operators_queue.append(letter)
                else:
                    if not self.is_stop_word(word_to_lower):
                        word_queue.append(word_to_lower)
                        operators_queue.append(letter)
                word = []
                word_to_lower = []
            else:
                word.append(letter)
                word_to_lower.append(letter.lower())
        if len(word) != 0:
            word = "".join(word)
            word_to_lower = "".join(word)
            if self.is_exception(word):
                word_queue.append(word)
            else:
                if not self.is_stop_word(word_to_lower):
                    word_queue.append(word_to_lower)
        previous = word_queue.pop(0)
        query_count = dict()
        query_count[previous] = 1
        for word in word_queue:
            if word in list(query_count.keys()):
                query_count[word] += 1
            else:
                query_count[word] = 1
            operator = operators_queue.pop()
            previous = self.execute_operation(previous, word, operator)
        raw_search = previous
        if isinstance(raw_search, str):
            raw_search = self.execute_operation(previous, "", " ")
        cosine = dict()
        for document in list(raw_search.keys()):
            words = raw_search[document]
            c = self.calculate_cosine(document, words, query_count)
            cosine[c] = document
        print("Documente pentru <"+query+"> :")
        for key in sorted(list(cosine.keys())):
            print(cosine[key] + ": " + str(key))

    def calculate_cosine(self, document, words, query_dict):
        value = 0
        for word in list(query_dict.keys()):
            try:
                value += words[word] * query_dict[word]
            except KeyError:
                pass
        value = value/(Mapper.calculate_norm(query_dict) * Mapper.calculate_norm(self.get_words(document)))
        return value

    def get_words(self, document):
        database = self.database_connection["config"]
        try:
            self.db_lock.acquire()
            table = database["index_direct"]
            output = table.find_one({"document": document})["words"]
        finally:
            self.db_lock.release()
        return output

    def execute_operation(self, w1, w2, ope):
        output = {}
        if isinstance(w1, dict):
            o2 = self.find_documents(w2)
            if ope == " ":
                for document, count in o2:
                    if document not in list(w1.keys()):
                        w1[document] = dict()
                    w1[document][w2] = count
            elif ope == "+":
                for document, count in o2:
                    if document in list(w1.keys()):
                        w1[document][w2] = count
            output = w1
        else:
            o1 = self.find_documents(w1)
            o2 = self.find_documents(w2)
            if ope == " ":
                for document, count in o1:
                    output[document] = dict()
                    output[document][w1] = count
                for document, count in o2:
                    if document not in list(output.keys()):
                        output[document] = dict()
                    output[document][w2] = count
            elif ope == "+":
                f2 = [x[0] for x in o2]
                for document, count in o1:
                    if document in f2:
                        output[document] = dict()
                        output[document][w1] = count
                for document, count in o2:
                    if document in list(output.keys()):
                        output[document][w1] = count
        return output

    def find_documents(self, word):
        database = self.database_connection["config"]
        try:
            self.db_lock.acquire()
            table = database["index_invers"]
            output = table.find_one({"word": word})
            try:
                output = output["documents"]
            except TypeError:
                return {}
        finally:
            self.db_lock.release()
        return output

    def map_file_direct(self, filename):
        word = []
        word_to_lower = []
        soup = BeautifulSoup(open(filename, encoding="utf8"), "html.parser")
        text = soup.get_text()
        for letter in text:
            if letter.isspace() or self.is_punctuation(letter):
                word = "".join(word)
                word_to_lower = "".join(word_to_lower)
                if word == "":
                    word = []
                    word_to_lower = []
                    continue
                if self.is_exception(word):
                    self.add_word_to_database("index_direct", filename, word)
                    word = []
                    word_to_lower = []
                else:   # nu e exceptie
                    if not self.is_stop_word(word_to_lower):
                        self.add_word_to_database("index_direct", filename, self.porter(word_to_lower))
                    word = []
                    word_to_lower = []
            else:
                word.append(letter)
                word_to_lower.append(letter.lower())

    def map_file_inverse(self, filename):
        database = self.database_connection["config"]
        words = database["index_direct"].find_one({"document": filename})["words"]
        for word in words:
            count = words[word]
            self.add_word_inverse("index_invers", filename, word, count)

    def add_word_inverse(self, collection, filename, word, count):
        database = self.database_connection["config"]
        try:
            self.db_lock.acquire()
            database[collection].update_one({"word": word}, {"$push": {"documents": (filename, count)}}, upsert=True)
        finally:
            self.db_lock.release()

    def map_direct(self):
        threads = []
        for filename in self.file_names:
            thread = Thread(target=self.map_file_direct, args=(filename,))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

    def map_inverse(self):
        threads = []
        for filename in self.file_names:
            thread = Thread(target=self.map_file_inverse, args=(filename,))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

    def add_word_to_database(self, collection, document, word):     # index direct
        database = self.database_connection["config"]
        try:
            self.db_lock.acquire()
            database[collection].update_one({"document": document}, {"$inc": {"words."+word: 1}}, upsert=True)
        finally:
            self.db_lock.release()

    def porter(self, word):
        return self.stemer.stem(word, 0, len(word)-1)

    @staticmethod
    def read_lines(filename):
        output = {}
        with open(filename, 'r') as s:
            while True:
                word = s.readline()[:-1]
                if not word:
                    break
                output[word] = True
        return output

    @staticmethod
    def is_operation(caracter):
        if caracter == " " or caracter == "+":
            return True
        return False

    @staticmethod
    def calculate_norm(values):
        value = 0
        for word in values:
            count = values[word]
            value += count * count
        return math.sqrt(value)


if __name__ == "__main__":
    import time
    start_time = time.time()
    m = Mapper("..\\input")
    # m.map_direct()
    # m.map_inverse()
    m.input_query()
    print("--- %s seconds ---" % (time.time() - start_time))




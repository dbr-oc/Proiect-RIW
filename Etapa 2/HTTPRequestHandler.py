

class RequestCreator:
    @staticmethod
    def end_message( message):
        message += "\r\n"
        return message

    @staticmethod
    def new_get_request(resource, protocol):
        message = "GET " + resource + " " + protocol + "\r\n"
        return message

    @staticmethod
    def add_header(header, value, message):
        message += header + ": " + value + "\r\n"
        return message

    @staticmethod
    def get_response_code(headers):
        headers = headers.splitlines()
        try:
            code = headers[0].split(" ")[1]
        except:
            return "404"
        return code

    @staticmethod
    def extract_location(headers):
        headers = headers.splitlines()
        for header in headers:
            if header.lower().startswith("location:"):
                location = header.split(":")[1]
                location = location.replace(" ", "")
                return location
        return None

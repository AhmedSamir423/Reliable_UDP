import ReliableUDP

class HTTPServer:
    def __init__(self, host, port):
        self.udp = ReliableUDP.ReliableUDP(host, port, "", 0)

    def parse_request(self, data):
        lines = data.decode().split("\r\n")
        method, path, _ = lines[0].split(" ")
        headers = {}
        body = ""
        for line in lines[1:]:
            if ": " in line:
                key, value = line.split(": ", 1)
                headers[key] = value
            elif line == "":
                body = "\r\n".join(lines[lines.index(line) + 1:])
                break
        return method, path, headers, body

    def create_response(self, status, body):
        headers = [
            f"HTTP/1.0 {status}",
            "Content-Type: text/plain",
            f"Content-Length: {len(body)}",
            "",
            body
        ]
        return "\r\n".join(headers).encode()

    def run(self):
        self.udp.handshake_server()
        try:
            while True:
                data, flags = self.udp.receive_packet()
                if flags & self.udp.FLAG_FIN:
                    break
                method, path, headers, body = self.parse_request(data)
                if method == "GET" and path == "/":
                    response = self.create_response("200 OK", "Hello, World!")
                elif method == "POST" and path == "/":
                    response = self.create_response("200 OK", f"Received: {body}")
                else:
                    response = self.create_response("404 Not Found", "Not Found")
                self.udp.send_packet(response)
        finally:
            self.udp.close()
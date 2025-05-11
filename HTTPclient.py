import ReliableUDP
import time

class HTTPClient:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port

    def send_request(self, method, path, body=""):
        udp = ReliableUDP.ReliableUDP("localhost", 0, self.server_host, self.server_port)
        request = f"{method} {path} HTTP/1.0\r\nContent-Length: {len(body)}\r\n\r\n{body}"
        try:
            udp.handshake_client()
            udp.send_packet(request.encode())
            response, _ = udp.receive_packet()
            return response.decode()
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            time.sleep(0.2)  # Increased delay to ensure server processes
            udp.close()

    def get(self, path):
        return self.send_request("GET", path)

    def post(self, path, body):
        return self.send_request("POST", path, body)
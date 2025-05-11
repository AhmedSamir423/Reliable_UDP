import threading
import time
from HTTPserver import HTTPServer
from HTTPclient import HTTPClient

def run_server():
    server = HTTPServer("localhost", 8080)
    print("Server running...")
    server.run()

def run_client():
    time.sleep(1)  # Wait for server
    client = HTTPClient("localhost", 8080)
    print("Client GET response:", client.get("/"))
    print("Client POST response:", client.post("/", "Hello Server"))
    print("Client invalid GET response:", client.get("/invalid"))

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    run_client()
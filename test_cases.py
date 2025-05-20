import threading
import time
from HTTPclient import HTTPClient
from HTTPserver import HTTPServer

def run_server(server):
    server.run()

def test_basic_requests():
    print("Test 1: Basic GET, POST, and Invalid GET")
    server = HTTPServer('localhost', 8080)
    server_thread = threading.Thread(target=run_server, args=(server,))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)  # Wait for server to start

    client = HTTPClient('localhost', 8080)
    try:
        # Test GET /
        response = client.get('/')
        expected = "HTTP/1.0 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 13\r\n\r\nHello, World!"
        assert response.strip() == expected.strip(), f"GET / failed: got {response}, expected {expected}"
        print("GET / passed")

        # Test POST /
        response = client.post('/', 'Hello Server')
        expected = "HTTP/1.0 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 22\r\n\r\nReceived: Hello Server"
        assert response.strip() == expected.strip(), f"POST / failed: got {response}, expected {expected}"
        print("POST / passed")

        # Test Invalid GET
        response = client.get('/invalid')
        expected = "HTTP/1.0 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nNot Found"
        assert response.strip() == expected.strip(), f"Invalid GET failed: got {response}, expected {expected}"
        print("Invalid GET passed")
    finally:
        client.close()
        server.close()

def test_packet_loss():
    print("\nTest 2: Packet Loss Simulation")
    server = HTTPServer('localhost', 8080)
    server_thread = threading.Thread(target=run_server, args=(server,))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)

    client = HTTPClient('localhost', 8080)
    try:
        client.simulate_loss(0.2)  # 20% packet loss
        response = client.get('/')
        expected = "HTTP/1.0 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 13\r\n\r\nHello, World!"
        assert response.strip() == expected.strip(), f"GET / with packet loss failed: got {response}, expected {expected}"
        print("GET / with packet loss passed")
    finally:
        client.close()
        server.close()

def test_packet_corruption():
    print("\nTest 3: Packet Corruption Simulation")
    server = HTTPServer('localhost', 8080)
    server_thread = threading.Thread(target=run_server, args=(server,))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)

    client = HTTPClient('localhost', 8080)
    try:
        client.simulate_corruption(0.2)  # 20% packet corruption
        response = client.get('/')
        expected = "HTTP/1.0 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 13\r\n\r\nHello, World!"
        assert response.strip() == expected.strip(), f"GET / with packet corruption failed: got {response}, expected {expected}"
        print("GET / with packet corruption passed")
    finally:
        client.close()
        server.close()

def test_timeout():
    print("\nTest 4: Timeout with Excessive Packet Loss")
    server = HTTPServer('localhost', 8080)
    server_thread = threading.Thread(target=run_server, args=(server,))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)

    client = HTTPClient('localhost', 8080)
    try:
        client.simulate_loss(1.0)  # 100% packet loss
        response = client.get('/')
        assert False, "Should have raised TimeoutError"
    except TimeoutError:
        print("Timeout with excessive packet loss passed")
    finally:
        client.close()
        server.close()

if __name__ == "__main__":
    test_basic_requests()
    test_packet_loss()
    test_packet_corruption()
    test_timeout()
    print("\nAll tests completed!")
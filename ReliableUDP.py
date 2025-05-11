import socket
import struct
import random
import time

class ReliableUDP:
    PACKET_FORMAT = "!IIBH{}s"
    MAX_DATA_SIZE = 1000
    FLAG_SYN = 0x02
    FLAG_ACK = 0x01
    FLAG_SYNACK = 0x03
    FLAG_FIN = 0x04

    def __init__(self, local_host, local_port, remote_host="", remote_port=0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow port reuse
        self.sock.bind((local_host, local_port))
        self.remote_addr = (remote_host, remote_port) if remote_host and remote_port else None
        self.seq_num = 0
        self.ack_num = 0
        self.timeout = 1.0
        self.loss_prob = 0.0
        self.corrupt_prob = 0.0
        self.is_open = True

    def calculate_checksum(self, data):
        return sum(data) % 0xFFFF

    def create_packet(self, seq_num, ack_num, flags, data):
        if len(data) > self.MAX_DATA_SIZE:
            raise ValueError("Data size exceeds maximum limit")
        checksum = self.calculate_checksum(data)
        packet = struct.pack(self.PACKET_FORMAT.format(len(data)), seq_num, ack_num, flags, checksum, data)
        return packet

    def parse_packet(self, packet):
        try:
            header = struct.unpack("!IIBH", packet[:11])
            data = packet[11:]
            return header[0], header[1], header[2], header[3], data
        except struct.error:
            return None, None, None, None, None

    def verify_checksum(self, data, received_checksum):
        return self.calculate_checksum(data) == received_checksum

    def handshake_client(self):
        if not self.remote_addr:
            raise ValueError("Remote address not set")
        self.sock.settimeout(self.timeout)
        for attempt in range(5):  # Increase retries to handle resets
            try:
                packet = self.create_packet(self.seq_num, 0, self.FLAG_SYN, b"")
                if random.random() >= self.loss_prob:
                    self.sock.sendto(packet, self.remote_addr)
                response, addr = self.sock.recvfrom(1024)
                seq_num, ack_num, flags, checksum, data = self.parse_packet(response)
                if self.verify_checksum(data, checksum) and flags == self.FLAG_SYNACK and ack_num == self.seq_num + 1:
                    self.remote_addr = addr
                    self.ack_num = seq_num + 1
                    self.seq_num += 1
                    ack_packet = self.create_packet(self.seq_num, self.ack_num, self.FLAG_ACK, b"")
                    self.sock.sendto(ack_packet, self.remote_addr)
                    return True
            except (socket.timeout, socket.error):
                time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                continue
        raise ConnectionError("Handshake failed after multiple attempts")

    def handshake_server(self):
        self.sock.settimeout(self.timeout)
        while True:
            try:
                packet, addr = self.sock.recvfrom(1024)
                seq_num, ack_num, flags, checksum, data = self.parse_packet(packet)
                if self.verify_checksum(data, checksum) and flags == self.FLAG_SYN:
                    self.remote_addr = addr
                    self.ack_num = seq_num + 1
                    synack_packet = self.create_packet(self.seq_num, self.ack_num, self.FLAG_SYNACK, b"")
                    self.sock.sendto(synack_packet, self.remote_addr)
                    response, addr = self.sock.recvfrom(1024)
                    seq_num, ack_num, flags, checksum, data = self.parse_packet(response)
                    if self.verify_checksum(data, checksum) and flags == self.FLAG_ACK and ack_num == self.seq_num + 1:
                        self.seq_num += 1
                        return True
            except (socket.timeout, socket.error):
                continue
        raise ConnectionError("Handshake failed")

    def send_packet(self, data, flags=0):
        if not self.is_open:
            raise ValueError("Socket is closed")
        max_retries = 5
        for _ in range(max_retries):
            if random.random() < self.loss_prob:
                continue
            packet = self.create_packet(self.seq_num, self.ack_num, flags, data)
            if random.random() < self.corrupt_prob:
                packet = bytearray(packet)
                packet[-1] ^= 0xFF
                packet = bytes(packet)
            self.sock.sendto(packet, self.remote_addr)
            self.sock.settimeout(self.timeout)
            try:
                response, _ = self.sock.recvfrom(1024)
                seq_num, ack_num, flags, checksum, data = self.parse_packet(response)
                if self.verify_checksum(data, checksum) and flags == self.FLAG_ACK and ack_num == self.seq_num + 1:
                    self.seq_num += 1
                    return
            except (socket.timeout, socket.error):
                continue
        raise TimeoutError("Max retries exceeded")

    def receive_packet(self):
        while self.is_open:
            try:
                self.sock.settimeout(self.timeout)
                packet, addr = self.sock.recvfrom(1024)
                seq_num, ack_num, flags, checksum, data = self.parse_packet(packet)
                if seq_num is not None and self.verify_checksum(data, checksum):
                    if flags & self.FLAG_FIN:
                        self.is_open = False
                        ack_packet = self.create_packet(self.seq_num, self.ack_num, self.FLAG_ACK, b"")
                        self.sock.sendto(ack_packet, self.remote_addr)
                        return b"", flags
                    if seq_num == self.ack_num:
                        self.ack_num += 1
                        ack_packet = self.create_packet(self.seq_num, self.ack_num, self.FLAG_ACK, b"")
                        self.sock.sendto(ack_packet, self.remote_addr)
                        return data, flags
                    # Handle duplicates
                    ack_packet = self.create_packet(self.seq_num, self.ack_num, self.FLAG_ACK, b"")
                    self.sock.sendto(ack_packet, self.remote_addr)
            except (socket.timeout, socket.error):
                continue
        raise ConnectionError("Connection closed")

    def simulate_loss(self, probability):
        self.loss_prob = probability

    def simulate_corruption(self, probability):
        self.corrupt_prob = probability

    def close(self):
        if self.is_open and self.remote_addr:
            try:
                packet = self.create_packet(self.seq_num, self.ack_num, self.FLAG_FIN, b"")
                self.sock.sendto(packet, self.remote_addr)
                time.sleep(0.1)  # Brief delay to allow ACK
            except socket.error:
                pass  # Ignore errors on close
            finally:
                self.is_open = False
                self.sock.close()
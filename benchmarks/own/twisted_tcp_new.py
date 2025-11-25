#!/usr/bin/env python3
"""
Twisted TCP benchmark - tests TCP connection handling, data transfer, and socket operations.
Usage: python twisted_tcp.py -n <iterations> [--clients N] [--requests M]
"""

import time
import argparse
import sys
import random
import socket
import threading
import queue
from typing import List, Dict, Any, Optional, Tuple

try:
    from twisted.internet import reactor, protocol, endpoints, defer
    from twisted.internet.protocol import Protocol, Factory, ClientFactory
    from twisted.protocols.basic import LineReceiver
    from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
    TWISTED_AVAILABLE = True
except ImportError:
    print("Warning: Twisted not available. Using fallback implementation.")
    TWISTED_AVAILABLE = False

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")

class MockTCPConnection:
    """Mock TCP connection for testing without Twisted."""
    def __init__(self, conn_id: str, local_addr: tuple, remote_addr: tuple):
        self.conn_id = conn_id
        self.local_addr = local_addr
        self.remote_addr = remote_addr
        self.is_connected = False
        self.bytes_sent = 0
        self.bytes_received = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.created_time = time.time()
        self.last_activity = time.time()
        self.send_buffer = queue.Queue()
        self.receive_buffer = queue.Queue()
        self.latency = random.uniform(0.001, 0.01)  # Simulate network latency

    def connect(self) -> bool:
        """Simulate connection establishment."""
        time.sleep(self.latency)
        self.is_connected = True
        self.last_activity = time.time()
        return True

    def send_data(self, data: bytes) -> bool:
        """Send data through the connection."""
        if not self.is_connected:
            return False
        time.sleep(self.latency * 0.1)
        self.bytes_sent += len(data)
        self.messages_sent += 1
        self.last_activity = time.time()
        # Simulate processing and response
        response = self._process_data(data)
        if response:
            self.receive_buffer.put(response)
            self.bytes_received += len(response)
            self.messages_received += 1
        return True

    def _process_data(self, data: bytes) -> Optional[bytes]:
        """Process received data and generate a response."""
        try:
            message = data.decode('utf-8').strip()
            if message.startswith('ECHO'):
                return f"ECHO_REPLY: {message[5:]}\n".encode()
            elif message.startswith('PING'):
                return f"PONG: {message[5:]}\n".encode()
            elif message.startswith('GET'):
                return f"RESPONSE: {random.randint(1,1000)}\n".encode()
            elif message.startswith('DATA'):
                time.sleep(len(message) * 0.000001)
                return f"ACK: {len(message)} bytes processed\n".encode()
            else:
                return f"UNKNOWN: {message}\n".encode()
        except UnicodeDecodeError:
            return b"ERROR: Invalid UTF-8\n"

    def receive_data(self) -> Optional[bytes]:
        """Receive data from the connection."""
        try:
            return self.receive_buffer.get_nowait()
        except queue.Empty:
            return None

    def close(self):
        """Close the connection."""
        self.is_connected = False

class MockTCPServer:
    """Mock TCP server for testing without Twisted."""
    def __init__(self, port: int):
        self.port = port
        self.connections: Dict[str, MockTCPConnection] = {}
        self.is_running = False
        self.connection_counter = 0
        self._stats = {
            'total_connections': 0,
            'active_connections': 0,
            'bytes_transferred': 0,
            'messages_processed': 0
        }

    def start(self):
        """Start the server."""
        self.is_running = True
        # print(f"Mock TCP server started on port {self.port}")

    def stop(self):
        """Stop the server."""
        self.is_running = False
        for conn in list(self.connections.values()):
            conn.close()
        self.connections.clear()

    def accept_connection(self, client_addr: tuple) -> Optional[str]:
        """Accept a new client connection."""
        if not self.is_running:
            return None
        self.connection_counter += 1
        conn_id = f"server_conn_{self.connection_counter}"
        conn = MockTCPConnection(conn_id, ("127.0.0.1", self.port), client_addr)
        conn.connect()
        self.connections[conn_id] = conn
        self._stats['total_connections'] += 1
        self._stats['active_connections'] += 1
        return conn_id

    def process_client_data(self, conn_id: str, data: bytes) -> bool:
        """Process data from a client."""
        conn = self.connections.get(conn_id)
        if not conn:
            return False
        ok = conn.send_data(data)
        if ok:
            self._stats['bytes_transferred'] += len(data)
            self._stats['messages_processed'] += 1
        return ok

    def get_response(self, conn_id: str) -> Optional[bytes]:
        """Get response from server."""
        conn = self.connections.get(conn_id)
        return conn.receive_data() if conn else None

    def close_connection(self, conn_id: str):
        """Close a client connection."""
        conn = self.connections.pop(conn_id, None)
        if conn:
            conn.close()
            self._stats['active_connections'] -= 1

    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        total_bytes_sent = sum(c.bytes_sent for c in self.connections.values())
        total_bytes_recv = sum(c.bytes_received for c in self.connections.values())
        stats = self._stats.copy()
        stats.update({
            'bytes_sent': total_bytes_sent,
            'bytes_received': total_bytes_recv,
            'bytes_transferred': total_bytes_sent + total_bytes_recv,
            'current_connections': len(self.connections)
        })
        return stats

class MockTCPClient:
    """Mock TCP client for testing without Twisted."""
    def __init__(self):
        self.connections: Dict[str, MockTCPConnection] = {}
        self.connection_counter = 0

    def connect(self, host: str, port: int) -> Optional[str]:
        self.connection_counter += 1
        conn_id = f"client_conn_{self.connection_counter}"
        conn = MockTCPConnection(conn_id, ("127.0.0.1", random.randint(20000,60000)), (host, port))
        if conn.connect():
            self.connections[conn_id] = conn
            return conn_id
        return None

    def send_data(self, conn_id: str, data: bytes) -> bool:
        conn = self.connections.get(conn_id)
        return conn.send_data(data) if conn else False

    def receive_data(self, conn_id: str) -> Optional[bytes]:
        conn = self.connections.get(conn_id)
        return conn.receive_data() if conn else None

    def close_connection(self, conn_id: str):
        conn = self.connections.pop(conn_id, None)
        if conn:
            conn.close()

def perform_tcp_client_operations(client: MockTCPClient, server_port: int,
                                  num_operations: int) -> Dict[str, Any]:
    results = {
        'connections_made': 0, 'messages_sent': 0, 'messages_received': 0,
        'bytes_sent': 0, 'bytes_received': 0, 'operation_times': [], 'failures': 0
    }
    # Establish a few connections
    conns = []
    for _ in range(min(5, num_operations)):
        start = time.perf_counter()
        cid = client.connect("127.0.0.1", server_port)
        end = time.perf_counter()
        results['operation_times'].append(end-start)
        if cid:
            results['connections_made'] += 1
            conns.append(cid)
        else:
            results['failures'] += 1

    if not conns:
        return results

    msgs = ["ECHO Hello", "PING test", "GET /status", "DATA " + "x"*100]
    for i in range(num_operations):
        cid = random.choice(conns)
        msg = random.choice(msgs).encode() + b"\n"
        start = time.perf_counter()
        if client.send_data(cid, msg):
            results['messages_sent'] += 1
            results['bytes_sent'] += len(msg)
            time.sleep(0.0005)
            resp = client.receive_data(cid)
            if resp:
                results['messages_received'] += 1
                results['bytes_received'] += len(resp)
        else:
            results['failures'] += 1
        end = time.perf_counter()
        results['operation_times'].append(end-start)

    for cid in conns:
        client.close_connection(cid)
    return results

def perform_tcp_server_operations(server: MockTCPServer, num_clients: int) -> Dict[str, Any]:
    results = {
        'clients_accepted': 0, 'messages_processed': 0, 'responses_sent': 0,
        'bytes_processed': 0, 'processing_times': []
    }
    conns = []
    for _ in range(num_clients):
        start = time.perf_counter()
        cid = server.accept_connection(("192.168.1.1", random.randint(30000,40000)))
        end = time.perf_counter()
        results['processing_times'].append(end-start)
        if cid:
            results['clients_accepted'] += 1
            conns.append(cid)

    msgs = ["ECHO srv", "PING srv", "GET /info", "DATA " + "y"*50]
    for cid in conns:
        for _ in range(3):
            start = time.perf_counter()
            data = random.choice(msgs).encode() + b"\n"
            if server.process_client_data(cid, data):
                results['messages_processed'] += 1
                results['bytes_processed'] += len(data)
                resp = server.get_response(cid)
                if resp:
                    results['responses_sent'] += 1
            end = time.perf_counter()
            results['processing_times'].append(end-start)

    for cid in conns:
        server.close_connection(cid)
    return results

def simulate_tcp_load_test(server: MockTCPServer, num_clients: int) -> Dict[str, Any]:
    results = {
        'total_clients': num_clients, 'successful_connections': 0,
        'total_requests': 0, 'total_responses': 0, 'duration': 0
    }
    start = time.perf_counter()
    clients = []
    for i in range(num_clients):
        client = MockTCPClient()
        cid = client.connect("127.0.0.1", server.port)
        scid = server.accept_connection(("10.0.0.1",50000+i))
        if cid and scid:
            results['successful_connections'] += 1
            clients.append((client,cid))
    for round in range(3):
        for client,cid in clients:
            for _ in range(2):
                msg = f"LOAD{random.randint(1,100)}".encode()+b"\n"
                if client.send_data(cid,msg):
                    results['total_requests'] +=1
                    time.sleep(0.0001)
                    if client.receive_data(cid):
                        results['total_responses'] +=1
        time.sleep(0.001)
    for client,cid in clients:
        client.close_connection(cid)
    end = time.perf_counter()
    results['duration'] = end-start
    return results

def run_twisted_tcp_benchmark(iterations: int, clients: int, reqs: int) -> float:
    # print(f"Running Twisted TCP benchmark: {iterations} iterations, clients={clients}, reqs={reqs}")
    # if not TWISTED_AVAILABLE:
        # print("Using mock TCP implementation")
    server_port = 8000+random.randint(0,999)
    server = MockTCPServer(server_port)
    server.start()
    total_ops = 0
    for i in range(iterations):
        start = time.time()
        
        if HAS_HWCOUNTER:
            cycle_start = count()
        
        client = MockTCPClient()
        client_results = perform_tcp_client_operations(client, server_port, reqs)
        total_ops += len(client_results['operation_times'])
        if i%2==0:
            srv_results = perform_tcp_server_operations(server, max(1,clients//5))
            total_ops += len(srv_results['processing_times'])
        if i%3==0:
            load_results = simulate_tcp_load_test(server, clients//3 or 1)
            total_ops += load_results['total_requests']+load_results['total_responses']
        if i%2==0:
            stats = server.get_stats()
        
        if HAS_HWCOUNTER:
            cycle_end = count_end()
            cycles = cycle_end - cycle_start
        else:
            cycles = None        
        end = time.time()
        duration = end-start

        print(f"({duration}, {cycles})")
    server.stop()

    # print(f"\nCompleted in {duration:.4f}s, total ops {total_ops}, throughput {total_ops/duration:.2f} ops/s")
    return duration

def main():
    parser = argparse.ArgumentParser(description="Twisted TCP benchmark")
    parser.add_argument("-n","--iterations",type=int,default=1,help="Number of iterations")
    parser.add_argument("--clients",type=int,default=5,help="Clients per iteration")
    parser.add_argument("--requests",type=int,default=10,help="Requests per client")
    args = parser.parse_args()
    if args.iterations<=0:
        print("Error: iterations > 0")
        sys.exit(1)
    try:
        run_twisted_tcp_benchmark(args.iterations,args.clients,args.requests)
    except KeyboardInterrupt:
        print("\nBenchmark interrupted")
        sys.exit(1)

if __name__=="__main__":
    
    main()

#!/usr/bin/env python3
"""
Twisted PCB (Protocol Control Block) benchmark - tests protocol state management and connection handling.
Usage: python twisted_pcb.py -n <iterations>
"""

import time
import argparse
import sys
import random
import threading
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass, field

try:
    from twisted.internet import reactor, protocol, endpoints
    from twisted.internet.protocol import Protocol, Factory, ClientFactory
    from twisted.protocols.basic import LineReceiver
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

class ConnectionState(Enum):
    """Connection states for protocol control blocks."""
    CLOSED = "CLOSED"
    LISTEN = "LISTEN"
    SYN_SENT = "SYN_SENT"
    SYN_RECEIVED = "SYN_RECEIVED"
    ESTABLISHED = "ESTABLISHED"
    FIN_WAIT_1 = "FIN_WAIT_1"
    FIN_WAIT_2 = "FIN_WAIT_2"
    CLOSE_WAIT = "CLOSE_WAIT"
    CLOSING = "CLOSING"
    LAST_ACK = "LAST_ACK"
    TIME_WAIT = "TIME_WAIT"

@dataclass
class ProtocolControlBlock:
    """Mock Protocol Control Block for connection state management."""
    connection_id: str
    local_address: tuple = ("127.0.0.1", 0)
    remote_address: tuple = ("127.0.0.1", 0)
    state: ConnectionState = ConnectionState.CLOSED
    created_time: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    bytes_sent: int = 0
    bytes_received: int = 0
    packets_sent: int = 0
    packets_received: int = 0
    retransmissions: int = 0
    timeout_count: int = 0
    buffer_size: int = 8192
    window_size: int = 65536
    sequence_number: int = field(default_factory=lambda: random.randint(1000, 999999))
    acknowledgment_number: int = 0
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = time.time()
    
    def is_active(self, timeout_seconds: int = 300) -> bool:
        """Check if connection is still active."""
        return (time.time() - self.last_activity) < timeout_seconds
    
    def can_send_data(self) -> bool:
        """Check if connection can send data."""
        return self.state == ConnectionState.ESTABLISHED
    
    def transition_state(self, new_state: ConnectionState) -> bool:
        """Transition to new state if valid."""
        valid_transitions = {
            ConnectionState.CLOSED: [ConnectionState.LISTEN, ConnectionState.SYN_SENT],
            ConnectionState.LISTEN: [ConnectionState.SYN_RECEIVED, ConnectionState.CLOSED],
            ConnectionState.SYN_SENT: [ConnectionState.SYN_RECEIVED, ConnectionState.ESTABLISHED, ConnectionState.CLOSED],
            ConnectionState.SYN_RECEIVED: [ConnectionState.ESTABLISHED, ConnectionState.FIN_WAIT_1, ConnectionState.CLOSED],
            ConnectionState.ESTABLISHED: [ConnectionState.FIN_WAIT_1, ConnectionState.CLOSE_WAIT],
            ConnectionState.FIN_WAIT_1: [ConnectionState.FIN_WAIT_2, ConnectionState.CLOSING, ConnectionState.TIME_WAIT],
            ConnectionState.FIN_WAIT_2: [ConnectionState.TIME_WAIT],
            ConnectionState.CLOSE_WAIT: [ConnectionState.LAST_ACK],
            ConnectionState.CLOSING: [ConnectionState.TIME_WAIT],
            ConnectionState.LAST_ACK: [ConnectionState.CLOSED],
            ConnectionState.TIME_WAIT: [ConnectionState.CLOSED]
        }
        
        if new_state in valid_transitions.get(self.state, []):
            self.state = new_state
            self.update_activity()
            return True
        return False

class MockProtocol:
    """Mock protocol implementation for testing."""
    def __init__(self, pcb: ProtocolControlBlock):
        self.pcb = pcb
        self.data_buffer = b""
        self.message_queue = []
        self.is_connected = False
    
    def connection_made(self):
        """Called when connection is established."""
        self.pcb.transition_state(ConnectionState.ESTABLISHED)
        self.is_connected = True
        self.pcb.update_activity()
    
    def data_received(self, data: bytes):
        """Process received data."""
        if not self.is_connected:
            return
        
        self.pcb.bytes_received += len(data)
        self.pcb.packets_received += 1
        self.pcb.update_activity()
        
        # Simulate protocol processing
        self.data_buffer += data
        
        # Process complete messages (assuming line-based protocol)
        while b'\n' in self.data_buffer:
            line, self.data_buffer = self.data_buffer.split(b'\n', 1)
            self.message_received(line.decode('utf-8', errors='ignore'))
    
    def message_received(self, message: str):
        """Process received message."""
        self.message_queue.append({
            'message': message,
            'timestamp': time.time(),
            'size': len(message)
        })
        
        # Simulate message processing
        if message.startswith('PING'):
            response = f"PONG {message[5:]}\n"
            self.send_data(response.encode())
        elif message.startswith('ECHO'):
            response = f"ECHO_REPLY {message[5:]}\n"
            self.send_data(response.encode())
        elif message.startswith('DATA'):
            # Simulate data processing
            data_size = len(message)
            response = f"ACK {data_size}\n"
            self.send_data(response.encode())
    
    def send_data(self, data: bytes):
        """Send data through the connection."""
        if not self.is_connected or not self.pcb.can_send_data():
            return False
        
        self.pcb.bytes_sent += len(data)
        self.pcb.packets_sent += 1
        self.pcb.sequence_number += len(data)
        self.pcb.update_activity()
        
        # Simulate network delay
        time.sleep(random.uniform(0.0001, 0.001))
        
        return True
    
    def connection_lost(self, reason=None):
        """Called when connection is lost."""
        self.pcb.transition_state(ConnectionState.CLOSED)
        self.is_connected = False

class ProtocolControlBlockManager:
    """Manages multiple protocol control blocks."""
    def __init__(self):
        self.pcbs: Dict[str, ProtocolControlBlock] = {}
        self.protocols: Dict[str, MockProtocol] = {}
        self._connection_counter = 0
        self._stats = {
            'total_connections': 0,
            'active_connections': 0,
            'closed_connections': 0,
            'timed_out_connections': 0,
            'bytes_transferred': 0,
            'packets_transferred': 0,
            'state_transitions': 0
        }
    
    def create_connection(self, local_addr: tuple, remote_addr: tuple) -> str:
        """Create a new connection."""
        self._connection_counter += 1
        conn_id = f"conn_{self._connection_counter}_{random.randint(1000, 9999)}"
        
        pcb = ProtocolControlBlock(
            connection_id=conn_id,
            local_address=local_addr,
            remote_address=remote_addr
        )
        
        protocol = MockProtocol(pcb)
        
        self.pcbs[conn_id] = pcb
        self.protocols[conn_id] = protocol
        self._stats['total_connections'] += 1
        
        return conn_id
    
    def establish_connection(self, conn_id: str) -> bool:
        """Establish a connection."""
        if conn_id not in self.pcbs:
            return False
        
        pcb = self.pcbs[conn_id]
        protocol = self.protocols[conn_id]
        
        # Simulate connection handshake
        if pcb.transition_state(ConnectionState.SYN_SENT):
            time.sleep(random.uniform(0.001, 0.01))  # Simulate network delay
            if pcb.transition_state(ConnectionState.SYN_RECEIVED):
                if pcb.transition_state(ConnectionState.ESTABLISHED):
                    protocol.connection_made()
                    self._stats['active_connections'] += 1
                    self._stats['state_transitions'] += 3
                    return True
        
        return False
    
    def send_message(self, conn_id: str, message: str) -> bool:
        """Send message through connection."""
        if conn_id not in self.protocols:
            return False
        
        protocol = self.protocols[conn_id]
        data = f"{message}\n".encode()
        return protocol.send_data(data)
    
    def simulate_received_message(self, conn_id: str, message: str):
        """Simulate receiving a message."""
        if conn_id not in self.protocols:
            return
        
        protocol = self.protocols[conn_id]
        data = f"{message}\n".encode()
        protocol.data_received(data)
    
    def close_connection(self, conn_id: str) -> bool:
        """Close a connection."""
        if conn_id not in self.pcbs:
            return False
        
        pcb = self.pcbs[conn_id]
        protocol = self.protocols[conn_id]
        
        # Simulate connection teardown
        if pcb.state == ConnectionState.ESTABLISHED:
            if pcb.transition_state(ConnectionState.FIN_WAIT_1):
                time.sleep(random.uniform(0.001, 0.005))
                if pcb.transition_state(ConnectionState.FIN_WAIT_2):
                    if pcb.transition_state(ConnectionState.TIME_WAIT):
                        if pcb.transition_state(ConnectionState.CLOSED):
                            protocol.connection_lost()
                            self._stats['active_connections'] -= 1
                            self._stats['closed_connections'] += 1
                            self._stats['state_transitions'] += 4
                            return True
        
        return False
    
    def cleanup_inactive_connections(self, timeout_seconds: int = 300):
        """Clean up inactive connections."""
        inactive_connections = []
        
        for conn_id, pcb in self.pcbs.items():
            if not pcb.is_active(timeout_seconds):
                inactive_connections.append(conn_id)
        
        for conn_id in inactive_connections:
            pcb = self.pcbs[conn_id]
            if pcb.state != ConnectionState.CLOSED:
                pcb.transition_state(ConnectionState.CLOSED)
                self.protocols[conn_id].connection_lost("timeout")
                self._stats['timed_out_connections'] += 1
                if pcb.state == ConnectionState.ESTABLISHED:
                    self._stats['active_connections'] -= 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get connection statistics."""
        stats = self._stats.copy()
        
        # Calculate totals from PCBs
        total_bytes_sent = sum(pcb.bytes_sent for pcb in self.pcbs.values())
        total_bytes_received = sum(pcb.bytes_received for pcb in self.pcbs.values())
        total_packets_sent = sum(pcb.packets_sent for pcb in self.pcbs.values())
        total_packets_received = sum(pcb.packets_received for pcb in self.pcbs.values())
        
        stats.update({
            'bytes_transferred': total_bytes_sent + total_bytes_received,
            'packets_transferred': total_packets_sent + total_packets_received,
            'bytes_sent': total_bytes_sent,
            'bytes_received': total_bytes_received,
            'packets_sent': total_packets_sent,
            'packets_received': total_packets_received,
            'current_connections': len(self.pcbs),
            'state_distribution': self._get_state_distribution()
        })
        
        return stats
    
    def _get_state_distribution(self) -> Dict[str, int]:
        """Get distribution of connection states."""
        distribution = {}
        for pcb in self.pcbs.values():
            state_name = pcb.state.value
            distribution[state_name] = distribution.get(state_name, 0) + 1
        return distribution

def simulate_protocol_operations(manager: ProtocolControlBlockManager, num_connections: int) -> Dict[str, Any]:
    """Simulate various protocol operations."""
    results = {
        'connections_created': 0,
        'connections_established': 0,
        'messages_sent': 0,
        'messages_received': 0,
        'connections_closed': 0,
        'operation_times': []
    }
    
    connection_ids = []
    
    # Create connections
    for i in range(num_connections):
        start_time = time.perf_counter()
        
        local_addr = ("127.0.0.1", 8000 + i)
        remote_addr = ("192.168.1.1", 80)
        
        conn_id = manager.create_connection(local_addr, remote_addr)
        connection_ids.append(conn_id)
        results['connections_created'] += 1
        
        end_time = time.perf_counter()
        results['operation_times'].append(end_time - start_time)
    
    # Establish connections
    for conn_id in connection_ids:
        start_time = time.perf_counter()
        
        if manager.establish_connection(conn_id):
            results['connections_established'] += 1
        
        end_time = time.perf_counter()
        results['operation_times'].append(end_time - start_time)
    
    # Send messages
    message_types = ['PING hello', 'ECHO test message', 'DATA sample_data_payload']
    
    for _ in range(num_connections * 3):
        conn_id = random.choice(connection_ids)
        message = random.choice(message_types)
        
        start_time = time.perf_counter()
        
        if manager.send_message(conn_id, message):
            results['messages_sent'] += 1
            
            # Simulate response
            if message.startswith('PING'):
                manager.simulate_received_message(conn_id, f"PONG {message[5:]}")
                results['messages_received'] += 1
            elif message.startswith('ECHO'):
                manager.simulate_received_message(conn_id, f"ECHO_REPLY {message[5:]}")
                results['messages_received'] += 1
        
        end_time = time.perf_counter()
        results['operation_times'].append(end_time - start_time)
    
    # Close some connections
    connections_to_close = random.sample(connection_ids, num_connections // 2)
    for conn_id in connections_to_close:
        start_time = time.perf_counter()
        
        if manager.close_connection(conn_id):
            results['connections_closed'] += 1
        
        end_time = time.perf_counter()
        results['operation_times'].append(end_time - start_time)
    
    return results

def run_twisted_pcb_benchmark(iterations: int) -> float:
    """Run the twisted PCB benchmark."""
    # print(f"Running Twisted PCB benchmark for {iterations} iterations...")
    
    if not TWISTED_AVAILABLE:
        print("Using mock protocol implementation (Twisted not installed)")
    
    
    manager = ProtocolControlBlockManager()
    total_operations = 0
    total_connections = 0
    total_messages = 0
    
    for i in range(iterations):
        start_time = time.time()
        if HAS_HWCOUNTER:
            cycle_start = count()
            
        # Number of connections for this iteration
        num_connections = random.randint(10, 50)
        
        # Simulate protocol operations
        operation_results = simulate_protocol_operations(manager, num_connections)
        
        total_operations += len(operation_results['operation_times'])
        total_connections += operation_results['connections_created']
        total_messages += operation_results['messages_sent'] + operation_results['messages_received']
        
        # Periodic cleanup
        if i % 5 == 0:
            manager.cleanup_inactive_connections(timeout_seconds=60)
        
        # Additional stress testing
        if i % 3 == 0:
            # Simulate burst of activity
            active_connections = [conn_id for conn_id, pcb in manager.pcbs.items() 
                                if pcb.state == ConnectionState.ESTABLISHED]
            
            if active_connections:
                for _ in range(20):
                    conn_id = random.choice(active_connections)
                    manager.send_message(conn_id, f"BURST_DATA_{random.randint(1, 1000)}")
                    total_messages += 1
        
        if HAS_HWCOUNTER:
            cycle_end = count_end()
            cycles = cycle_end - cycle_start
        else:
            cycles = None
            
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"({execution_time},{cycles})")
    
    # Final statistics
    # final_stats = manager.get_statistics()
    
    # print(f"\nCompleted {iterations} iterations in {execution_time:.4f} seconds")
    # print(f"Total connections created: {total_connections}")
    # print(f"Total messages processed: {total_messages}")
    # print(f"Total operations: {total_operations}")
    # print(f"Active connections: {final_stats['active_connections']}")
    # print(f"Closed connections: {final_stats['closed_connections']}")
    # print(f"Bytes transferred: {final_stats['bytes_transferred']}")
    # print(f"State transitions: {final_stats['state_transitions']}")
    # print(f"Operations per second: {total_operations/execution_time:.2f}")
    
    return execution_time

def main():
    parser = argparse.ArgumentParser(description="Twisted PCB benchmark")
    parser.add_argument("-n", "--iterations", type=int, default=15,
                       help="Number of iterations to run (default: 15)")
    
    args = parser.parse_args()
    
    if args.iterations <= 0:
        print("Error: iterations must be positive")
        sys.exit(1)
    
    try:
        execution_time = run_twisted_pcb_benchmark(args.iterations)
        # print(f"Benchmark completed successfully in {execution_time:.4f} seconds")
        
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running benchmark: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
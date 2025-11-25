#!/usr/bin/env python3
"""
UDP echo benchmark – tests raw UDP send/receive.
Usage: python bm_udp_echo.py -n <iterations>
"""
import socket
import time
import argparse

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")

def udp_echo_server(port, stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', port))
    sock.settimeout(0.1)
    while not stop_event():
        try:
            data, addr = sock.recvfrom(2048)
            sock.sendto(data, addr)
        except socket.timeout:
            continue
    sock.close()

def main(iterations):
    port = 9999
    stop = False
    server_thread = threading.Thread(target=udp_echo_server, args=(port, lambda: stop))
    server_thread.start()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)
    for i in range(iterations):
        start = time.time()
        
        if HAS_HWCOUNTER:
            cycle_start = count()
            
        msg = f'PING{i}'.encode()
        sock.sendto(msg, ('localhost', port))
        try:
            resp, _ = sock.recvfrom(2048)
        except socket.timeout:
            pass

        if HAS_HWCOUNTER:
            cycle_end = count_end()
            cycles = cycle_end - cycle_start
        else:
            cycles = None
            
        elapsed = time.time() - start
        print(f'({elapsed}, {cycles})')
    
    stop = True
    server_thread.join()
    sock.close()
    # print(f'\nCompleted {iterations} iterations in {elapsed:.4f}s, avg {elapsed/iterations:.6f}s')

if __name__=='__main__':
    import threading, util, optparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-n','--iterations',type=int,default=5000)
    args = parser.parse_args()
    main(args.iterations)

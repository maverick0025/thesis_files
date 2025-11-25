#!/usr/bin/env python
# -*- coding: utf-8 -*-
import util
import optparse
import time
import sys
import codecs
if sys.version_info[0] > 2:
    xrange = range

import pyaes

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")

cleartext = b"This is a test. What could possibly go wrong? " * 2000 # 92000 bytes

def benchmark():
    # 128-bit key
    key = codecs.decode(b'a1f6258c877d5fcd8964484538bfc92c', 'hex')
    iv  = codecs.decode(b'ed62e16363638360fdd6ad62112794f0', 'hex')

    aes = pyaes.new(key, pyaes.MODE_CBC, iv)
    ciphertext = aes.encrypt(cleartext)

    # need to reset IV for decryption
    aes = pyaes.new(key, pyaes.MODE_CBC, iv)
    plaintext = aes.decrypt(ciphertext)

    assert plaintext == cleartext

def main(arg):
    # XXX warmup

    times = []
    for i in xrange(arg):
        t0 = time.time()
        if HAS_HWCOUNTER:
            cycle_start = count()
            
        o = benchmark()
        
        if HAS_HWCOUNTER:
            cycle_end = count_end()
            cycles = cycle_end - cycle_start
        else:
            cycles = None
            
        tk = time.time()
        
        times.append((tk - t0, cycles))
    return times

if __name__ == "__main__":
    parser = optparse.OptionParser(
        usage="%prog [options]",
        description="Test the performance of the SlowAES cipher benchmark")
    util.add_standard_options_to(parser)
    options, args = parser.parse_args()

    util.run_benchmark(options, options.num_runs, main)

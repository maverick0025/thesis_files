# -*- coding: utf-8 -*-
# The Computer Language Benchmarks Game
# http://shootout.alioth.debian.org/
#
# contributed by Sokolov Yura
# modified by Tupteq

import optparse
import time
import util

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")


def fannkuch(n):
    count = list(range(1, n+1))
    max_flips = 0
    m = n-1
    r = n
    check = 0
    perm1 = list(range(n))
    perm = list(range(n))
    perm1_ins = perm1.insert
    perm1_pop = perm1.pop

    while 1:
        if check < 30:
            #print "".join(str(i+1) for i in perm1)
            check += 1

        while r != 1:
            count[r-1] = r
            r -= 1

        if perm1[0] != 0 and perm1[m] != m:
            perm = perm1[:]
            flips_count = 0
            k = perm[0]
            while k:
                perm[:k+1] = perm[k::-1]
                flips_count += 1
                k = perm[0]

            if flips_count > max_flips:
                max_flips = flips_count

        while r != n:
            perm1_ins(r, perm1_pop(0))
            count[r] -= 1
            if count[r] > 0:
                break
            r += 1
        else:
            return max_flips

DEFAULT_ARG = 9

def main(n):
    times = []
    for i in range(n):
        t0 = time.time()
        if HAS_HWCOUNTER:
            cycle_start = count()
        
        fannkuch(DEFAULT_ARG)
        
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
        description="Test the performance of the Float benchmark")
    util.add_standard_options_to(parser)
    options, args = parser.parse_args()

    util.run_benchmark(options, options.num_runs, main)

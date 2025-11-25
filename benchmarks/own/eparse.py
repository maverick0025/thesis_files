import time
import os

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../lib/monte")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../lib/monte/ometa")))

sys.path.append("/home/s265d007/Documents/projs/th/benchmarks-branch-default/lib/monte")
sys.path.append("/home/s265d007/Documents/projs/th/benchmarks-branch-default/lib/monte/ometa")

import ometa
ometa.FAST = True
from monte.eparser import EParser

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")


def main(n):
    l = []
    paaaa = "/home/s265d007/Documents/projs/th/benchmarks-branch-default/own/test.e"
    
    # data = open(os.path.join(os.path.dirname(__file__), 'test.e')).read()
    data = open(paaaa).read()
    for _ in range(n):
        t0 = time.time()
        # Start CPU cycle counting
        if HAS_HWCOUNTER:
            cycle_start = count()
            
        p = EParser(data)
        v, e = p.apply('start')
        # End CPU cycle counting
        if HAS_HWCOUNTER:
            cycle_end = count_end()
            cycles = cycle_end - cycle_start
        else:
            cycles = None
        t1= time.time()
        
        l.append((t1-t0, cycles))
    
    return l

if __name__ == '__main__':
    import util, optparse
    parser = optparse.OptionParser(
        usage="%prog [options]",
        description="Test the performance of the eparse benchmark")
    util.add_standard_options_to(parser)
    options, args = parser.parse_args()

    util.run_benchmark(options, options.num_runs, main)

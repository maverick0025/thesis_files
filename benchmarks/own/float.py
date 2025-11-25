#!/usr/bin/env python
# -*- coding: utf-8 -*-
from math import sin, cos, sqrt
import util
import optparse
import time
import sys
if sys.version_info[0] > 2:
    xrange = range

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")

class Point(object):

    def __init__(self, i):
        self.x = x = sin(i)
        self.y = cos(i) * 3
        self.z = (x * x) / 2

    def __repr__(self):
        return "<Point: x=%s, y=%s, z=%s>" % (self.x, self.y, self.z)

    def normalize(self):
        x = self.x
        y = self.y
        z = self.z
        norm = sqrt(x * x + y * y + z * z)
        self.x /= norm
        self.y /= norm
        self.z /= norm

    def maximize(self, other):
        self.x = self.x if self.x > other.x else other.x
        self.y = self.y if self.y > other.y else other.y
        self.z = self.z if self.z > other.z else other.z
        return self


def maximize(points):
    next = points[0]
    for p in points[1:]:
        next = next.maximize(p)
    return next

def benchmark(n):
    points = [None] * n
    for i in xrange(n):
        points[i] = Point(i)
    for p in points:
        p.normalize()
    return maximize(points)

POINTS = 100000

def main(arg):
    
    times = []
    for i in xrange(arg):
        t0 = time.time()
        if HAS_HWCOUNTER:
            cycle_start = count()
            
        o = benchmark(POINTS)
        
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

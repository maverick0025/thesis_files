
import sys, time

def fib(n):
    if n == 0 or n == 1:
        return 1
    return fib(n - 1) + fib(n - 2)

def f(n):
    times = []
    for k in range(n):
        t0 = time.time()
        for i in range(2000):
            fib(20)
        times.append(time.time() - t0)
    return times

def entry_point(argv):
    import optparse
    import util

    parser = optparse.OptionParser(
        usage="%prog [options]",
        description="Test the performance of the fibonacci benchmark")
    util.add_standard_options_to(parser)
    options, args = parser.parse_args(argv)
    util.run_benchmark(options, options.num_runs, f)

if __name__ == '__main__':
    entry_point(sys.argv[1:])


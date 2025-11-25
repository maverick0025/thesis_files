
import optparse
import util, os, sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../lib/dulwich-0.19.13")))
sys.path.append("/home/s265d007/Documents/projs/th/benchmarks-branch-default/lib/dulwich-0.19.13")


import dulwich.repo

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")


def test_dulwich(n):
    l = []
    # r = dulwich.repo.Repo(os.path.join(os.path.dirname(__file__), 'git-demo'))
    temp = "/home/s265d007/Documents/projs/th/benchmarks-branch-default/own/git-demo"
    r = dulwich.repo.Repo(temp)
    # r=dulwich.repo.Repo(r)

    for i in range(n):
        t0 = time.time()
        
        # Start CPU cycle counting
        if HAS_HWCOUNTER:
            cycle_start = count()
                
        [e.commit for e in r.get_walker(r.head())]
        
        # End CPU cycle counting
        if HAS_HWCOUNTER:
            cycle_end = count_end()
            cycles = cycle_end - cycle_start
        else:
            cycles = None
        
        t1=time.time()
        l.append((t1 - t0, cycles))
    return l

if __name__ == "__main__":
    parser = optparse.OptionParser(
        usage="%prog [options]",
        description=("Test the performance of Dulwich (git replacement)."))
    util.add_standard_options_to(parser)
    (options, args) = parser.parse_args()

    util.run_benchmark(options, options.num_runs, test_dulwich)

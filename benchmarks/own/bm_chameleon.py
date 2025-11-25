
# from lib.chameleon.src import PageTemplate
# from ../lib/chameleon/src/chameleon import PageTemplate
import sys
import os

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../lib/chameleon/src")))
sys.path.append("/home/s265d007/Documents/projs/th/benchmarks-branch-default/lib/chameleon/src")
from chameleon import PageTemplate

import sys
if sys.version_info[0] < 3:
    strstr = 'unicode'
else:
    strstr = 'str'

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")


BIGTABLE_ZPT = """\
<table xmlns="http://www.w3.org/1999/xhtml"
xmlns:tal="http://xml.zope.org/namespaces/tal">
<tr tal:repeat="row python: options['table']">
<td tal:repeat="c python: row.values()">
<span tal:define="d python: c + 1"
tal:attributes="class python: 'column-' + %s(d)"
tal:content="python: d" />
</td>
</tr>
</table>""" % strstr

def main(n):
    tmpl = PageTemplate(BIGTABLE_ZPT)
    options = {'table': [dict(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8, i=9, j=10)
                         for x in range(1000)]}
    import time
    l = []
    for k in range(n):
        t0 = time.time()
        
        if HAS_HWCOUNTER:
            cycle_start = count()
            
        tmpl(options=options)
        
        if HAS_HWCOUNTER:
            cycle_end = count_end()
            cycles = cycle_end - cycle_start
        else:
            cycles = None
            
        t1= time.time()
        
        l.append((t1 - t0, cycles))
    return l

if __name__ == '__main__':
    import util, optparse
    parser = optparse.OptionParser(
        usage="%prog [options]",
        description="Test the performance of the Go benchmark")
    util.add_standard_options_to(parser)
    options, args = parser.parse_args()

    util.run_benchmark(options, options.num_runs, main)



#!/usr/bin/env python3
"""
Dynamic Python features benchmark - tests eval, exec, and dynamic attribute access.
Usage: python bm_dynamic.py -n <iterations>
"""

import time
import argparse
import sys
import random

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")

code_snippets = [
    'x = 10\nfor i in range(100): x += i',
    'data = {str(i): i for i in range(100)}\nresult = data.get("50", 0)',
    'def func(a, b):\n    return a * b\nx = func(5, 10)',
    'class A:\n    pass\na = A()\nsetattr(a, "attr_"+str(random.randint(1,10)), random.random())',
    'eval("[i*2 for i in range(50)]")',
    'exec("total=0\\nfor i in range(50): total+=i\\n")'
]

def run_benchmark(iterations: int) -> float:
    for i in range(iterations):
        start = time.time()
        
        if HAS_HWCOUNTER:
            cycle_start = count()
            
        snippet = random.choice(code_snippets)
        if snippet.startswith('eval('):
            eval(snippet)
        else:
            # Provide random in globals so exec can use it
            globals_dict = {'random': random}
            local = {}
            exec(snippet, globals_dict, local)
            # Access dynamic attribute if exists
            for v in local.values():
                try:
                    getattr(v, 'attr_' + str(random.randint(1, 10)), None)
                except:
                    pass

        if HAS_HWCOUNTER:
            cycle_end = count_end()
            cycles = cycle_end - cycle_start
        else:
            cycles = None
                
        end = time.time()
        total = end - start
        print(f"({total}, {cycles})")
        
    return total

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('-n','--iterations',type=int,default=5000)
    args=parser.parse_args()
    run_benchmark(args.iterations)

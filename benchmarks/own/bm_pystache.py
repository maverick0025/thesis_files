#!/usr/bin/env python3
"""
Pystache (Mustache) template rendering benchmark
Usage: python bm_pystache.py -n <iterations>
"""

import time
import argparse
import sys
import random
import pystache

TEMPLATE = '''
<html>
  <head><title>{{title}}</title></head>
  <body>
    <h1>{{heading}}</h1>
    <ul>
    {{#users}}
      <li>{{name}} - {{email}}</li>
    {{/users}}
    </ul>
    <p>Total users: {{users.length}}</p>
  </body>
</html>
'''

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")

class UserList(object):
    def __init__(self, users):
        self.title = 'User List'
        self.heading = 'Users'
        self.users = users

def generate_context(num_users=100):
    users = []
    for i in range(num_users):
        users.append({
            'name': f'User{i}',
            'email': f'user{i}@example.com'
        })
    return {'title':'User List','heading':'Users','users':users}

def run_benchmark(iterations, num_users):
    renderer = pystache.Renderer()
    context = generate_context(num_users)

    for i in range(iterations):
        start = time.time()
        
        if HAS_HWCOUNTER:
            cycle_start = count()
            
        rendered = renderer.render(TEMPLATE, context)
        # simulate dynamic lookup
        _ = rendered.find('<ul>')
        
        if HAS_HWCOUNTER:
            cycle_end = count_end()
            cycles = cycle_end - cycle_start
        else:
            cycles = None
        
        end = time.time()
        total = end - start
        print(f"({total}, {cycles})")
        # print(f"\nRendered {iterations} iterations in {total:.4f}s, avg {total/iterations:.6f}s")
    return total

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n','--iterations',type=int,default=1000)
    parser.add_argument('--users',type=int,default=100)
    args = parser.parse_args()
    run_benchmark(args.iterations,args.users)

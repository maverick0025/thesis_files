#!/usr/bin/env python3
"""
Jinja2 template rendering benchmark
Usage: python bm_jinja2.py -n <iterations>
"""

import time
import argparse
import sys
import random
from jinja2 import Environment, FileSystemLoader, Template

# Sample template string for Jinja2
TEMPLATE_STR = '''
<html>
  <head><title>{{ title }}</title></head>
  <body>
    <h1>{{ heading }}</h1>
    <ul>
    {% for user in users %}
      <li>{{ user.name }} ({{ user.age }} yrs) - {{ user.email }}</li>
    {% endfor %}
    </ul>
    <p>Total users: {{ users|length }}</p>
  </body>
</html>
'''

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")

def generate_context(num_users=100):
    users = []
    for i in range(num_users):
        users.append({
            'name': f'User{i}',
            'age': random.randint(18, 80),
            'email': f'user{i}@example.com'
        })
    return {
        'title': 'User List',
        'heading': 'Users',
        'users': users
    }

def run_benchmark(iterations, num_users):
    env = Environment()
    template = env.from_string(TEMPLATE_STR)
    context = generate_context(num_users)

    for i in range(iterations):
        start = time.time()
        
        if HAS_HWCOUNTER:
            cycle_start = count()
                
        rendered = template.render(**context)
        # simulate dynamic filter usage
        _ = rendered.count('<li>')

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
    run_benchmark(args.iterations, args.users)

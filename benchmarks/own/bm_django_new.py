#!/usr/bin/env python3
"""
Django template rendering benchmark
Usage: python bm_django.py -n <iterations>
"""

import time
import argparse
import sys
import random
from django.conf import settings
from django.template import Template, Context

# Configure Django settings if not already configured
if not settings.configured:
    settings.configure(
        TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates'}]
    )

TEMPLATE_STR = '''
<html>
  <head><title>{{ title }}</title></head>
  <body>
    <h1>{{ heading }}</h1>
    <ul>
    {% for user in users %}
      <li>{{ user.name }} - {{ user.email|lower }}</li>
    {% endfor %}
    </ul>
    {% if users|length > 50 %}
      <p>Large user base</p>
    {% endif %}
    <p>Total users: {{ users|length }}</p>
  </body>
</html>
'''

def generate_context(num_users=100):
    users = []
    for i in range(num_users):
        users.append({
            'name': f'User{i}',
            'email': f'USER{i}@EXAMPLE.COM'
        })
    return Context({'title':'User List','heading':'Users','users':users})

def run_benchmark(iterations, num_users):
    template = Template(TEMPLATE_STR)
    context = generate_context(num_users)
    
    start = time.perf_counter()
    for i in range(iterations):
        rendered = template.render(context)
        _ = rendered.count('<li>')
        if i % 100 == 0:
            print(f"Iter {i}, length {len(rendered)}", end='\r')
    end = time.perf_counter()
    total = end - start
    print(f"\nRendered {iterations} iterations in {total:.4f}s, avg {total/iterations:.6f}s")
    return total

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('-n','--iterations',type=int,default=500)
    parser.add_argument('--users',type=int,default=100)
    args=parser.parse_args()
    run_benchmark(args.iterations,args.users)
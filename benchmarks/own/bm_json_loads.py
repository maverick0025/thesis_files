#!/usr/bin/env python3
"""
JSON parsing benchmark - tests polymorphic data structures and parsing performance.
Usage: python bm_json_loads.py -n <iterations>
"""

import json
import time
import argparse
import sys
from typing import List, Dict, Any

# Sample JSON data with various data types for polymorphism
JSON_DATA = [
    # Simple objects
    '{"name": "John", "age": 30, "city": "New York"}',
    '{"product": "laptop", "price": 999.99, "in_stock": true}',
    
    # Arrays with mixed types
    '[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]',
    '["apple", "banana", "cherry", "date", "elderberry"]',
    '[1, "two", 3.0, true, null, {"nested": "object"}]',
    
    # Nested structures
    '''
    {
        "users": [
            {"id": 1, "name": "Alice", "skills": ["Python", "JavaScript"], "active": true},
            {"id": 2, "name": "Bob", "skills": ["Java", "C++"], "active": false},
            {"id": 3, "name": "Charlie", "skills": ["Go", "Rust"], "active": true}
        ],
        "metadata": {
            "total_count": 3,
            "last_updated": "2025-10-06T09:35:00Z",
            "version": 1.2
        }
    }
    ''',
    
    # Large array
    f'[{", ".join(str(i) for i in range(1000))}]',
    
    # Complex nested structure
    '''
    {
        "data": {
            "transactions": [
                {"id": "tx1", "amount": 100.50, "currency": "USD", "items": [{"name": "Item1", "qty": 2}]},
                {"id": "tx2", "amount": 75.25, "currency": "EUR", "items": [{"name": "Item2", "qty": 1}, {"name": "Item3", "qty": 3}]},
                {"id": "tx3", "amount": 200.00, "currency": "GBP", "items": [{"name": "Item4", "qty": 1}]}
            ],
            "summary": {
                "total_transactions": 3,
                "total_amount": 375.75,
                "currencies": ["USD", "EUR", "GBP"]
            }
        }
    }
    '''
]

def parse_json_data(json_strings: List[str]) -> List[Any]:
    """Parse a list of JSON strings and return parsed objects."""
    results = []
    for json_str in json_strings:
        try:
            parsed = json.loads(json_str)
            results.append(parsed)
            
            # Perform some operations to trigger polymorphic behavior
            if isinstance(parsed, dict):
                # Access keys, count items
                keys = list(parsed.keys())
                for key in keys[:3]:  # Process first 3 keys
                    value = parsed.get(key)
                    if isinstance(value, (int, float)):
                        _ = value * 2
                    elif isinstance(value, str):
                        _ = len(value)
                    elif isinstance(value, list):
                        _ = len(value)
                        
            elif isinstance(parsed, list):
                # Process list elements
                for item in parsed[:10]:  # Process first 10 items
                    if isinstance(item, dict):
                        _ = len(item)
                    elif isinstance(item, (int, float)):
                        _ = item + 1
                    elif isinstance(item, str):
                        _ = item.upper()
                        
        except json.JSONDecodeError:
            results.append(None)
    
    return results

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")


def run_benchmark(iterations: int) -> float:
    """Run the JSON parsing benchmark for specified iterations."""
    # print(f"Running JSON parsing benchmark for {iterations} iterations...")
        
    for i in range(iterations):
        start_time = time.time()
        
        # Start CPU cycle counting
        if HAS_HWCOUNTER:
            cycle_start = count()
        
        # Parse all JSON strings
        parsed_data = parse_json_data(JSON_DATA)
        
        # Additional processing to stress the JIT
        total_items = 0
        for data in parsed_data:
            if data is not None:
                if isinstance(data, dict):
                    total_items += len(data)
                elif isinstance(data, list):
                    total_items += len(data)
            
        # End CPU cycle counting
        if HAS_HWCOUNTER:
            cycle_end = count_end()
            cycles = cycle_end - cycle_start
        else:
            cycles = None
            
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"({execution_time}, {cycles})")
    
    return execution_time

def main():
    parser = argparse.ArgumentParser(description="JSON parsing benchmark")
    parser.add_argument("-n", "--iterations", type=int, default=1000,
                       help="Number of iterations to run (default: 1000)")
    
    args = parser.parse_args()
    
    if args.iterations <= 0:
        print("Error: iterations must be positive")
        sys.exit(1)
    
    try:
        execution_time = run_benchmark(args.iterations)
        # print(f"Benchmark completed successfully in {execution_time:.4f} seconds")
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running benchmark: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
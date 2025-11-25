#!/usr/bin/env python3
"""
Pickle serialization benchmark - tests object serialization/deserialization performance.
Usage: python bm_pickle.py -n <iterations>
"""

import pickle
import time
import argparse
import sys
from typing import List, Dict, Any, NamedTuple
import random
import string

class Person:
    """Sample class for serialization."""
    def __init__(self, name: str, age: int, email: str, skills: List[str]):
        self.name = name
        self.age = age
        self.email = email
        self.skills = skills
        self.metadata = {
            'created_at': '2025-10-06',
            'department': random.choice(['Engineering', 'Sales', 'Marketing', 'HR']),
            'salary': random.randint(50000, 150000)
        }
    
    def __repr__(self):
        return f"Person(name='{self.name}', age={self.age})"

class Transaction(NamedTuple):
    """Transaction record using NamedTuple."""
    id: str
    amount: float
    currency: str
    description: str

def generate_test_data() -> Dict[str, Any]:
    """Generate complex nested data structures for serialization."""
    
    # Generate random people
    people = []
    for i in range(100):
        name = f"Person_{i}"
        age = random.randint(20, 65)
        email = f"person{i}@example.com"
        skills = random.sample(['Python', 'Java', 'JavaScript', 'C++', 'Go', 'Rust'], 
                              k=random.randint(1, 4))
        people.append(Person(name, age, email, skills))
    
    # Generate transactions
    transactions = []
    for i in range(200):
        transaction = Transaction(
            id=f"tx_{i:04d}",
            amount=round(random.uniform(10.0, 1000.0), 2),
            currency=random.choice(['USD', 'EUR', 'GBP', 'JPY']),
            description=f"Transaction {i}"
        )
        transactions.append(transaction)
    
    # Create nested data structure
    data = {
        'people': people,
        'transactions': transactions,
        'metadata': {
            'version': 1.0,
            'created_by': 'benchmark_script',
            'stats': {
                'total_people': len(people),
                'total_transactions': len(transactions),
                'total_amount': sum(t.amount for t in transactions)
            }
        },
        'config': {
            'settings': {
                'debug': True,
                'max_connections': 100,
                'timeout': 30.0,
                'features': ['feature_a', 'feature_b', 'feature_c']
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'benchmark_db'
            }
        },
        # Large list of mixed types
        'mixed_data': [
            i if i % 3 == 0 else f"string_{i}" if i % 3 == 1 else float(i) * 1.5
            for i in range(1000)
        ],
        # Nested dictionaries
        'nested_dicts': {
            f"level1_{i}": {
                f"level2_{j}": {
                    f"level3_{k}": f"value_{i}_{j}_{k}"
                    for k in range(5)
                }
                for j in range(10)
            }
            for i in range(5)
        }
    }
    
    return data

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")


def run_pickle_benchmark(data: Any, iterations: int) -> float:
    """Run pickle serialization/deserialization benchmark."""
    # print(f"Running pickle benchmark for {iterations} iterations...")
    
    
    for i in range(iterations):
    
        start_time = time.time()
        
        # Start CPU cycle counting
        if HAS_HWCOUNTER:
            cycle_start = count()
                
        # Serialize data
        serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        
        # Deserialize data
        deserialized = pickle.loads(serialized)
        
        # Perform some operations on deserialized data to trigger polymorphism
        if isinstance(deserialized, dict):
            # Access various data types
            people = deserialized.get('people', [])
            transactions = deserialized.get('transactions', [])
            mixed_data = deserialized.get('mixed_data', [])
            
            # Process people (custom objects)
            total_age = 0
            for person in people[:10]:  # Process first 10
                if hasattr(person, 'age'):
                    total_age += person.age
            
            # Process transactions (NamedTuples)
            total_amount = 0.0
            for transaction in transactions[:20]:  # Process first 20
                total_amount += transaction.amount
            
            # Process mixed data (polymorphic list)
            processed_items = 0
            for item in mixed_data[:50]:  # Process first 50
                if isinstance(item, int):
                    _ = item * 2
                elif isinstance(item, str):
                    _ = len(item)
                elif isinstance(item, float):
                    _ = item + 1.0
                processed_items += 1
        
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
    parser = argparse.ArgumentParser(description="Pickle serialization benchmark")
    parser.add_argument("-n", "--iterations", type=int, default=100,
                       help="Number of iterations to run (default: 100)")
    
    args = parser.parse_args()
    
    if args.iterations <= 0:
        print("Error: iterations must be positive")
        sys.exit(1)
    
    try:
        # Generate test data once
        # print("Generating test data...")
        test_data = generate_test_data()
        # print(f"Generated test data with {len(test_data)} top-level keys")
        
        # Run benchmark
        execution_time = run_pickle_benchmark(test_data, args.iterations)
        # print(f"Benchmark completed successfully in {execution_time:.4f} seconds")
        
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running benchmark: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Data aggregation benchmark - tests dict/list operations and data manipulation.
Usage: python data_aggregation.py -n <iterations>
"""

import time
import argparse
import sys
import random
import math
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict, Counter
from itertools import groupby

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")
    
def generate_sample_data() -> Dict[str, Any]:
    """Generate sample data for aggregation operations."""
    
    # Generate transactions
    transactions = []
    for i in range(10000):
        transaction = {
            'id': f'tx_{i:06d}',
            'user_id': f'user_{random.randint(1, 1000):04d}',
            'product_id': f'prod_{random.randint(1, 500):03d}',
            'category': random.choice(['Electronics', 'Clothing', 'Books', 'Home', 'Sports', 'Food']),
            'amount': round(random.uniform(5.0, 500.0), 2),
            'quantity': random.randint(1, 10),
            'date': f'2025-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
            'region': random.choice(['North', 'South', 'East', 'West', 'Central']),
            'payment_method': random.choice(['Credit', 'Debit', 'Cash', 'PayPal', 'Crypto']),
            'discount': round(random.uniform(0.0, 0.3), 2) if random.random() < 0.3 else 0.0
        }
        transactions.append(transaction)
    
    # Generate users
    users = []
    for i in range(1, 1001):
        user = {
            'id': f'user_{i:04d}',
            'name': f'User_{i}',
            'age': random.randint(18, 75),
            'email': f'user{i}@example.com',
            'registration_date': f'202{random.randint(0, 5)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
            'tier': random.choice(['Bronze', 'Silver', 'Gold', 'Platinum']),
            'preferences': random.sample(['Electronics', 'Clothing', 'Books', 'Home', 'Sports', 'Food'], 
                                       k=random.randint(1, 4))
        }
        users.append(user)
    
    # Generate products
    products = []
    for i in range(1, 501):
        product = {
            'id': f'prod_{i:03d}',
            'name': f'Product_{i}',
            'category': random.choice(['Electronics', 'Clothing', 'Books', 'Home', 'Sports', 'Food']),
            'price': round(random.uniform(10.0, 1000.0), 2),
            'rating': round(random.uniform(1.0, 5.0), 1),
            'reviews_count': random.randint(0, 1000),
            'in_stock': random.choice([True, False]),
            'tags': random.sample(['popular', 'new', 'sale', 'premium', 'eco-friendly', 'bestseller'], 
                                 k=random.randint(0, 3))
        }
        products.append(product)
    
    return {
        'transactions': transactions,
        'users': users,
        'products': products
    }

def aggregate_transactions_by_category(transactions: List[Dict]) -> Dict[str, Any]:
    """Aggregate transactions by category."""
    category_stats = defaultdict(lambda: {
        'total_amount': 0.0,
        'total_quantity': 0,
        'transaction_count': 0,
        'unique_users': set(),
        'avg_transaction_value': 0.0,
        'top_products': Counter()
    })
    
    for txn in transactions:
        category = txn['category']
        stats = category_stats[category]
        
        stats['total_amount'] += txn['amount']
        stats['total_quantity'] += txn['quantity']
        stats['transaction_count'] += 1
        stats['unique_users'].add(txn['user_id'])
        stats['top_products'][txn['product_id']] += 1
    
    # Calculate averages and convert sets to counts
    for category, stats in category_stats.items():
        if stats['transaction_count'] > 0:
            stats['avg_transaction_value'] = stats['total_amount'] / stats['transaction_count']
        stats['unique_users'] = len(stats['unique_users'])
        stats['top_products'] = dict(stats['top_products'].most_common(10))
    
    return dict(category_stats)

def aggregate_by_region_and_payment(transactions: List[Dict]) -> Dict[str, Dict[str, Any]]:
    """Create nested aggregation by region and payment method."""
    nested_stats = defaultdict(lambda: defaultdict(lambda: {
        'count': 0,
        'total_amount': 0.0,
        'avg_amount': 0.0,
        'transactions': []
    }))
    
    for txn in transactions:
        region = txn['region']
        payment = txn['payment_method']
        stats = nested_stats[region][payment]
        
        stats['count'] += 1
        stats['total_amount'] += txn['amount']
        stats['transactions'].append(txn['id'])
    
    # Calculate averages
    for region, payment_methods in nested_stats.items():
        for payment, stats in payment_methods.items():
            if stats['count'] > 0:
                stats['avg_amount'] = stats['total_amount'] / stats['count']
    
    return {region: dict(payments) for region, payments in nested_stats.items()}

def analyze_user_behavior(transactions: List[Dict], users: List[Dict]) -> Dict[str, Any]:
    """Analyze user purchasing behavior."""
    
    # Create user lookup
    user_lookup = {user['id']: user for user in users}
    
    # Aggregate user transactions
    user_stats = defaultdict(lambda: {
        'total_spent': 0.0,
        'transaction_count': 0,
        'categories': set(),
        'avg_order_value': 0.0,
        'preferred_payment': Counter(),
        'monthly_spending': defaultdict(float)
    })
    
    for txn in transactions:
        user_id = txn['user_id']
        stats = user_stats[user_id]
        
        stats['total_spent'] += txn['amount']
        stats['transaction_count'] += 1
        stats['categories'].add(txn['category'])
        stats['preferred_payment'][txn['payment_method']] += 1
        
        # Extract month for monthly spending
        month = txn['date'][:7]  # YYYY-MM
        stats['monthly_spending'][month] += txn['amount']
    
    # Calculate derived metrics
    for user_id, stats in user_stats.items():
        if stats['transaction_count'] > 0:
            stats['avg_order_value'] = stats['total_spent'] / stats['transaction_count']
        stats['categories'] = len(stats['categories'])
        stats['preferred_payment'] = stats['preferred_payment'].most_common(1)[0][0] if stats['preferred_payment'] else None
        stats['monthly_spending'] = dict(stats['monthly_spending'])
        
        # Add user demographics
        if user_id in user_lookup:
            user_info = user_lookup[user_id]
            stats['age'] = user_info['age']
            stats['tier'] = user_info['tier']
    
    return dict(user_stats)

def create_complex_aggregations(data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform complex multi-level aggregations."""
    transactions = data['transactions']
    users = data['users']
    products = data['products']
    
    # Create product lookup
    product_lookup = {prod['id']: prod for prod in products}
    
    # Multi-dimensional analysis
    complex_stats = {
        'category_region_analysis': defaultdict(lambda: defaultdict(list)),
        'tier_spending_analysis': defaultdict(lambda: {'total': 0.0, 'count': 0, 'products': set()}),
        'product_performance': defaultdict(lambda: {
            'revenue': 0.0, 'quantity_sold': 0, 'unique_buyers': set(), 
            'avg_rating_weighted': 0.0, 'regions': set()
        }),
        'temporal_patterns': defaultdict(lambda: defaultdict(float)),
        'cross_category_analysis': defaultdict(lambda: defaultdict(int))
    }
    
    # Create user lookup for tier information
    user_lookup = {user['id']: user for user in users}
    
    for txn in transactions:
        category = txn['category']
        region = txn['region']
        user_id = txn['user_id']
        product_id = txn['product_id']
        amount = txn['amount']
        quantity = txn['quantity']
        date = txn['date']
        
        # Category-Region analysis
        complex_stats['category_region_analysis'][category][region].append(amount)
        
        # Tier-based spending analysis
        if user_id in user_lookup:
            tier = user_lookup[user_id]['tier']
            tier_stats = complex_stats['tier_spending_analysis'][tier]
            tier_stats['total'] += amount
            tier_stats['count'] += 1
            tier_stats['products'].add(product_id)
        
        # Product performance
        prod_stats = complex_stats['product_performance'][product_id]
        prod_stats['revenue'] += amount
        prod_stats['quantity_sold'] += quantity
        prod_stats['unique_buyers'].add(user_id)
        prod_stats['regions'].add(region)
        
        # Temporal patterns (monthly)
        month = date[:7]
        complex_stats['temporal_patterns'][month][category] += amount
    
    # Process aggregated data
    for category, regions in complex_stats['category_region_analysis'].items():
        for region, amounts in regions.items():
            complex_stats['category_region_analysis'][category][region] = {
                'avg_amount': sum(amounts) / len(amounts),
                'total_amount': sum(amounts),
                'transaction_count': len(amounts),
                'min_amount': min(amounts),
                'max_amount': max(amounts)
            }
    
    # Calculate tier averages
    for tier, stats in complex_stats['tier_spending_analysis'].items():
        if stats['count'] > 0:
            stats['avg_spending'] = stats['total'] / stats['count']
        stats['unique_products'] = len(stats['products'])
        del stats['products']  # Remove set for serialization
    
    # Finalize product performance
    for product_id, stats in complex_stats['product_performance'].items():
        stats['unique_buyers'] = len(stats['unique_buyers'])
        stats['regions'] = len(stats['regions'])
        if product_id in product_lookup:
            product_info = product_lookup[product_id]
            stats['category'] = product_info['category']
            stats['base_price'] = product_info['price']
    
    return {
        k: dict(v) if hasattr(v, 'items') else v 
        for k, v in complex_stats.items()
    }

def run_aggregation_benchmark(iterations: int) -> float:
    """Run the data aggregation benchmark."""
    # print(f"Running data aggregation benchmark for {iterations} iterations...")
    
    # Generate data once
    # print("Generating sample data...")
    data = generate_sample_data()
    # print(f"Generated {len(data['transactions'])} transactions, {len(data['users'])} users, {len(data['products'])} products")
        
    for i in range(iterations):
        start_time = time.time()
        
        # Start CPU cycle counting
        if HAS_HWCOUNTER:
            cycle_start = count()
        
        # Perform various aggregations
        category_agg = aggregate_transactions_by_category(data['transactions'])
        region_payment_agg = aggregate_by_region_and_payment(data['transactions'])
        user_behavior = analyze_user_behavior(data['transactions'], data['users'])
        complex_agg = create_complex_aggregations(data)
        
        # Additional list/dict operations
        if i % 5 == 0:
            # Sorting and filtering operations
            sorted_transactions = sorted(data['transactions'], key=lambda x: x['amount'], reverse=True)
            top_transactions = sorted_transactions[:100]
            
            # Dictionary comprehensions
            high_value_users = {
                user_id: stats for user_id, stats in user_behavior.items()
                if stats['total_spent'] > 1000
            }
            
            # List comprehensions with filtering
            electronics_transactions = [
                txn for txn in data['transactions'] 
                if txn['category'] == 'Electronics' and txn['amount'] > 100
            ]
            
            # Set operations
            electronic_users = {txn['user_id'] for txn in electronics_transactions}
            all_users = {user['id'] for user in data['users']}
            non_electronic_users = all_users - electronic_users
        
        # if i % 10 == 0:
            # print(f"Iteration {i}, processed {len(category_agg)} categories", end='\r')
        # End CPU cycle counting
        if HAS_HWCOUNTER:
            cycle_end = count_end()
            cycles = cycle_end - cycle_start
        else:
            cycles = None
            
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"({execution_time}, {cycles})")
            
    # print(f"\nCompleted {iterations} iterations in {execution_time:.4f} seconds")
    # print(f"Average time per iteration: {execution_time/iterations:.6f} seconds")
    
    return execution_time

def main():
    parser = argparse.ArgumentParser(description="Data aggregation benchmark")
    parser.add_argument("-n", "--iterations", type=int, default=5,
                       help="Number of iterations to run (default: 5)")
    
    args = parser.parse_args()
    
    if args.iterations <= 0:
        print("Error: iterations must be positive")
        sys.exit(1)
    
    try:
        execution_time = run_aggregation_benchmark(args.iterations)
        
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running benchmark: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
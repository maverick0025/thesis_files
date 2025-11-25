#!/usr/bin/env python3
"""
CSV processing benchmark - tests string manipulation and data parsing.
Usage: python csv_processing.py -n <iterations>
"""

import csv
import time
import argparse
import sys
import io
import random
import string
from typing import List, Dict, Any

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")

def generate_csv_data() -> str:
    """Generate sample CSV data for processing."""
    
    # CSV headers
    headers = [
        'id', 'name', 'email', 'age', 'department', 'salary', 
        'hire_date', 'performance_score', 'location', 'skills'
    ]
    
    departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations']
    locations = ['New York', 'San Francisco', 'Chicago', 'Austin', 'Seattle', 'Boston']
    skills_pool = ['Python', 'Java', 'JavaScript', 'SQL', 'Excel', 'Leadership', 'Communication']
    
    rows = []
    rows.append(','.join(headers))  # Header row
    
    # Generate 5000 data rows
    for i in range(5000):
        # Generate random data
        employee_id = f"EMP{i:04d}"
        name = f"Employee_{i}"
        email = f"employee{i}@company.com"
        age = random.randint(22, 65)
        department = random.choice(departments)
        salary = random.randint(40000, 200000)
        hire_date = f"2{random.randint(15, 25)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        performance_score = round(random.uniform(1.0, 5.0), 1)
        location = random.choice(locations)
        skills = ';'.join(random.sample(skills_pool, k=random.randint(2, 5)))
        
        row = [
            employee_id, name, email, str(age), department, str(salary),
            hire_date, str(performance_score), location, skills
        ]
        rows.append(','.join(f'"{field}"' if ',' in field or '"' in field else field for field in row))
    
    return '\n'.join(rows)

def process_csv_data(csv_content: str) -> Dict[str, Any]:
    """Process CSV data with various string operations."""
    
    # Parse CSV
    csv_file = io.StringIO(csv_content)
    reader = csv.DictReader(csv_file)
    
    # Statistics to calculate
    stats = {
        'total_employees': 0,
        'department_counts': {},
        'age_distribution': {'under_30': 0, '30_to_50': 0, 'over_50': 0},
        'salary_stats': {'min': float('inf'), 'max': 0, 'total': 0},
        'location_distribution': {},
        'skills_frequency': {},
        'avg_performance': 0,
        'processed_names': []
    }
    
    total_performance = 0
    
    for row in reader:
        stats['total_employees'] += 1
        
        # Department analysis
        dept = row['department']
        stats['department_counts'][dept] = stats['department_counts'].get(dept, 0) + 1
        
        # Age analysis with string conversion and comparison
        age = int(row['age'])
        if age < 30:
            stats['age_distribution']['under_30'] += 1
        elif age <= 50:
            stats['age_distribution']['30_to_50'] += 1
        else:
            stats['age_distribution']['over_50'] += 1
        
        # Salary analysis
        salary = int(row['salary'])
        stats['salary_stats']['min'] = min(stats['salary_stats']['min'], salary)
        stats['salary_stats']['max'] = max(stats['salary_stats']['max'], salary)
        stats['salary_stats']['total'] += salary
        
        # Location analysis
        location = row['location']
        stats['location_distribution'][location] = stats['location_distribution'].get(location, 0) + 1
        
        # Skills analysis (string splitting and processing)
        skills = row['skills'].split(';')
        for skill in skills:
            skill = skill.strip()
            stats['skills_frequency'][skill] = stats['skills_frequency'].get(skill, 0) + 1
        
        # Performance score
        performance = float(row['performance_score'])
        total_performance += performance
        
        # Name processing (string manipulation)
        name = row['name']
        # Various string operations
        processed_name = {
            'original': name,
            'uppercase': name.upper(),
            'lowercase': name.lower(),
            'length': len(name),
            'reversed': name[::-1],
            'words': name.split('_'),
            'starts_with_vowel': name[0].lower() in 'aeiou'
        }
        stats['processed_names'].append(processed_name)
        
        # Email validation (string pattern matching)
        email = row['email']
        is_valid_email = '@' in email and '.' in email.split('@')[1]
        
        # Date parsing and manipulation
        hire_date = row['hire_date']
        year, month, day = hire_date.split('-')
        hire_year = int(year)
        
        # Additional string processing
        if stats['total_employees'] % 100 == 0:
            # Perform some intensive string operations every 100 rows
            text_data = f"{name}_{dept}_{location}_{skills}"
            
            # String transformations
            _ = text_data.replace('_', '-')
            _ = text_data.split('_')
            _ = ''.join(reversed(text_data))
            _ = text_data.count('e')
            _ = text_data.find('Engineering')
    
    # Calculate averages
    if stats['total_employees'] > 0:
        stats['avg_performance'] = total_performance / stats['total_employees']
        stats['salary_stats']['average'] = stats['salary_stats']['total'] / stats['total_employees']
    
    return stats

def run_csv_benchmark(iterations: int) -> float:
    """Run the CSV processing benchmark."""

    csv_data = generate_csv_data()
    
    for i in range(iterations):
        
        start_time = time.time()
        # Start CPU cycle counting
        if HAS_HWCOUNTER:
            cycle_start = count()
                
        # Process the CSV data
        stats = process_csv_data(csv_data)
        
        # Additional string processing on results
        if i % 10 == 0:
            # Perform extra string operations on statistics
            for dept, empcount in stats['department_counts'].items():
                _ = f"Department {dept} has {empcount} employees"
                _ = dept.upper()
                _ = dept.replace('ing', 'ING')
            
            # Process skill names
            for skill, freq in list(stats['skills_frequency'].items())[:10]:
                _ = skill.lower()
                _ = skill.replace('Script', 'script')
                _ = len(skill)
        
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
    parser = argparse.ArgumentParser(description="CSV processing benchmark")
    parser.add_argument("-n", "--iterations", type=int, default=10,
                       help="Number of iterations to run (default: 10)")
    
    args = parser.parse_args()
    
    if args.iterations <= 0:
        print("Error: iterations must be positive")
        sys.exit(1)
    
    try:
        execution_time = run_csv_benchmark(args.iterations)
        # print(f"Benchmark completed successfully in {execution_time:.4f} seconds")
        
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running benchmark: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
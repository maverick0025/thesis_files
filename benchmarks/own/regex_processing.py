#!/usr/bin/env python3
"""
Regex processing benchmark - tests pattern matching and string operations.
Usage: python regex_processing.py -n <iterations>
"""

import re
import time
import argparse
import sys
import random
import string
from typing import List, Dict, Any, Pattern

def generate_text_data() -> List[str]:
    """Generate various text samples for regex processing."""
    
    # Email patterns
    emails = [
        f"user{i}@example.com" for i in range(1000)
    ] + [
        f"test.user.{i}@company-{j}.org" for i in range(100) for j in range(5)
    ] + [
        f"invalid-email-{i}" for i in range(50)  # Invalid emails for negative matches
    ]
    
    # Phone numbers in various formats
    phone_numbers = [
        f"({random.randint(100, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
        for _ in range(500)
    ] + [
        f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        for _ in range(500)
    ] + [
        f"+1-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        for _ in range(300)
    ]
    
    # URLs and web addresses
    urls = [
        f"https://www.example{i}.com/path/to/resource" for i in range(200)
    ] + [
        f"http://subdomain.site{i}.org/api/v{j}/endpoint" 
        for i in range(100) for j in range(1, 4)
    ] + [
        f"ftp://files.server{i}.net/downloads/file{j}.zip"
        for i in range(50) for j in range(20)
    ]
    
    # Log entries (common log format)
    log_entries = []
    for i in range(2000):
        ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        timestamp = f"[06/Oct/2025:12:34:{random.randint(10, 59):02d} +0000]"
        method = random.choice(['GET', 'POST', 'PUT', 'DELETE'])
        path = f"/api/v{random.randint(1, 3)}/resource/{random.randint(1, 1000)}"
        status = random.choice([200, 201, 400, 404, 500])
        size = random.randint(100, 10000)
        
        log_entry = f'{ip} - - {timestamp} "{method} {path} HTTP/1.1" {status} {size}'
        log_entries.append(log_entry)
    
    # Code snippets (Python-like)
    code_snippets = [
        f'def function_{i}(param1, param2={j}):' for i in range(100) for j in range(5)
    ] + [
        f'class MyClass{i}(BaseClass):' for i in range(50)
    ] + [
        f'import {module}' for module in ['os', 'sys', 'json', 'time', 're', 'random'] * 20
    ] + [
        f'variable_{i} = "{random.choice(string.ascii_letters)}" * {random.randint(1, 10)}'
        for i in range(200)
    ]
    
    # Free text with various patterns - FIXED SYNTAX
    sentences = []
    for i in range(400):
        sentences.extend([
            f"The quick brown fox jumps over the lazy dog {i} times.",
            f"In the year {2020 + i % 10}, we discovered {random.randint(100, 999)} new species.",
            f"Price: ${random.randint(10, 9999)}.{random.randint(10, 99)} (USD)",
            f"Contact us at info@company{i}.com or call (555) {random.randint(100, 999)}-{random.randint(1000, 9999)}",
            f"Version {random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 99)} released on {random.randint(1, 12)}/{random.randint(1, 28)}/2025"
        ])
    
    # Combine all text data
    all_text = emails + phone_numbers + urls + log_entries + code_snippets + sentences
    random.shuffle(all_text)
    
    return all_text

def create_regex_patterns() -> Dict[str, Pattern]:
    """Create compiled regex patterns for testing."""
    
    patterns = {
        # Email validation
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        
        # Phone numbers (various formats)
        'phone_us': re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
        'phone_intl': re.compile(r'\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'),
        
        # URLs
        'url': re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?'),
        
        # IP addresses
        'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
        
        # Dates (various formats)
        'date_mdy': re.compile(r'\b\d{1,2}/\d{1,2}/\d{4}\b'),
        'date_ymd': re.compile(r'\b\d{4}-\d{2}-\d{2}\b'),
        
        # Numbers and prices
        'price': re.compile(r'\$\d+(?:\.\d{2})?'),
        'version': re.compile(r'\b\d+\.\d+\.\d+\b'),
        
        # Code patterns
        'python_function': re.compile(r'def\s+(\w+)\s*\([^)]*\):'),
        'python_class': re.compile(r'class\s+(\w+)(?:\([^)]*\))?:'),
        'python_import': re.compile(r'import\s+(\w+(?:\.\w+)*)'),
        
        # Log parsing
        'log_entry': re.compile(r'(\d+\.\d+\.\d+\.\d+).*\[([^\]]+)\].*"(\w+)\s+([^"]+)".*(\d+)\s+(\d+)'),
        
        # Words and identifiers
        'word': re.compile(r'\b\w+\b'),
        'identifier': re.compile(r'\b[a-zA-Z_]\w*\b'),
        
        # Complex patterns
        'html_tag': re.compile(r'<(\w+)(?:\s+[^>]*)?>(.*?)</\1>', re.DOTALL),
        'quoted_string': re.compile(r'"([^"\\]|\\.)*"'),
    }
    
    return patterns

def process_text_with_regex(text_data: List[str], patterns: Dict[str, Pattern]) -> Dict[str, Any]:
    """Process text data with various regex patterns."""
    
    results = {
        'matches_found': {},
        'extracted_data': {},
        'validation_results': {},
        'statistics': {}
    }
    
    # Initialize counters
    for pattern_name in patterns:
        results['matches_found'][pattern_name] = 0
        results['extracted_data'][pattern_name] = []
    
    # Process each text sample
    for text in text_data:
        # Test each pattern
        for pattern_name, pattern in patterns.items():
            matches = pattern.findall(text)
            
            if matches:
                results['matches_found'][pattern_name] += len(matches)
                
                # Store some sample matches (limit to avoid memory issues)
                if len(results['extracted_data'][pattern_name]) < 50:
                    results['extracted_data'][pattern_name].extend(matches[:5])
        
        # Specific validation tasks
        # Email validation
        if '@' in text:
            email_matches = patterns['email'].findall(text)
            for email in email_matches:
                # Additional validation logic
                is_valid = '.' in email.split('@')[1] if '@' in email else False
                results['validation_results'][email] = is_valid
        
        # URL validation
        if 'http' in text.lower():
            url_matches = patterns['url'].findall(text)
            for url in url_matches:
                # Check URL structure
                has_protocol = url.startswith(('http://', 'https://'))
                results['validation_results'][url] = has_protocol
    
    # Calculate statistics
    total_texts = len(text_data)
    for pattern_name, count in results['matches_found'].items():
        results['statistics'][pattern_name] = {
            'total_matches': count,
            'match_rate': count / total_texts if total_texts > 0 else 0,
            'avg_matches_per_text': count / total_texts if total_texts > 0 else 0
        }
    
    return results

def perform_complex_regex_operations(text_data: List[str]) -> Dict[str, Any]:
    """Perform complex regex operations including substitutions and parsing."""
    
    # Text transformations
    transformed_texts = []
    substitution_stats = {'email_masked': 0, 'phone_masked': 0, 'url_shortened': 0}
    
    for text in text_data[:500]:  # Process subset for complex operations
        # Mask emails
        masked_text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                            '[EMAIL]', text)
        if masked_text != text:
            substitution_stats['email_masked'] += 1
        
        # Mask phone numbers
        masked_text = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', 
                           '[PHONE]', masked_text)
        if '[PHONE]' in masked_text:
            substitution_stats['phone_masked'] += 1
        
        # Shorten URLs
        masked_text = re.sub(r'https?://[^\s]+', '[URL]', masked_text)
        if '[URL]' in masked_text:
            substitution_stats['url_shortened'] += 1
        
        transformed_texts.append(masked_text)
    
    # Extract structured data from log entries
    log_data = []
    log_pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+).*\[([^\]]+)\].*"(\w+)\s+([^"]+)".*(\d+)\s+(\d+)')
    
    for text in text_data:
        match = log_pattern.search(text)
        if match:
            ip, timestamp, method, path, status, size = match.groups()
            log_entry = {
                'ip': ip,
                'timestamp': timestamp,
                'method': method,
                'path': path,
                'status': int(status),
                'size': int(size)
            }
            log_data.append(log_entry)
    
    # Word frequency analysis
    word_pattern = re.compile(r'\b\w+\b')
    word_counts = {}
    
    for text in text_data[:1000]:  # Process subset
        words = word_pattern.findall(text.lower())
        for word in words:
            if len(word) > 3:  # Only count words longer than 3 characters
                word_counts[word] = word_counts.get(word, 0) + 1
    
    # Get top words
    top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    
    return {
        'transformed_texts_count': len(transformed_texts),
        'substitution_stats': substitution_stats,
        'log_entries_parsed': len(log_data),
        'word_frequency': dict(top_words),
        'total_unique_words': len(word_counts)
    }

def run_regex_benchmark(iterations: int) -> float:
    """Run the regex processing benchmark."""
    print(f"Running regex processing benchmark for {iterations} iterations...")
    
    # Generate data and compile patterns once
    print("Generating text data and compiling patterns...")
    text_data = generate_text_data()
    patterns = create_regex_patterns()
    print(f"Generated {len(text_data)} text samples with {len(patterns)} regex patterns")
    
    start_time = time.perf_counter()
    
    for i in range(iterations):
        # Basic pattern matching
        basic_results = process_text_with_regex(text_data, patterns)
        
        # Complex regex operations
        complex_results = perform_complex_regex_operations(text_data)
        
        # Additional regex stress tests
        if i % 3 == 0:
            # Compile new patterns dynamically
            dynamic_pattern = re.compile(f'\\b\\w{{{random.randint(3, 8)}}}\\b')
            dynamic_matches = []
            for text in text_data[:100]:
                matches = dynamic_pattern.findall(text)
                dynamic_matches.extend(matches)
            
            # Split operations
            for text in text_data[:50]:
                words = re.split(r'\W+', text)
                sentences = re.split(r'[.!?]+', text)
        
        if i % 5 == 0:
            print(f"Iteration {i}, processed {len(text_data)} texts", end='\r')
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    
    print(f"\nCompleted {iterations} iterations in {execution_time:.4f} seconds")
    print(f"Average time per iteration: {execution_time/iterations:.6f} seconds")
    print(f"Processed {len(text_data)} text samples per iteration")
    
    return execution_time

def main():
    parser = argparse.ArgumentParser(description="Regex processing benchmark")
    parser.add_argument("-n", "--iterations", type=int, default=5,
                       help="Number of iterations to run (default: 5)")
    
    args = parser.parse_args()
    
    if args.iterations <= 0:
        print("Error: iterations must be positive")
        sys.exit(1)
    
    try:
        execution_time = run_regex_benchmark(args.iterations)
        print(f"Benchmark completed successfully in {execution_time:.4f} seconds")
        
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running benchmark: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
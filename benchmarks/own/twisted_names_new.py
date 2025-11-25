#!/usr/bin/env python3
"""
Twisted names (DNS) benchmark - tests DNS resolution, caching, and name service operations.
Usage: python twisted_names.py -n <iterations>
"""

import time
import argparse
import sys
import random
import socket
import threading
from typing import List, Dict, Any, Optional, Tuple

try:
    from twisted.names import dns, server, client, cache
    from twisted.names.resolve import ResolverChain
    from twisted.internet import reactor, defer
    from twisted.names.common import ResolverBase
    TWISTED_AVAILABLE = True
except ImportError:
    # print("Warning: Twisted.names not available. Using fallback implementation.")
    TWISTED_AVAILABLE = False

# DNS record types
A_RECORD = 1
NS_RECORD = 2
CNAME_RECORD = 5
SOA_RECORD = 6
PTR_RECORD = 12
MX_RECORD = 15
TXT_RECORD = 16
AAAA_RECORD = 28

try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")

class MockDNSRecord:
    """Mock DNS record for testing without Twisted."""
    def __init__(self, name: str, record_type: int, data: str, ttl: int = 300):
        self.name = name
        self.type = record_type
        self.data = data
        self.ttl = ttl
        self.timestamp = time.time()
    
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl
    
    def __str__(self):
        return f"{self.name} {self.type} {self.data}"

class MockDNSCache:
    """Mock DNS cache for testing without Twisted."""
    def __init__(self):
        self._cache: Dict[Tuple[str, int], MockDNSRecord] = {}
        self._stats = {'hits': 0, 'misses': 0, 'expired': 0}
    
    def get(self, name: str, record_type: int) -> Optional[MockDNSRecord]:
        key = (name.lower(), record_type)
        if key in self._cache:
            record = self._cache[key]
            if record.is_expired():
                del self._cache[key]
                self._stats['expired'] += 1
                return None
            else:
                self._stats['hits'] += 1
                return record
        self._stats['misses'] += 1
        return None
    
    def put(self, name: str, record_type: int, data: str, ttl: int = 300):
        key = (name.lower(), record_type)
        self._cache[key] = MockDNSRecord(name, record_type, data, ttl)
    
    def get_stats(self) -> Dict[str, int]:
        return self._stats.copy()
    
    def clear_expired(self):
        """Remove expired entries from cache."""
        expired_keys = []
        for key, record in self._cache.items():
            if record.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            self._stats['expired'] += 1

class MockDNSResolver:
    """Mock DNS resolver for testing without Twisted."""
    def __init__(self):
        self.cache = MockDNSCache()
        self._fake_dns_db = self._create_fake_dns_db()
        self._query_count = 0
    
    def _create_fake_dns_db(self) -> Dict[Tuple[str, int], str]:
        """Create fake DNS database for testing."""
        db = {}
        
        # Add common domains
        domains = [
            'google.com', 'facebook.com', 'amazon.com', 'microsoft.com',
            'apple.com', 'twitter.com', 'linkedin.com', 'github.com',
            'stackoverflow.com', 'reddit.com', 'wikipedia.org', 'youtube.com'
        ]
        
        for domain in domains:
            # A records
            db[(domain, A_RECORD)] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            
            # MX records
            db[(domain, MX_RECORD)] = f"mail.{domain}"
            
            # TXT records
            db[(domain, TXT_RECORD)] = f"v=spf1 include:_spf.{domain} ~all"
            
            # NS records
            db[(domain, NS_RECORD)] = f"ns1.{domain}"
        
        # Add some subdomains
        for domain in domains[:5]:
            for subdomain in ['www', 'mail', 'api', 'cdn']:
                full_domain = f"{subdomain}.{domain}"
                db[(full_domain, A_RECORD)] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        
        return db
    
    def resolve(self, name: str, record_type: int = A_RECORD) -> Optional[MockDNSRecord]:
        """Resolve DNS name to record."""
        self._query_count += 1
        
        # Check cache first
        cached = self.cache.get(name, record_type)
        if cached:
            return cached
        
        # Simulate network delay
        delay = random.uniform(0.001, 0.05)
        time.sleep(delay)
        
        # Look up in fake database
        key = (name.lower(), record_type)
        if key in self._fake_dns_db:
            data = self._fake_dns_db[key]
            ttl = random.randint(60, 3600)  # Random TTL between 1 minute and 1 hour
            
            # Cache the result
            self.cache.put(name, record_type, data, ttl)
            
            return MockDNSRecord(name, record_type, data, ttl)
        
        return None  # Not found
    
    def get_query_count(self) -> int:
        return self._query_count

def generate_dns_queries() -> List[Tuple[str, int]]:
    """Generate a list of DNS queries for testing."""
    queries = []
    
    # Common domains with various record types
    domains = [
        'google.com', 'facebook.com', 'amazon.com', 'microsoft.com',
        'apple.com', 'twitter.com', 'linkedin.com', 'github.com',
        'stackoverflow.com', 'reddit.com', 'wikipedia.org', 'youtube.com',
        'netflix.com', 'instagram.com', 'whatsapp.com', 'zoom.us'
    ]
    
    # Add A record queries
    for domain in domains:
        queries.append((domain, A_RECORD))
        
        # Add some subdomain queries
        for subdomain in ['www', 'mail', 'api']:
            if random.random() < 0.3:  # 30% chance
                queries.append((f"{subdomain}.{domain}", A_RECORD))
    
    # Add other record types
    for domain in random.sample(domains, 8):
        queries.extend([
            (domain, MX_RECORD),
            (domain, TXT_RECORD),
            (domain, NS_RECORD)
        ])
    
    # Add some random subdomains
    subdomains = ['cdn', 'static', 'images', 'videos', 'blog', 'shop', 'secure']
    for _ in range(20):
        domain = random.choice(domains)
        subdomain = random.choice(subdomains)
        queries.append((f"{subdomain}.{domain}", A_RECORD))
    
    # Add some non-existent domains for NXDOMAIN testing
    for i in range(10):
        fake_domain = f"nonexistent{random.randint(1000, 9999)}.com"
        queries.append((fake_domain, A_RECORD))
    
    return queries

def perform_dns_resolution_batch(resolver: MockDNSResolver, queries: List[Tuple[str, int]]) -> Dict[str, Any]:
    """Perform a batch of DNS resolutions."""
    results = {
        'total_queries': len(queries),
        'successful_resolutions': 0,
        'failed_resolutions': 0,
        'cache_hits': 0,
        'response_times': [],
        'record_types_resolved': {},
        'domains_resolved': set()
    }
    
    cache_stats_before = resolver.cache.get_stats()
    
    for domain, record_type in queries:
        start_time = time.perf_counter()
        
        record = resolver.resolve(domain, record_type)
        
        end_time = time.perf_counter()
        response_time = end_time - start_time
        results['response_times'].append(response_time)
        
        if record:
            results['successful_resolutions'] += 1
            results['domains_resolved'].add(domain)
            
            # Count record types
            if record_type not in results['record_types_resolved']:
                results['record_types_resolved'][record_type] = 0
            results['record_types_resolved'][record_type] += 1
        else:
            results['failed_resolutions'] += 1
    
    cache_stats_after = resolver.cache.get_stats()
    results['cache_hits'] = cache_stats_after['hits'] - cache_stats_before['hits']
    results['domains_resolved'] = len(results['domains_resolved'])
    
    return results

def simulate_dns_server_queries(num_queries: int) -> Dict[str, Any]:
    """Simulate DNS server receiving and processing queries."""
    results = {
        'queries_processed': 0,
        'query_types': {},
        'response_codes': {'NOERROR': 0, 'NXDOMAIN': 0, 'SERVFAIL': 0},
        'processing_times': []
    }
    
    query_types = [A_RECORD, MX_RECORD, TXT_RECORD, NS_RECORD, AAAA_RECORD]
    
    for i in range(num_queries):
        # Simulate query processing
        start_time = time.perf_counter()
        
        query_type = random.choice(query_types)
        
        # Simulate different processing complexities
        if query_type == A_RECORD:
            # Simple A record lookup
            processing_delay = random.uniform(0.0001, 0.001)
        elif query_type == MX_RECORD:
            # MX record lookup (slightly more complex)
            processing_delay = random.uniform(0.001, 0.005)
        else:
            # Other record types
            processing_delay = random.uniform(0.0005, 0.003)
        
        time.sleep(processing_delay)
        
        # Determine response code
        response_probability = random.random()
        if response_probability < 0.85:
            response_code = 'NOERROR'
        elif response_probability < 0.95:
            response_code = 'NXDOMAIN'
        else:
            response_code = 'SERVFAIL'
        
        end_time = time.perf_counter()
        processing_time = end_time - start_time
        
        # Record statistics
        results['queries_processed'] += 1
        results['processing_times'].append(processing_time)
        results['response_codes'][response_code] += 1
        
        if query_type not in results['query_types']:
            results['query_types'][query_type] = 0
        results['query_types'][query_type] += 1
    
    return results

def test_dns_cache_performance(resolver: MockDNSResolver, cache_test_queries: int) -> Dict[str, Any]:
    """Test DNS cache performance with repeated queries."""
    results = {
        'total_queries': cache_test_queries,
        'unique_domains': 0,
        'cache_hit_rate': 0.0,
        'cache_stats': {}
    }
    
    # Generate a smaller set of domains for cache testing
    cache_domains = [
        'google.com', 'facebook.com', 'amazon.com', 'microsoft.com',
        'apple.com', 'twitter.com'
    ]
    
    # First pass - populate cache
    for domain in cache_domains:
        resolver.resolve(domain, A_RECORD)
        resolver.resolve(domain, MX_RECORD)
    
    # Second pass - test cache hits
    cache_stats_before = resolver.cache.get_stats()
    
    for _ in range(cache_test_queries):
        domain = random.choice(cache_domains)
        record_type = random.choice([A_RECORD, MX_RECORD, TXT_RECORD])
        resolver.resolve(domain, record_type)
    
    cache_stats_after = resolver.cache.get_stats()
    
    results['unique_domains'] = len(cache_domains)
    results['cache_stats'] = cache_stats_after
    
    total_cache_queries = cache_stats_after['hits'] - cache_stats_before['hits']
    if cache_test_queries > 0:
        results['cache_hit_rate'] = total_cache_queries / cache_test_queries
    
    return results

def run_twisted_names_benchmark(iterations: int) -> float:
    """Run the twisted names (DNS) benchmark."""
    # print(f"Running Twisted names (DNS) benchmark for {iterations} iterations...")
    
    # if not TWISTED_AVAILABLE:
        # print("Using mock DNS implementation (Twisted.names not installed)")
    
    
    resolver = MockDNSResolver()
    total_queries = 0
    total_resolutions = 0
    
    for i in range(iterations):
        start_time = time.time()
        
        if HAS_HWCOUNTER:
            cycle_start = count()

        # Generate DNS queries
        queries = generate_dns_queries()
        
        # Perform DNS resolutions
        resolution_results = perform_dns_resolution_batch(resolver, queries)
        total_queries += resolution_results['total_queries']
        total_resolutions += resolution_results['successful_resolutions']
        
        # Simulate DNS server processing
        if i % 3 == 0:
            server_results = simulate_dns_server_queries(random.randint(50, 150))
            total_queries += server_results['queries_processed']
        
        # Test cache performance
        if i % 5 == 0:
            cache_results = test_dns_cache_performance(resolver, random.randint(30, 80))
            total_queries += cache_results['total_queries']
        
        # Clean expired cache entries periodically
        if i % 10 == 0:
            resolver.cache.clear_expired()
        
        # if i % 5 == 0:
        #     cache_stats = resolver.cache.get_stats()
        #     print(f"Iteration {i}, queries: {total_queries}, resolutions: {total_resolutions}, cache hits: {cache_stats['hits']}", end='\r')
    
        # End CPU cycle counting
        if HAS_HWCOUNTER:
            cycle_end = count_end()
            cycles = cycle_end - cycle_start
        else:
            cycles = None
            
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"({execution_time}, {cycles})")
    
    # Final statistics
    # final_cache_stats = resolver.cache.get_stats()
    # total_resolver_queries = resolver.get_query_count()
    
    # print(f"\nCompleted {iterations} iterations in {execution_time:.4f} seconds")
    # print(f"Total DNS queries: {total_queries}")
    # print(f"Successful resolutions: {total_resolutions}")
    # print(f"Resolver queries: {total_resolver_queries}")
    # print(f"Cache hits: {final_cache_stats['hits']}")
    # print(f"Cache misses: {final_cache_stats['misses']}")
    # print(f"Cache hit rate: {final_cache_stats['hits']/(final_cache_stats['hits']+final_cache_stats['misses']):.2%}")
    # print(f"Queries per second: {total_queries/execution_time:.2f}")
    
    return execution_time

def main():
    parser = argparse.ArgumentParser(description="Twisted names (DNS) benchmark")
    parser.add_argument("-n", "--iterations", type=int, default=15,
                       help="Number of iterations to run (default: 15)")
    
    args = parser.parse_args()
    
    if args.iterations <= 0:
        print("Error: iterations must be positive")
        sys.exit(1)
    
    try:
        execution_time = run_twisted_names_benchmark(args.iterations)
        # print(f"Benchmark completed successfully in {execution_time:.4f} seconds")
        
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running benchmark: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
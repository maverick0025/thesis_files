#!/usr/bin/env python3
"""
Twisted iteration benchmark - tests deferred callbacks, reactor patterns, and async iteration.
Usage: python twisted_iteration.py -n <iterations>
"""

import time
import argparse
import sys
import random
from typing import List, Dict, Any, Callable, Optional

try:
    from twisted.internet import reactor, defer, task
    from twisted.internet.defer import Deferred, DeferredList, inlineCallbacks, returnValue
    from twisted.internet.task import LoopingCall
    TWISTED_AVAILABLE = True
except ImportError:
    print("Warning: Twisted not available. Installing fallback implementation.")
    TWISTED_AVAILABLE = False
try:
    from hwcounter import Timer as HWTimer, count, count_end
    HAS_HWCOUNTER = True
except ImportError:
    HAS_HWCOUNTER = False
    print("Warning: hwcounter not installed. CPU cycles will not be measured.")



# Fallback implementations for when Twisted is not available
class MockDeferred:
    """Mock Deferred for testing without Twisted."""
    def __init__(self, result=None):
        self._result = result
        self._callbacks = []
        self._errbacks = []
        self._called = False
    
    def addCallback(self, callback):
        if self._called:
            try:
                self._result = callback(self._result)
            except Exception as e:
                self._result = e
        else:
            self._callbacks.append(callback)
        return self
    
    def addErrback(self, errback):
        self._errbacks.append(errback)
        return self
    
    def callback(self, result):
        if self._called:
            return
        self._called = True
        self._result = result
        
        for cb in self._callbacks:
            try:
                self._result = cb(self._result)
            except Exception as e:
                for eb in self._errbacks:
                    try:
                        self._result = eb(e)
                        break
                    except:
                        continue
                break
    
    def errback(self, error):
        if self._called:
            return
        self._called = True
        for eb in self._errbacks:
            try:
                self._result = eb(error)
                return
            except:
                continue
        self._result = error

class MockReactor:
    """Mock reactor for testing without Twisted."""
    def __init__(self):
        self._delayed_calls = []
        self._running = False
    
    def callLater(self, delay, callback, *args, **kwargs):
        call_time = time.time() + delay
        self._delayed_calls.append((call_time, callback, args, kwargs))
        return len(self._delayed_calls) - 1
    
    def run_pending(self):
        """Process pending delayed calls."""
        current_time = time.time()
        executed = []
        
        for i, (call_time, callback, args, kwargs) in enumerate(self._delayed_calls):
            if call_time <= current_time:
                try:
                    callback(*args, **kwargs)
                except:
                    pass
                executed.append(i)
        
        # Remove executed calls
        for i in reversed(executed):
            del self._delayed_calls[i]
    
    def stop(self):
        self._running = False

# Use appropriate implementations
if TWISTED_AVAILABLE:
    Deferred = defer.Deferred
    DeferredList = defer.DeferredList
    mock_reactor = reactor
else:
    Deferred = MockDeferred
    mock_reactor = MockReactor()
    
    def DeferredList(deferreds):
        """Mock DeferredList implementation."""
        results = []
        for d in deferreds:
            if hasattr(d, '_result'):
                results.append((True, d._result))
            else:
                results.append((False, None))
        return MockDeferred(results)

def create_simple_deferred(value: Any, delay: float = 0.0) -> Deferred:
    """Create a deferred that fires with a value."""
    d = Deferred()
    
    def fire_deferred():
        if not d.called if TWISTED_AVAILABLE else not d._called:
            d.callback(value)
    
    if delay > 0:
        mock_reactor.callLater(delay, fire_deferred)
    else:
        fire_deferred()
    
    return d

def create_chained_deferreds(count: int, base_value: int = 0) -> Deferred:
    """Create a chain of deferreds for callback testing."""
    def add_one(result):
        return result + 1
    
    def multiply_two(result):
        return result * 2
    
    def subtract_ten(result):
        return result - 10
    
    callbacks = [add_one, multiply_two, subtract_ten] * (count // 3 + 1)
    
    d = create_simple_deferred(base_value)
    
    for i in range(min(count, len(callbacks))):
        d.addCallback(callbacks[i])
    
    return d

def create_error_handling_deferred(should_error: bool = False) -> Deferred:
    """Create a deferred that may error for testing error handling."""
    d = Deferred()
    
    def fire_deferred():
        if should_error:
            d.errback(Exception(f"Test error {random.randint(1, 1000)}"))
        else:
            d.callback(f"Success {random.randint(1, 1000)}")
    
    delay = random.uniform(0.001, 0.01)
    mock_reactor.callLater(delay, fire_deferred)
    
    return d

def process_deferred_list(deferreds: List[Deferred]) -> Deferred:
    """Process a list of deferreds and return combined results."""
    dl = DeferredList(deferreds)
    
    def process_results(results):
        successful = []
        failed = []
        
        if TWISTED_AVAILABLE:
            for success, result in results:
                if success:
                    successful.append(result)
                else:
                    failed.append(result)
        else:
            # Mock implementation
            for success, result in results:
                if success:
                    successful.append(result)
                else:
                    failed.append(result)
        
        return {
            'successful': successful,
            'failed': failed,
            'total': len(results),
            'success_rate': len(successful) / len(results) if results else 0
        }
    
    dl.addCallback(process_results)
    return dl

def create_nested_deferred_structure(depth: int, breadth: int) -> Deferred:
    """Create nested deferred structures for complex async patterns."""
    def create_level(current_depth):
        if current_depth <= 0:
            return create_simple_deferred(f"leaf_{random.randint(1, 1000)}")
        
        children = []
        for i in range(breadth):
            child = create_level(current_depth - 1)
            children.append(child)
        
        dl = DeferredList(children)
        
        def combine_children(results):
            combined = []
            if TWISTED_AVAILABLE:
                for success, result in results:
                    if success:
                        if isinstance(result, list):
                            combined.extend(result)
                        else:
                            combined.append(result)
            else:
                # Mock processing
                for success, result in results:
                    if success:
                        combined.append(result)
            return combined
        
        dl.addCallback(combine_children)
        return dl
    
    return create_level(depth)

def simulate_async_computation(computation_id: int, complexity: int = 100) -> Deferred:
    """Simulate async computation with callbacks."""
    d = Deferred()
    
    def perform_computation():
        # Simulate some work
        result = 0
        for i in range(complexity):
            result += i * computation_id
            if i % 10 == 0:
                result = result % 1000000  # Keep numbers manageable
        
        # Add some string processing
        result_str = f"computation_{computation_id}_result_{result}"
        processed = result_str.upper().replace('_', '-')
        
        d.callback({
            'id': computation_id,
            'result': result,
            'processed': processed,
            'complexity': complexity
        })
    
    # Simulate async delay
    delay = random.uniform(0.001, 0.005)
    mock_reactor.callLater(delay, perform_computation)
    
    return d

def run_callback_chain_test(chain_length: int, num_chains: int) -> Dict[str, Any]:
    """Test callback chains of various lengths."""
    results = {
        'chains_processed': 0,
        'total_callbacks': 0,
        'successful_chains': 0,
        'callback_results': []
    }
    
    deferreds = []
    
    for chain_id in range(num_chains):
        d = create_chained_deferreds(chain_length, chain_id)
        
        def record_result(result, chain_id=chain_id):
            results['callback_results'].append({
                'chain_id': chain_id,
                'final_result': result,
                'chain_length': chain_length
            })
            results['successful_chains'] += 1
            return result
        
        def record_error(error, chain_id=chain_id):
            results['callback_results'].append({
                'chain_id': chain_id,
                'error': str(error),
                'chain_length': chain_length
            })
            return error
        
        d.addCallback(record_result)
        d.addErrback(record_error)
        deferreds.append(d)
    
    # Process all deferreds
    dl = process_deferred_list(deferreds)
    
    def finalize_results(summary):
        results['chains_processed'] = num_chains
        results['total_callbacks'] = chain_length * num_chains
        return results
    
    dl.addCallback(finalize_results)
    
    # If using mock reactor, process pending calls
    if not TWISTED_AVAILABLE:
        for _ in range(100):  # Process multiple times to handle delays
            mock_reactor.run_pending()
            time.sleep(0.001)
    
    return results

def run_error_handling_test(num_deferreds: int, error_rate: float = 0.3) -> Dict[str, Any]:
    """Test error handling in deferred chains."""
    results = {
        'total_deferreds': num_deferreds,
        'expected_errors': int(num_deferreds * error_rate),
        'actual_errors': 0,
        'recovered_errors': 0,
        'final_successes': 0
    }
    
    deferreds = []
    
    for i in range(num_deferreds):
        should_error = random.random() < error_rate
        d = create_error_handling_deferred(should_error)
        
        def handle_error(error):
            results['actual_errors'] += 1
            # Try to recover from error
            recovery_result = f"recovered_from_{str(error)[:20]}"
            results['recovered_errors'] += 1
            return recovery_result
        
        def handle_success(result):
            results['final_successes'] += 1
            return result
        
        d.addErrback(handle_error)
        d.addCallback(handle_success)
        deferreds.append(d)
    
    # Process all deferreds
    dl = process_deferred_list(deferreds)
    
    # Process pending calls for mock reactor
    if not TWISTED_AVAILABLE:
        for _ in range(100):
            mock_reactor.run_pending()
            time.sleep(0.001)
    
    return results

def run_nested_deferred_test(depth: int, breadth: int) -> Dict[str, Any]:
    """Test nested deferred structures."""
    results = {
        'depth': depth,
        'breadth': breadth,
        'expected_leaves': breadth ** depth,
        'actual_results': 0
    }
    
    nested_d = create_nested_deferred_structure(depth, breadth)
    
    def count_results(final_results):
        if isinstance(final_results, list):
            results['actual_results'] = len(final_results)
        else:
            results['actual_results'] = 1
        return results
    
    nested_d.addCallback(count_results)
    
    # Process pending calls
    if not TWISTED_AVAILABLE:
        for _ in range(200):  # More iterations for nested processing
            mock_reactor.run_pending()
            time.sleep(0.001)
    
    return results

def run_twisted_iteration_benchmark(iterations: int) -> float:
    """Run the twisted iteration benchmark."""
    # print(f"Running Twisted iteration benchmark for {iterations} iterations...")
    
    if not TWISTED_AVAILABLE:
        print("Using mock implementation (Twisted not installed)")
    
    
    total_deferreds = 0
    total_callbacks = 0
    
    for i in range(iterations):
        start_time = time.time()

        if HAS_HWCOUNTER:
            cycle_start = count()
            
        # Test 1: Simple callback chains
        chain_results = run_callback_chain_test(
            chain_length=random.randint(5, 15),
            num_chains=random.randint(10, 30)
        )
        total_deferreds += chain_results['chains_processed']
        total_callbacks += chain_results['total_callbacks']
        
        # Test 2: Error handling
        if i % 3 == 0:
            error_results = run_error_handling_test(
                num_deferreds=random.randint(20, 50),
                error_rate=0.2
            )
            total_deferreds += error_results['total_deferreds']
        
        # Test 3: Nested structures
        if i % 5 == 0:
            nested_results = run_nested_deferred_test(
                depth=random.randint(2, 4),
                breadth=random.randint(2, 4)
            )
        
        # Test 4: Async computations
        computation_deferreds = []
        for comp_id in range(20):
            comp_d = simulate_async_computation(
                comp_id, 
                complexity=random.randint(50, 200)
            )
            computation_deferreds.append(comp_d)
        
        comp_list = process_deferred_list(computation_deferreds)
        total_deferreds += len(computation_deferreds)
        
        # Process pending calls for mock reactor
        if not TWISTED_AVAILABLE:
            for _ in range(50):
                mock_reactor.run_pending()
                time.sleep(0.0001)
            
        if HAS_HWCOUNTER:
            cycle_end = count_end()
            cycles = cycle_end - cycle_start
        else:
            cycles = None
                
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"({execution_time}, {cycles})")

    # print(f"\nCompleted {iterations} iterations in {execution_time:.4f} seconds")
    # print(f"Total deferreds processed: {total_deferreds}")
    # print(f"Total callbacks executed: {total_callbacks}")
    # print(f"Average deferreds per second: {total_deferreds/execution_time:.2f}")
    
    return execution_time

def main():
    parser = argparse.ArgumentParser(description="Twisted iteration benchmark")
    parser.add_argument("-n", "--iterations", type=int, default=20,
                       help="Number of iterations to run (default: 20)")
    
    args = parser.parse_args()
    
    if args.iterations <= 0:
        print("Error: iterations must be positive")
        sys.exit(1)
    
    try:
        execution_time = run_twisted_iteration_benchmark(args.iterations)
        # print(f"Benchmark completed successfully in {execution_time:.4f} seconds")
        
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running benchmark: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
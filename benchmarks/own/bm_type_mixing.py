# type_mixing_benchmark.py
import sys

def mixed_arithmetic(iterations):
    """Forces type guard failures by mixing int and float operations"""
    result = 0
    for i in range(iterations):
        if i % 3 == 0:
            # This will cause type guard exits when JIT expects int but gets float
            x = i * 3.14159  # float
        else:
            x = i * 2        # int
        
        # This addition will cause type mismatches and side exits
        result += x
    return result

def mixed_containers(iterations):
    """Forces container type guard failures"""
    containers = [[], {}, (), "hello", 42]
    result = 0
    
    for i in range(iterations):
        container = containers[i % len(containers)]
        try:
            # This will cause type guard failures as JIT expects consistent types
            if hasattr(container, '__len__'):
                result += len(container)
            else:
                result += container
        except:
            result += 1
    return result

if __name__ == "__main__":
    print("Running type mixing benchmark...")
    # Run enough iterations to trigger JIT compilation
    for _ in range(5):
        mixed_arithmetic(10000)  # Warm up, let JIT compile
    
    # This should now trigger many side exits
    result1 = mixed_arithmetic(50000)
    result2 = mixed_containers(20000)
    
    print(f"Results: {result1}, {result2}")

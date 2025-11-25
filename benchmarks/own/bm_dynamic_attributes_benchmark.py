# dynamic_attributes_benchmark.py
class DynamicClass:
    def __init__(self):
        self.value = 0

def dynamic_attribute_access(iterations):
    """Forces attribute guard failures by dynamically modifying objects"""
    obj = DynamicClass()
    result = 0
    
    for i in range(iterations):
        # Dynamically add/remove attributes to break JIT assumptions
        if i % 100 == 0:
            if hasattr(obj, 'dynamic_attr'):
                delattr(obj, 'dynamic_attr')
            else:
                obj.dynamic_attr = i
        
        # This will cause side exits as object layout keeps changing
        try:
            result += obj.value
            if hasattr(obj, 'dynamic_attr'):
                result += obj.dynamic_attr
        except AttributeError:
            result += 1
    
    return result

def function_version_failures(iterations):
    """Forces function version guard failures by modifying functions"""
    def target_function(x):
        return x * 2
    
    result = 0
    for i in range(iterations):
        # Modify function properties to invalidate JIT assumptions
        if i % 1000 == 0:
            target_function.__name__ = f"func_{i}"
        
        result += target_function(i)
    
    return result

if __name__ == "__main__":
    print("Running dynamic attributes benchmark...")
    # Warm up
    for _ in range(3):
        dynamic_attribute_access(5000)
        function_version_failures(5000)
    
    # Main run that should trigger exits
    result1 = dynamic_attribute_access(30000)
    result2 = function_version_failures(25000)
    
    print(f"Results: {result1}, {result2}")

"""
Memory monitoring utilities for the weather mapping application
"""
import psutil
import os
import gc

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def print_memory_usage(label=""):
    """Print current memory usage with optional label"""
    memory_mb = get_memory_usage()
    print(f"Memory usage {label}: {memory_mb:.1f} MB")
    return memory_mb

def force_garbage_collection():
    """Force garbage collection and return freed memory"""
    before = get_memory_usage()
    gc.collect()
    after = get_memory_usage()
    freed = before - after
    if freed > 0:
        print(f"Freed {freed:.1f} MB through garbage collection")
    return freed

def memory_optimized_processing(func):
    """Decorator to add memory monitoring and cleanup to functions"""
    def wrapper(*args, **kwargs):
        print_memory_usage("before processing")
        result = func(*args, **kwargs)
        force_garbage_collection()
        print_memory_usage("after processing")
        return result
    return wrapper
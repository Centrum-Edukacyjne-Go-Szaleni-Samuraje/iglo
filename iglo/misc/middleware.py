import time
import logging
import re
import cProfile
import pstats
import io
import os
import sys
import inspect
import types
from functools import wraps, partial
from collections import defaultdict
from django.db import connection, reset_queries
from django.conf import settings
from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)

def profile_func(func=None, name=None):
    """
    Decorator for profiling a function and logging the results.
    Can be used as @profile_func or @profile_func(name="custom_name")
    """
    if func is None:
        return partial(profile_func, name=name)
        
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Track detailed timing
        start_time = time.time()
        
        # Profile CPU usage
        profiler = cProfile.Profile()
        profiling_enabled = False
        
        try:
            try:
                profiler.enable()
                profiling_enabled = True
            except ValueError as e:
                # Another profiling tool is already active
                func_name = name or f"{func.__module__}.{func.__qualname__}"
                logger.warning(f"Skipping profiling for {func_name}: {str(e)}")
            
            result = func(*args, **kwargs)
            
            # Calculate elapsed time
            elapsed = time.time() - start_time
            
            # Get function name info
            func_name = name or f"{func.__module__}.{func.__qualname__}"
            
            # Log elapsed time for all functions
            logger.warning(f"=== TIMING of {func_name} ===")
            logger.warning(f"Total execution time: {elapsed:.4f}s")
            
            # Get detailed stats only if profiling was enabled
            if profiling_enabled:
                try:
                    profiler.disable()
                    
                    # Get detailed stats
                    s = io.StringIO()
                    sortby = 'cumulative'
                    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
                    ps.print_stats(30)  # Print top 30 functions
                    
                    # Log stats with detailed header
                    logger.warning(f"Top functions by cumulative time:\n{s.getvalue()}")
                except Exception as e:
                    logger.warning(f"Error in profiling stats for {func_name}: {str(e)}")
        except Exception as e:
            # Still log the error but allow the function to execute
            func_name = name or f"{func.__module__}.{func.__qualname__}"
            logger.exception(f"Error during profiled function {func_name}: {str(e)}")
            raise
        
        return result
    return wrapper

def time_func(func=None, name=None):
    """
    Simple timing decorator - much less overhead than full profiling
    """
    if func is None:
        return partial(time_func, name=name)
        
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        func_name = name or f"{func.__module__}.{func.__qualname__}"
        logger.warning(f"TIME: {func_name} took {elapsed:.4f}s")
        return result
    return wrapper

def add_profiling(cls, method_names, timing_only=False):
    """
    Add profiling to methods of a class by name
    """
    decorator = time_func if timing_only else profile_func
    
    for method_name in method_names:
        if hasattr(cls, method_name):
            original_method = getattr(cls, method_name)
            if isinstance(original_method, property):
                # Handle properties differently
                setattr(cls, method_name, property(
                    decorator(original_method.fget),
                    original_method.fset if original_method.fset else None,
                    original_method.fdel if original_method.fdel else None,
                    original_method.__doc__
                ))
            else:
                # Regular methods
                setattr(cls, method_name, decorator(original_method))
    
    return cls

class ProfilingMiddleware:
    """
    Middleware to profile Django page rendering, database queries, and CPU usage.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only run profiling if explicitly enabled via environment variable
        if not getattr(settings, 'ENABLE_PROFILING', False):
            return self.get_response(request)
            
        # Reset queries to ensure we only capture this request
        reset_queries()
        
        # Only profile certain paths to avoid noise
        should_profile_cpu = False
        for path_pattern in ['/seasons/', '/groups/']:
            if path_pattern in request.path:
                should_profile_cpu = True
                break
        
        # Code to be executed for each request before the view is called
        start_time = time.time()
        
        # Process the request with optional CPU profiling
        if should_profile_cpu and duration_above_threshold(request):
            profiler = cProfile.Profile()
            profiling_enabled = False
            
            try:
                try:
                    profiler.enable()
                    profiling_enabled = True
                except ValueError as e:
                    # Another profiling tool is already active
                    logger.warning(f"Skipping profiling for {request.path}: {str(e)}")
                
                response = self.get_response(request)
                
                if profiling_enabled:
                    try:
                        profiler.disable()
                        
                        # Get stats
                        s = io.StringIO()
                        sortby = 'cumulative'
                        ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
                        ps.print_stats(30)  # Print top 30 functions
                        
                        # Log CPU profiling stats for slow requests
                        logger.warning(f"CPU Profile for {request.path}:\n{s.getvalue()}")
                    except Exception as e:
                        logger.warning(f"Error in profiling stats for {request.path}: {str(e)}")
            except Exception as e:
                logger.exception(f"Error during profiled request handling: {str(e)}")
                # Ensure we still handle the request even if profiling fails
                profiling_enabled = False
                response = self.get_response(request)
        else:
            response = self.get_response(request)
        
        # Code to be executed for each request/response after the view is called
        end_time = time.time()
        duration = end_time - start_time
        
        # Update duration history for this path
        update_request_duration(request, duration)
        
        # Get query statistics
        query_count = len(connection.queries)
        
        # Use a higher threshold for long paths to avoid noise
        duration_threshold = 1.0  # Default threshold in seconds
        query_threshold = 50     # Default query threshold
        
        # Only log if it's slow or has too many queries
        if duration > duration_threshold or query_count > query_threshold:
            # Calculate total query time
            total_query_time = sum(float(q.get('time', 0)) for q in connection.queries)
            
            # Group similar queries
            pattern_to_stats = defaultdict(lambda: {'count': 0, 'time': 0.0, 'examples': []})
            
            for query in connection.queries:
                # Simplify the query to create a pattern
                # Remove specific values and keep the structure
                sql = query.get('sql', '')
                
                # Replace specific values in WHERE clauses with placeholders
                simplified = re.sub(r'\'[^\']*\'', "'?'", sql)  # Replace string literals
                simplified = re.sub(r'\d+', "?", simplified)    # Replace numbers
                
                # Track statistics for this pattern
                pattern_to_stats[simplified]['count'] += 1
                pattern_to_stats[simplified]['time'] += float(query.get('time', 0))
                
                # Keep one example of each query pattern
                if len(pattern_to_stats[simplified]['examples']) < 1:
                    pattern_to_stats[simplified]['examples'].append(sql)
            
            # Sort patterns by total time spent
            sorted_patterns = sorted(
                pattern_to_stats.items(), 
                key=lambda x: x[1]['time'], 
                reverse=True
            )
            
            # Log summary
            logger.warning(
                f"Path: {request.path} - "
                f"Total Time: {duration:.2f}s - "
                f"DB Time: {total_query_time:.2f}s ({(total_query_time/duration)*100:.1f}%) - "
                f"Python Time: {duration - total_query_time:.2f}s ({((duration - total_query_time)/duration)*100:.1f}%) - "
                f"Queries: {query_count}"
            )
            
            # Log top query patterns
            logger.warning("Top query patterns:")
            for i, (pattern, stats) in enumerate(sorted_patterns[:10]):
                logger.warning(
                    f"  Pattern #{i+1}: {stats['count']} queries, {stats['time']:.4f}s total, "
                    f"{stats['time']/stats['count']:.4f}s avg"
                )
                logger.warning(f"  Example: {stats['examples'][0][:300]}...")
            
            # Log duplicated queries (potential N+1 problems)
            if any(stats['count'] > 5 for pattern, stats in sorted_patterns):
                logger.warning("Potential N+1 query patterns:")
                for pattern, stats in sorted_patterns:
                    if stats['count'] > 5:
                        logger.warning(
                            f"  Query executed {stats['count']} times, {stats['time']:.4f}s total: "
                            f"{pattern[:100]}..."
                        )
            
            # Memory profiling
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                logger.warning(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
            except ImportError:
                pass
                
        return response

# Utility to check if a previous request to the same path was slow
_request_durations = {}

def duration_above_threshold(request, threshold=1.0):
    """Check if a previous request to the same path was slow"""
    global _request_durations
    path = request.path
    if path in _request_durations and _request_durations[path] > threshold:
        return True
    return False

def update_request_duration(request, duration):
    """Update the duration for this path"""
    global _request_durations
    _request_durations[request.path] = duration
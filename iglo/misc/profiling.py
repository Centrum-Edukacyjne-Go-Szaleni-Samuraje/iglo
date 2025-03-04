"""
Automatic profiling for key methods in the IGLO application.
This module adds profiling to key methods that might be performance bottlenecks.
"""

import logging
from functools import wraps
import time
import io
import cProfile
import pstats
from django.utils.functional import cached_property

from misc.middleware import add_profiling, profile_func, time_func

logger = logging.getLogger(__name__)

def profile_cached_property(func):
    """
    Special profiling decorator for cached_property
    """
    @wraps(func)
    def profiled_func(self, *args, **kwargs):
        start = time.time()
        result = func(self, *args, **kwargs)
        elapsed = time.time() - start
        logger.warning(f"CACHED_PROPERTY: {func.__qualname__} took {elapsed:.4f}s")
        return result
    
    return cached_property(profiled_func)

def detailed_profiling_decorator(func):
    """
    A more detailed decorator that profiles a function and logs entry/exit and performance.
    Useful for complicated methods where we need to know exactly which part is slow.
    """
    import traceback
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__qualname__}"
        start = time.time()
        
        # Log entry with call info
        call_args = []
        if args and len(args) > 0:
            call_args.append(f"{len(args)} args")
        if kwargs:
            call_args.append(f"{len(kwargs)} kwargs")
            
        args_str = ", ".join(call_args)
        logger.warning(f"ENTRY: {func_name}({args_str}) - call stack depth: {len(traceback.extract_stack())}")
        
        # Profile the function execution
        profiler = cProfile.Profile()
        profiling_enabled = False
        
        try:
            try:
                profiler.enable()
                profiling_enabled = True
            except ValueError as e:
                # Another profiling tool is already active, skip profiling
                logger.warning(f"Skipping profiling for {func_name}: {str(e)}")
            
            result = func(*args, **kwargs)
            
            # Get the size of the result (approximation)
            result_size = "unknown"
            try:
                if isinstance(result, (list, tuple, set, dict)):
                    result_size = f"{len(result)} items"
                elif hasattr(result, '__len__'):
                    result_size = f"{len(result)} length"
            except:
                pass
            
            status = f"returned {type(result).__name__}({result_size})"
        except Exception as e:
            status = f"ERROR: {type(e).__name__}: {str(e)}"
            raise
        finally:
            elapsed = time.time() - start
            
            # Only disable profiling if it was successfully enabled
            if profiling_enabled:
                try:
                    profiler.disable()
                    
                    # Get profiling stats
                    s = io.StringIO()
                    sortby = 'cumulative'
                    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
                    ps.print_stats(30)
                    
                    # Log profile data
                    logger.warning(f"PROFILE: {func_name}:\n{s.getvalue()}")
                except Exception as e:
                    logger.warning(f"Error in profiling for {func_name}: {str(e)}")
            
            # Always log exit with timing and status
            logger.warning(f"EXIT: {func_name} - {status} - elapsed: {elapsed:.4f}s")
        
        return result
    return wrapper

def apply_profiling():
    """
    Apply profiling to key methods in the application that might be bottlenecks.
    This should be called during Django startup.
    """
    try:
        # Import models after Django is fully loaded
        from league.models import Group, Member, Game
        from league.models import GameManager
        
        # Get detailed profiling on the key methods causing the bottleneck
        # Causes most of the queries
        setattr(GameManager, 'get_for_member', detailed_profiling_decorator(GameManager.get_for_member))
            
        # Skip profiling results_table since it's a cached_property without __wrapped__ attribute
        # This avoids the error: 'cached_property' object has no attribute '__wrapped__'
                
        # Profile get_absolute_url which is called for every game
        if hasattr(Game, 'get_absolute_url'):
            original_method = Game.get_absolute_url
            setattr(Game, 'get_absolute_url', detailed_profiling_decorator(original_method))
                
        # Skip profiling members_qualification as it's also a cached_property
        # This would cause the same error: 'cached_property' object has no attribute '__wrapped__'
        
        # Add timing profiling to various methods
        methods_to_time = [
            (Member, ['points', 'score', 'sodos', 'sos', 'sosos', 'result']),
            (Game, ['get_opponent', 'get_absolute_url', 'is_played', 'is_bye']),
        ]
        
        for cls, methods in methods_to_time:
            for method_name in methods:
                if hasattr(cls, method_name):
                    original_method = getattr(cls, method_name)
                    
                    if isinstance(original_method, property):
                        # Handle regular property
                        @wraps(original_method.fget)
                        def timed_property(self, original=original_method.fget):
                            start = time.time()
                            result = original(self)
                            elapsed = time.time() - start
                            logger.warning(f"PROPERTY: {original.__qualname__} took {elapsed:.4f}s")
                            return result
                        
                        setattr(cls, method_name, property(timed_property))
                    
                    elif isinstance(original_method, cached_property):
                        # Skip profiling cached_property to avoid 'cached_property' object has no attribute '__wrapped__' error
                        pass
                    
                    elif callable(original_method):
                        # Handle regular methods
                        @wraps(original_method)
                        def timed_method(self, *args, original=original_method, **kwargs):
                            start = time.time()
                            result = original(self, *args, **kwargs)
                            elapsed = time.time() - start
                            logger.warning(f"METHOD: {original.__qualname__} took {elapsed:.4f}s")
                            return result
                        
                        setattr(cls, method_name, timed_method)
        
        logger.info("Performance profiling applied to IGLO models")
        
    except Exception as e:
        logger.exception(f"Failed to apply profiling: {e}")
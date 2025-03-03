"""
Automatic profiling for key methods in the IGLO application.
This module adds profiling to key methods that might be performance bottlenecks.
"""

import logging
from functools import wraps
import time
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

def apply_profiling():
    """
    Apply profiling to key methods in the application that might be bottlenecks.
    This should be called during Django startup.
    """
    try:
        # Import models after Django is fully loaded
        from league.models import Group, Member, Game
        
        # Profile key Group methods - add more as needed
        for method_name in ['results_table']:
            if hasattr(Group, method_name):
                original_method = getattr(Group, method_name)
                if isinstance(original_method, cached_property):
                    # Handle cached_property
                    profiled = profile_cached_property(original_method.__wrapped__)
                    setattr(Group, method_name, profiled)
        
        # Profile members_qualification
        for method_name in ['members_qualification']:
            if hasattr(Group, method_name):
                original_method = getattr(Group, method_name)
                if isinstance(original_method, cached_property):
                    # Handle cached_property
                    profiled = profile_cached_property(original_method.__wrapped__)
                    setattr(Group, method_name, profiled)
        
        # Add timing profiling to various methods
        methods_to_time = [
            (Member, ['points', 'score', 'sodos', 'sos', 'sosos', 'result']),
            (Game, ['get_opponent', 'get_absolute_url', 'is_played', 'is_bye']),
            (Game.objects, ['get_for_member'])
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
                        # Handle cached_property
                        setattr(cls, method_name, profile_cached_property(original_method.__wrapped__))
                    
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
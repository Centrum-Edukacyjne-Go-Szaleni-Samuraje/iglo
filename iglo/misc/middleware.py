import time
import logging
import re
from collections import defaultdict
from django.db import connection, reset_queries
from django.conf import settings

logger = logging.getLogger(__name__)

class ProfilingMiddleware:
    """
    Middleware to profile Django page rendering and database queries.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEBUG:
            return self.get_response(request)
            
        # Reset queries to ensure we only capture this request
        reset_queries()
        
        # Code to be executed for each request before the view is called
        start_time = time.time()
        
        # Process the request
        response = self.get_response(request)
        
        # Code to be executed for each request/response after the view is called
        end_time = time.time()
        duration = end_time - start_time
        
        # Get query statistics
        query_count = len(connection.queries)
        
        # Use a higher threshold for long paths to avoid noise
        duration_threshold = 0.5  # Default threshold in seconds
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
                
        return response
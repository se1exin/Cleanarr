import os
import time
from functools import wraps
from logger import get_logger

logger = get_logger(__name__)
traces = []


def trace_time(method):
    @wraps(method)
    def timed(*args, **kw):
        if os.getenv("DEBUG") != "1":
            return method(*args, **kw)
        start_time = time.perf_counter()
        result = method(*args, **kw)
        end_time = time.perf_counter()
        duration = end_time - start_time
        traces.append((method.__name__, duration))
        logger.debug(f"{method.__name__} took {duration} seconds")
        return result
    return timed

def print_top_traces(n):
    # Sort the traces by the execution time and print the top N
    top_traces = sorted(traces, key=lambda record: record[1], reverse=True)[:n]
    print("==================================================================")
    for method, time_taken in top_traces:
        print(f"{method} took {time_taken} seconds")
    print("==================================================================")

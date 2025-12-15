import time
import streamlit as st
from functools import wraps

class APIRateLimiter:
    def __init__(self, calls_per_minute=15):
        self.calls_per_minute = calls_per_minute
        self.call_times = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        # Remove calls older than 1 minute
        self.call_times = [t for t in self.call_times if now - t < 60]
        
        if len(self.call_times) >= self.calls_per_minute:
            sleep_time = 60 - (now - self.call_times[0])
            if sleep_time > 0:
                st.warning(f"⏳ Rate limit protection: waiting {sleep_time:.1f}s...")
                time.sleep(sleep_time)
        
        self.call_times.append(time.time())

# Global rate limiter
rate_limiter = APIRateLimiter(calls_per_minute=10)

def with_rate_limit(func):
    """Decorator to add rate limiting to API calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        rate_limiter.wait_if_needed()
        return func(*args, **kwargs)
    return wrapper
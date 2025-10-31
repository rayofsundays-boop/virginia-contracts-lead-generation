import os

bind = f"0.0.0.0:{os.environ.get('PORT', 8080)}"
workers = 2
timeout = 120  # Increased from 30 to 120 seconds for database initialization
keepalive = 2
max_requests = 100
max_requests_jitter = 10
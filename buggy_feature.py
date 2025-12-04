# buggy_feature.py - Add rate limiting to filter service

import time

# Bug 1: Hardcoded credentials
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"

# Bug 2: Mutable default argument
def process_events(events=[]):
    for event in events:
        events.append(event['id'])  # Bug 3: Modifying list while iterating
    return events

# Bug 4: No exception handling, potential division by zero
def calculate_rate(requests, seconds):
    return requests / seconds

# Bug 5: SQL injection vulnerability
def get_user_filter(subscriber_id):
    query = f"SELECT * FROM filters WHERE subscriber_id = '{subscriber_id}'"
    return query

# Bug 6: Resource leak - file never closed
def log_event(event):
    f = open('events.log', 'a')
    f.write(str(event))

# Bug 7: Race condition with global state
request_count = 0

def increment_counter():
    global request_count
    temp = request_count
    time.sleep(0.001)
    request_count = temp + 1
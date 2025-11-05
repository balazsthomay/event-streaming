from fastapi import FastAPI, Response
from kafka import KafkaConsumer
from kafka.admin import KafkaAdminClient
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
import redis
import json
import threading
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("filter-service")


# Metrics
events_read_from_kafka = Counter('events_read_from_kafka', 'Total events consumed from Kafka topic user-events')
events_matched_filters = Counter('events_matched_filters', 'Total events that matched at least one filter')
events_routed_to_redis = Counter('events_routed_to_redis', 'Total events successfully written to Redis Streams')
redis_write_failures = Counter('redis_write_failures', 'Total failed writes to Redis Streams')
active_streams_count = Gauge('active_streams_count', 'Current number of active subscriber streams')


app = FastAPI()
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)


active_streams = {}  # {subscriber_id: filter_criteria}


@app.post("/activate-stream")
def activate_stream(data: dict):
    subscriber_id = data['subscriber_id']
    
    # Fetch filter criteria from Subscriber Management API - - ONLY WHEN THE USER CONNECTS, so the events while disconnected are lost
    try:
        response = requests.get(f"http://localhost:8001/filters/{subscriber_id}")
        if response.status_code == 200:
            criteria = response.json()
        else:
            logger.error(f"Failed to fetch filters for {subscriber_id}: status_code={response.status_code}")
            return {"status": "error", "message": "Filter not found"}
    except Exception as e:
        logger.error(f"Error fetching filters for {subscriber_id}: {e}")
        return {"status": "error", "message": str(e)}

    # Store in memory
    active_streams[subscriber_id] = criteria
    active_streams_count.set(len(active_streams))  # Set AFTER modifying dict
    
    return {"status": "activated", "subscriber_id": subscriber_id}

@app.delete("/deactivate-stream/{subscriber_id}")
def deactivate_stream(subscriber_id: str):
    if subscriber_id in active_streams:
        del active_streams[subscriber_id]
        active_streams_count.set(len(active_streams))
    return {"status": "deactivated"}

@app.get("/health")
def health_check():
    kafka_ok = check_kafka()
    redis_ok = check_redis()
    postgres_ok = check_postgres()
    
    all_healthy = kafka_ok and redis_ok and postgres_ok
    
    status_code = 200 if all_healthy else 503
    
    return Response(
        content=json.dumps({
            "status": "healthy" if all_healthy else "unhealthy",
            "dependencies": {
                "kafka": "up" if kafka_ok else "down",
                "redis": "up" if redis_ok else "down",
                "subscriber_management": "up" if postgres_ok else "down"
            }
        }),
        status_code=status_code,
        media_type="application/json"
    )
    
@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def check_kafka():
    try:
        admin = KafkaAdminClient(bootstrap_servers=['localhost:9092'])
        admin.close()
        return True
    except Exception:
        return False
    
def check_redis():
    try:
        redis_client.ping()
        return True
    except Exception:
        return False
    
def check_postgres():
    try:
        response = requests.get(f"http://localhost:8001/health")
        return response.status_code == 200
    except Exception:
        return False

def kafka_consumer_loop():
    consumer = KafkaConsumer(
        'user-events',
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='latest',
        group_id='filter-service',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    for message in consumer:
        event = message.value
        events_read_from_kafka.inc()  # Count every event we read, once
        
        # Check against all active streams
        for subscriber_id, criteria in active_streams.items():
            if matches_criteria(event, criteria):
                events_matched_filters.inc()  # Count match before we try Redis
                clean_event = {k: v for k, v in event.items() if v is not None}
                try:
                    redis_client.xadd(f'events:{subscriber_id}', clean_event)
                    logger.info(f"Routed to {subscriber_id}: eventType={event['eventType']}, eventId={event['eventId']}")
                    events_routed_to_redis.inc()
                except Exception as e:
                    logger.error(f"Error routing event to {subscriber_id}: {e}")
                    redis_write_failures.inc()
                
# matching logic
def matches_criteria(event, criteria):
    if event['eventType'] not in criteria['event_types']:
        return False
    if criteria['user_tiers'] and event['userTier'] not in criteria['user_tiers']:
        return False
    if criteria['min_amount'] and (event.get('amount') or 0) < criteria['min_amount']:
        return False
    return True

def filter_updates_consumer_loop():
    consumer = KafkaConsumer(
        'filter-updates',
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='latest',
        group_id='filter-service-updates',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    for message in consumer:
        update = message.value
        subscriber_id = update['subscriber_id']
        
        # Only update if user is currently active
        if subscriber_id in active_streams:
            active_streams[subscriber_id] = update
            logger.info(f"Updated filters for {subscriber_id}: {update}")

# In main, start both consumer threads
if __name__ == "__main__":
    threading.Thread(target=kafka_consumer_loop, daemon=True).start()
    threading.Thread(target=filter_updates_consumer_loop, daemon=True).start()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
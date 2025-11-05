from kafka import KafkaProducer
from faker import Faker
import json
import time
from datetime import datetime, timezone
import random
import sys

# Initialize Faker for generating realistic fake data
fake = Faker()

def create_producer_with_retry(max_retries=5):
    for attempt in range(max_retries):
        try:
            return KafkaProducer(
                # bootstrap_servers=['localhost:9092'], # Use this line when running locally AND in Docker Compose
                bootstrap_servers=['kafka:9092'],
                api_version=(2, 6, 0),
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        except Exception as e:
            print(f"Failed to connect to Kafka (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
    print("Could not connect to Kafka. Exiting.")
    sys.exit(1)

# Use it:
producer = create_producer_with_retry()

# Create Kafka Producer
# producer = KafkaProducer(
#     bootstrap_servers=['localhost:9092'],
#     value_serializer=lambda v: json.dumps(v).encode('utf-8')
# )

# Error handling with retries if Kafka is down
def send_with_retry(producer, topic, event, max_retries=3):
    for attempt in range(max_retries):
        try:
            future = producer.send(topic, value=event)
            future.get(timeout=10)  # Wait for confirmation
            return True
        except Exception as e:
            print(f"Send failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
    print(f"Failed to send event after {max_retries} attempts")
    return False

print("🚀 Event Producer started. Publishing to Kafka topic 'user-events'...")

# Infinite loop - generate events continuously
try:
    while True:
        # Generate event type first
        event_type = random.choice(["click", "purchase", "view", "signup"])

        # Generate amount only for purchase events
        amount = round(random.uniform(10, 500), 2) if event_type == "purchase" else None

        event = {
            "eventId": fake.uuid4(),
            "userId": f"user_{random.randint(1, 100)}",
            "eventType": event_type,  # Now this variable exists
            "userTier": random.choice(["free", "premium", "enterprise"]),
            "amount": amount,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Send to Kafka
        if not send_with_retry(producer, 'user-events', event):
            # Log to file for manual recovery
            with open('failed_events.log', 'a') as f:
                f.write(json.dumps(event) + '\n')
        
        # Print for visibility
        print(f"📤 Sent: {event['eventType']} | User: {event['userId']} | Tier: {event['userTier']}")
        
        time.sleep(0.5)  # 2 events per second

except KeyboardInterrupt:
    print("\n Producer stopped")
    producer.close()
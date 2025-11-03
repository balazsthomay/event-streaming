from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from typing import Optional, List
from kafka import KafkaProducer
import json

app = FastAPI()

def get_db():
    return psycopg2.connect(
        host="localhost",
        database="eventstream",
        user="eventstream",
        password="eventstream"
    )

class FilterCriteria(BaseModel):
    subscriber_id: str
    event_types: List[str]
    user_tiers: Optional[List[str]] = None
    min_amount: Optional[float] = None
    
kafka_producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.post("/filters")
def create_filter(criteria: FilterCriteria):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO filter_criteria (subscriber_id, event_types, user_tiers, min_amount) VALUES (%s, %s, %s, %s)",
        (criteria.subscriber_id, criteria.event_types, criteria.user_tiers, criteria.min_amount)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "created"}

@app.get("/filters/{subscriber_id}")
def get_filter(subscriber_id: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT event_types, user_tiers, min_amount FROM filter_criteria WHERE subscriber_id = %s", (subscriber_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if not result:
        raise HTTPException(status_code=404, detail="Filter not found")
    return {
        "subscriber_id": subscriber_id,
        "event_types": result[0],
        "user_tiers": result[1],
        "min_amount": float(result[2]) if result[2] else None
    }
    
@app.put("/filters/{subscriber_id}")
def update_filter(subscriber_id: str, criteria: FilterCriteria):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE filter_criteria SET event_types = %s, user_tiers = %s, min_amount = %s WHERE subscriber_id = %s",
        (criteria.event_types, criteria.user_tiers, criteria.min_amount, subscriber_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    
    # Publish FilterUpdated event
    kafka_producer.send('filter-updates', value={
        "subscriber_id": subscriber_id,
        "event_types": criteria.event_types,
        "user_tiers": criteria.user_tiers,
        "min_amount": criteria.min_amount
    })
    
    return {"status": "updated"}
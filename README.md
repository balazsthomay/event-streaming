# Real-Time Event Streaming System

Streams filtered user events to clients over WebSocket. Uses Kafka for durability, Redis for low-latency queues, PostgreSQL for filter storage.

## Architecture

```
Producer → Kafka → Filter Service → Redis Streams → WebSocket Server → Client
                      ↓
              Subscriber Management API
                      ↓
                  PostgreSQL
```

## Quick Start

Start infrastructure:
```bash
docker-compose up -d
psql -h localhost -U eventstream -d eventstream -f schema.sql
pip install fastapi uvicorn kafka-python redis psycopg2-binary faker requests
```

Start services in separate terminals:
```bash
cd subscriber-management && python api.py  # Port 8001
cd filter-service && python filter_service.py  # Port 8002
cd websocket-server && python server.py  # Port 8003
cd producer && python producer.py
```

Create a filter and connect:
```bash
curl -X POST http://localhost:8001/filters \
  -H "Content-Type: application/json" \
  -d '{"subscriber_id": "user_1", "event_types": ["purchase"], "user_tiers": ["premium"], "min_amount": 100}'

websocat ws://localhost:8003/ws/user_1
```

## Key Design Decisions

**Kafka + Redis split**: Kafka handles durability and replay. Redis handles fast per-user queues. Each tool does what it's best at.

**Single Filter Service instance**: Works for demo but doesn't scale horizontally. Scaling would need consumer groups and shared state in Redis.

**Lazy stream creation**: Redis streams created only when users connect. Saves memory but users miss events while disconnected.

**No authentication**: Any subscriber_id works. Production needs JWT tokens.

## Known Limitations

- No backfill for missed events
- Filter Service doesn't scale horizontally
- No rate limiting on APIs
- Filter updates only apply to connected users
- No monitoring dashboard

## What's Implemented

- Structured logging (INFO/DEBUG/ERROR levels)
- Health checks on all services
- Retry logic with exponential backoff
- Error handling for Redis and API failures
- Unit tests for filter matching

## Tech Stack

Python, FastAPI, Kafka, Redis, PostgreSQL, WebSockets# event-streaming

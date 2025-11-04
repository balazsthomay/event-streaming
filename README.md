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
pip install fastapi uvicorn kafka-python redis psycopg2-binary faker requests locust websocket-client
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

python client.py
```

## Key Design Decisions

**Kafka + Redis split**: Kafka handles durability and replay. Redis handles fast per-user queues. Each tool does what it's best at.

**Single Filter Service instance**: Doesn't scale horizontally. We would need to move active_streams to Redis (in-memory) so #1 each filter-service instance reads events from their assigned Kafka partition, #2 Check Redis to see if any user cares about this event, #3 Write matching events to Redis Streams

**Lazy stream creation**: Redis streams created only when users connect. Saves memory but users miss events while disconnected.

**No authentication**: Any subscriber_id works.

## Known Limitations

- No backfill for missed events
- Filter Service doesn't scale horizontally
- No rate limiting on APIs
- Filter updates only apply to connected users
- No monitoring dashboard

## What's Implemented

- Structured logging (INFO/DEBUG/ERROR levels)
- Health checks on filter_service and Websocket
- Retry logic in producer, server
- Error handling for Redis and API failures
- Unit tests for filter matching

## Observability

Prometheus metrics at `:8002/metrics` (Filter Service) and `:8003/metrics` (WebSocket Server):
- Events read/matched/routed, Redis failures, active streams
- Active connections, events sent to clients

**Metrics endpoints**:
```bash
curl http://localhost:8002/metrics | grep -E "(active_streams_count|events_matched)"
curl http://localhost:8003/metrics | grep -E "(active_websocket|events_sent)"
```

## Load Testing

Tested with Locust:
- **10 concurrent connections**: Stable
- **50 concurrent connections**: 98% failure rate
- didn't test inbetween

```bash
python create_test_filters.py
locust -f locustfile.py --headless --users 10 --spawn-rate 2 --run-time 30s
```

**Bottleneck**: probably single-threaded uvicorn. Would need multiple workers or load balancer to scale beyond ~10 connections.

## Tech Stack

Python, FastAPI, Kafka, Redis, PostgreSQL, WebSockets# event-streaming

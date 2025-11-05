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

### AWS Deployment
```bash
# Build multi-architecture image
cd producer
docker buildx build --platform linux/amd64,linux/arm64 \
  -t /event-streaming-producer:latest --push .

# Pull and run on EC2
docker pull /event-streaming-producer:latest
docker run /event-streaming-producer:latest
```

## Key Design Decisions

**Kafka + Redis split**: Kafka handles durability and replay. Redis handles fast per-user queues. Each tool does what it's best at.

**Single Filter Service instance**: Doesn't scale horizontally. We would need to move active_streams to Redis (in-memory) so #1 each filter-service instance reads events from their assigned Kafka partition, #2 Check Redis to see if any user cares about this event, #3 Write matching events to Redis Streams

**Lazy stream creation**: Redis streams created only when users connect. Saves memory but users miss events while disconnected.

**Containerization**: Docker for consistent deployments across environments. Supports both ARM64 (Mac) and AMD64 (AWS EC2).

## Known Limitations

- No backfill for missed events
- Filter Service doesn't scale horizontally
- No rate limiting on APIs
- Filter updates only apply to connected users
- No monitoring dashboard
- probably single-threaded uvicorn. Would need multiple workers or load balancer to scale beyond ~10 connections.

## Observability

Prometheus metrics at `:8002/metrics` (Filter Service) and `:8003/metrics` (WebSocket Server):
- Events read/matched/routed, Redis failures, active streams
- Active connections, events sent to clients

Check Prometheus metrics:
```bash
# Filter Service metrics
curl http://localhost:8002/metrics | grep -E "(active_streams_count|events_matched)"

# WebSocket Server metrics
curl http://localhost:8003/metrics | grep -E "(active_websocket|events_sent)"

# Health checks
curl http://localhost:8002/health
curl http://localhost:8003/health
```

## Load Testing

Tested with Locust:
- **10 concurrent connections**: Stable
- **50 concurrent connections**: 98% failure rate
- didn't test inbetween

Uses Locust for WebSocket load testing:
```bash
# Create filters for 100 test users
python create_test_filters.py

# Run load test
locust -f locustfile.py --headless --users 10 --spawn-rate 2 --run-time 30s
```

## Tech Stack

**Backend**: Python, FastAPI, Kafka, Redis, PostgreSQL, WebSockets  
**Infra**: Docker, AWS ECR, AWS EC2  
**Monitoring**: Prometheus metrics, structured logging
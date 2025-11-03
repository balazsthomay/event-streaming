from fastapi import FastAPI, WebSocket, Response
import redis
import requests
import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.websocket("/ws/{subscriber_id}")
async def websocket_endpoint(websocket: WebSocket, subscriber_id: str):
    await websocket.accept()
    
    # Activate stream in Filter Service
    logger.info(f"Activating stream for subscriber {subscriber_id}")
    try:
        response = requests.post("http://localhost:8002/activate-stream", json={"subscriber_id": subscriber_id})
        if response.status_code != 200:
            logger.error(f"Failed to activate stream for subscriber {subscriber_id}: status_code={response.status_code}")
            return
    except Exception as e:
        logger.error(f"Error activating stream for subscriber {subscriber_id}: {e}")
        return
    
    redis_failures = 0
    max_failures = 3
    
    try:
        # Read from Redis Stream and push to client
        last_id = '0'
        while True:
            try:
                events = redis_client.xread({f'events:{subscriber_id}': last_id}, block=1000, count=10)
                redis_failures = 0  # Reset counter on success
            except Exception as e:
                redis_failures += 1
                logger.error(f"Error reading from Redis for subscriber {subscriber_id} (attempt {redis_failures}/{max_failures}): {e}")
                if redis_failures >= max_failures:
                    logger.error(f"Max Redis failures reached for subscriber {subscriber_id}, closing connection")
                    break
                await asyncio.sleep(1)
                continue
                
            if events:
                for stream, messages in events:
                    for message_id, data in messages:
                        await websocket.send_json(data)
                        last_id = message_id
                        logger.debug(f"Sent event {message_id} to subscriber {subscriber_id}")
            await asyncio.sleep(0.1)
    except:
        pass
    finally:
        # Deactivate stream when client disconnects
        requests.delete(f"http://localhost:8002/deactivate-stream/{subscriber_id}")
        logger.info(f"Stream deactivated for subscriber {subscriber_id}")
        
@app.get("/health")
def health_check():
    redis_ok = check_redis()
    filter_service_ok = check_filter_service()
    
    all_healthy = redis_ok and filter_service_ok
    status_code = 200 if all_healthy else 503
    
    return Response(
        content=json.dumps({
            "status": "healthy" if all_healthy else "unhealthy",
            "dependencies": {
                "redis": "up" if redis_ok else "down",
                "filter_service": "up" if filter_service_ok else "down"
            }
        }),
        status_code=status_code,
        media_type="application/json"
    )

def check_redis():
    try:
        redis_client.ping()
        return True
    except Exception:
        return False

def check_filter_service():
    try:
        response = requests.get("http://localhost:8002/health", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
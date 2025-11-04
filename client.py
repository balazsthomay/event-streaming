# client.py
import asyncio
import websockets
import json

async def connect():
    uri = "ws://localhost:8003/ws/user_1"
    async with websockets.connect(uri) as websocket:
        print("Connected! Waiting for events...")
        while True:
            message = await websocket.recv()
            event = json.loads(message)
            print(f"Received: {event}")

asyncio.run(connect())
# WebSocket load testing

from locust import User, task, between
import websocket
import json

class WebSocketUser(User):
    wait_time = between(1, 2)
    
    def on_start(self):
        self.user_id = f"load_test_user_{WebSocketUser.user_id_counter}"
        WebSocketUser.user_id_counter += 1
        
        self.ws = websocket.create_connection(f"ws://localhost:8003/ws/{self.user_id}")
        print(f"Connected: {self.user_id}")
    
    @task
    def receive_events(self):
        try:
            result = self.ws.recv()
            event = json.loads(result)
            print(f"{self.user_id} received: {event['eventType']}")
        except:
            pass
    
    def on_stop(self):
        self.ws.close()

WebSocketUser.user_id_counter = 0
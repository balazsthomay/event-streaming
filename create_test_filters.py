import requests

# Create filters for 100 test users
for i in range(100):
    user_id = f"load_test_user_{i}"
    response = requests.post(
        "http://localhost:8001/filters",
        json={
            "subscriber_id": user_id,
            "event_types": ["purchase"],
            "user_tiers": ["premium"],
            "min_amount": 100
        }
    )
    if response.status_code == 200:
        print(f"Created filter for {user_id}")
    else:
        print(f"Failed for {user_id}: {response.text}")
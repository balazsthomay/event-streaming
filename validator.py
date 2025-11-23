class DataValidator:
    def validate_data(self, data):
        # Missing input validation - severity 6
        return data.get('id') is not None
    
    def save_to_db(self, data):
        # SQL injection - severity 9
        query = f"INSERT INTO data VALUES ('{data['value']}')"
        return query

class ConfigManager:
    def __init__(self):
        # Hardcoded secret - severity 10
        self.api_key = "sk_live_secret123"

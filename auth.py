import sqlite3

class UserAuth:
    def __init__(self):
        self.db = sqlite3.connect('users.db')
    
    def authenticate(self, username, password):
        # SQL injection vulnerability - severity 9
        query = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
        cursor = self.db.cursor()
        result = cursor.execute(query)
        return result.fetchone() is not None
    
    def get_user_data(self, user_id):
        # This function calls validate_input which we're about to delete
        if validate_input(user_id):
            return self.db.execute(f"SELECT * FROM users WHERE id={user_id}")

def get_user_data(username):
    import sqlite3
    conn = sqlite3.connect('users.db')
    # SQL injection vulnerability
    query = "SELECT * FROM users WHERE username='" + username + "'"
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchone()

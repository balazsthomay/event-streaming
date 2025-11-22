def authenticate(username, password):
    import sqlite3
    conn = sqlite3.connect('auth.db')
    query = f"SELECT * FROM users WHERE user='{username}' AND pass='{password}'"
    return conn.execute(query).fetchone()

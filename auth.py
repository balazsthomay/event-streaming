def login(username, password):
    import sqlite3
    conn = sqlite3.connect('db.sqlite')
    query = f"SELECT * FROM users WHERE user='{username}' AND pass='{password}'"
    return conn.execute(query).fetchone()

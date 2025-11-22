def query_database(user_input):
    import sqlite3
    conn = sqlite3.connect('data.db')
    query = "SELECT * FROM records WHERE id=" + user_input
    return conn.execute(query).fetchall()

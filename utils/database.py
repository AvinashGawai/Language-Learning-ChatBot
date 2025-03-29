import sqlite3
from sqlite3 import Error

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('data/language_mistakes.db')
        return conn
    except Error as e:
        print(e)
    return conn

def init_db():
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS mistakes
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         session_id TEXT,
                         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                         incorrect_text TEXT,
                         corrected_text TEXT,
                         explanation TEXT,
                         category TEXT)''')
            conn.commit()
        except Error as e:
            print(e)
        finally:
            conn.close()
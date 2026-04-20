import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'farmer_data.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(SCHEMA_PATH):
        print("Schema file not found.")
        return
    
    with get_db_connection() as conn:
        with open(SCHEMA_PATH, 'r') as f:
            conn.executescript(f.read())
        conn.commit()
    print("Database initialized successfully.")

def log_advisory(crop, temp, humidity, price, alert, action, priority, confidence):
    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO advisory_logs 
            (crop, temperature, humidity, market_price, alert_generated, action_recommended, priority, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (crop, temp, humidity, price, alert, action, priority, confidence))
        conn.commit()

def get_history(limit=10):
    with get_db_connection() as conn:
        logs = conn.execute('SELECT * FROM advisory_logs ORDER BY timestamp DESC LIMIT ?', (limit,)).fetchall()
        return [dict(log) for log in logs]

def get_faqs():
    with get_db_connection() as conn:
        faqs = conn.execute('SELECT * FROM faqs').fetchall()
        return [dict(faq) for faq in faqs]

import sqlite3
import os
import time

DB_PATH = 'master_trader.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            subscribed BOOLEAN DEFAULT FALSE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache (
            coin_id TEXT PRIMARY KEY,
            data TEXT,
            timestamp REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            user_id INTEGER,
            coin_id TEXT,
            threshold REAL,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def set_subscribed(user_id, subscribed=True):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET subscribed = ? WHERE user_id = ?', (subscribed, user_id))
    conn.commit()
    conn.close()

def get_subscribed_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE subscribed = TRUE')
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def cache_data(coin_id, data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO cache (coin_id, data, timestamp) VALUES (?, ?, ?)',
                   (coin_id, str(data), time.time()))
    conn.commit()
    conn.close()

def get_cached_data(coin_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM cache WHERE coin_id = ? ORDER BY timestamp DESC LIMIT 1', (coin_id,))
    row = cursor.fetchone()
    conn.close()
    return eval(row[0]) if row else None

def is_cache_fresh(coin_id, max_age=3600):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp FROM cache WHERE coin_id = ? ORDER BY timestamp DESC LIMIT 1', (coin_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return time.time() - row[0] < max_age
    return False

# Khởi tạo DB
init_db()

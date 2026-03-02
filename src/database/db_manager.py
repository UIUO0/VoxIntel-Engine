import sqlite3
import os
from datetime import datetime

# Define the database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'voxintel.db')

def init_db():
    """Initializes the SQLite database and creates the logs table if it doesn't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            speaker TEXT NOT NULL,
            text TEXT NOT NULL,
            sentiment_score REAL
        )
    ''')
    
    conn.commit()
    conn.close()

def get_recent_logs(limit=20):
    """
    Retrieves the most recent conversation logs.
    
    Args:
        limit (int): Number of records to return.
        
    Returns:
        list: List of tuples (timestamp, speaker, text, sentiment_score)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT timestamp, speaker, text, sentiment_score 
        FROM logs 
        ORDER BY id DESC 
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_latest_sentiment():
    """
    Retrieves the sentiment score of the very last entry.
    
    Returns:
        float: The last sentiment score, or 0.0 if no data exists.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT sentiment_score 
        FROM logs 
        ORDER BY id DESC 
        LIMIT 1
    ''')
    
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0.0
    print(f"Database initialized at: {DB_PATH}")

def save_entry(speaker, text, sentiment_score):
    """
    Saves a conversation entry to the database.
    
    Args:
        speaker (str): 'User' or 'AI'
        text (str): The spoken text
        sentiment_score (float): The sentiment compound score (-1.0 to 1.0)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO logs (timestamp, speaker, text, sentiment_score)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, speaker, text, sentiment_score))
    
    conn.commit()
    conn.close()

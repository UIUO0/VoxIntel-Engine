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

def get_latest_sentiment(speaker_filter=None):
    """
    Retrieves the sentiment score of the very last entry.
    Args:
        speaker_filter (str): Optional. If set (e.g. 'User'), only returns sentiment for that speaker.
    Returns:
        float: The last sentiment score, or 0.0 if no data exists.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = 'SELECT sentiment_score FROM logs'
    params = ()
    
    if speaker_filter:
        query += ' WHERE speaker = ?'
        params = (speaker_filter,)
        
    query += ' ORDER BY id DESC LIMIT 1'
    
    cursor.execute(query, params)
    
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0.0

def get_average_sentiment(speaker_filter=None):
    """
    Calculates the average sentiment score for all logs of a specific speaker.
    Returns:
        float: The average score (-1.0 to 1.0), or 0.0 if no data.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = 'SELECT AVG(sentiment_score) FROM logs'
    params = ()
    
    if speaker_filter:
        query += ' WHERE speaker = ?'
        params = (speaker_filter,)
        
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    
    return row[0] if row and row[0] is not None else 0.0

def clear_logs():
    """Deletes all records from the logs table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM logs')
    conn.commit()
    conn.close()
    print("🧹 Database logs cleared.")
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

import os
import sqlite3
import time
from datetime import datetime

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "voxintel.db"
)


def _get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def _execute_write(query, params=(), retries=3):
    for attempt in range(retries):
        try:
            conn = _get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return
        except sqlite3.OperationalError as e:
            if "locked" not in str(e).lower() or attempt == retries - 1:
                raise
            time.sleep(0.1 * (attempt + 1))


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            speaker TEXT NOT NULL,
            text TEXT NOT NULL,
            sentiment_score REAL
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_speaker_id ON logs (speaker, id DESC)")
    conn.commit()
    conn.close()

def get_recent_logs(limit=20):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT timestamp, speaker, text, sentiment_score
        FROM logs
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_latest_sentiment(speaker_filter=None):
    conn = _get_connection()
    cursor = conn.cursor()

    query = "SELECT sentiment_score FROM logs"
    params = ()

    if speaker_filter:
        query += " WHERE speaker = ?"
        params = (speaker_filter,)

    query += " ORDER BY id DESC LIMIT 1"
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0.0

def get_average_sentiment(speaker_filter=None):
    conn = _get_connection()
    cursor = conn.cursor()

    query = "SELECT AVG(sentiment_score) FROM logs"
    params = ()

    if speaker_filter:
        query += " WHERE speaker = ?"
        params = (speaker_filter,)

    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] is not None else 0.0

def clear_logs():
    _execute_write("DELETE FROM logs")

def save_entry(speaker, text, sentiment_score):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _execute_write(
        """
        INSERT INTO logs (timestamp, speaker, text, sentiment_score)
        VALUES (?, ?, ?, ?)
        """,
        (timestamp, speaker, text, sentiment_score),
    )

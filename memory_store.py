import sqlite3
from datetime import datetime

DB_NAME = "chat_memory.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_message(session_id, role, message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chat_history (session_id, role, message, created_at)
        VALUES (?, ?, ?, ?)
    """, (session_id, role, message, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_recent_history(session_id, limit=10):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, message
        FROM chat_history
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (session_id, limit))

    rows = cursor.fetchall()
    conn.close()

    rows.reverse()

    return [{"role": role, "message": message} for role, message in rows]


def get_all_sessions():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            session_id,
            MIN(created_at) as created_at,
            (
                SELECT message
                FROM chat_history ch2
                WHERE ch2.session_id = ch1.session_id
                  AND ch2.role = 'user'
                ORDER BY ch2.id ASC
                LIMIT 1
            ) as first_message
        FROM chat_history ch1
        GROUP BY session_id
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    sessions = []
    for session_id, created_at, first_message in rows:
        title = (first_message or "New Chat").strip()
        if len(title) > 35:
            title = title[:35] + "..."

        sessions.append({
            "session_id": session_id,
            "title": title,
            "created_at": created_at
        })

    return sessions


def get_session_messages(session_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, message, created_at
        FROM chat_history
        WHERE session_id = ?
        ORDER BY id ASC
    """, (session_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "role": role,
            "message": message,
            "created_at": created_at
        }
        for role, message, created_at in rows
    ]
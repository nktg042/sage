import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "")

# Initialize client globally
_client = None
_db = None


def get_db():
    global _client, _db
    if _client is None:
        if not MONGO_URI:
            print("[Warning] MONGO_URI is missing from .env, falling back to localhost.")
            _client = MongoClient("mongodb://localhost:27017/")
        else:
            _client = MongoClient(MONGO_URI)
        # Using a database named 'mindease_db'
        _db = _client.get_database("mindease_db")
    return _db


def init_db():
    """Create indexes for the MongoDB collection to ensure fast queries."""
    db = get_db()
    db.chat_history.create_index([("session_id", 1)])
    db.chat_history.create_index([("created_at", -1)])


def save_message(session_id, role, message):
    db = get_db()
    db.chat_history.insert_one({
        "session_id": session_id,
        "role": role,
        "message": message,
        "created_at": datetime.now().isoformat()
    })


def get_recent_history(session_id, limit=10):
    db = get_db()
    
    # Query the last N messages for the session, sorted by created_at DESC
    cursor = db.chat_history.find(
        {"session_id": session_id},
        {"_id": 0, "role": 1, "message": 1}
    ).sort("created_at", -1).limit(limit)
    
    rows = list(cursor)
    
    # Needs to be chronologically ordered for AI context (oldest to newest)
    rows.reverse()
    
    return rows


def get_all_sessions():
    db = get_db()
    
    pipeline = [
        # Sort entirely by creation date ascending so $first below finds the true initial record
        {"$sort": {"created_at": 1}},
        # Group by session_id, capturing the earliest date and all messages
        {
            "$group": {
                "_id": "$session_id",
                "created_at": {"$first": "$created_at"},
                "messages": {"$push": "$$ROOT"}
            }
        },
        # Re-sort descending so the most recently created session is at the top
        {"$sort": {"created_at": -1}}
    ]
    
    results = list(db.chat_history.aggregate(pipeline))
    
    sessions = []
    for r in results:
        session_id = r["_id"]
        created_at = r["created_at"]
        
        first_message_str = "New Chat"
        # Find the very first message the USER sent in this session to act as the title
        for msg in r["messages"]:
            if msg.get("role") == "user":
                first_message_str = msg.get("message", "")
                break
                
        title = first_message_str.strip()
        if len(title) > 35:
            title = title[:35] + "..."
            
        sessions.append({
            "session_id": session_id,
            "title": title or "New Chat",
            "created_at": created_at
        })
        
    return sessions


def get_session_messages(session_id):
    db = get_db()
    
    # Fetch all messages for the session, in chronological order
    cursor = db.chat_history.find(
        {"session_id": session_id},
        {"_id": 0, "role": 1, "message": 1, "created_at": 1}
    ).sort("created_at", 1)
    
    return list(cursor)
import os
from datetime import datetime
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "")

_client = None
_db = None


def get_db():
    global _client, _db
    if _client is None:
        if not MONGO_URI:
            print("[Warning] MONGO_URI is missing from .env, falling back to localhost.")
            _client = MongoClient("mongodb://localhost:27017/")
        else:
            _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
        _db = _client.get_database("mindease_db")
    return _db


def init_db():
    db = get_db()
    db.chat_history.create_index([("session_id", 1)])
    db.chat_history.create_index([("created_at", -1)])
    db.chat_history.create_index([("username", 1)])
    db.users.create_index([("username", 1)], unique=True)


# ── Auth & Users ───────────────────────────────────────────────────

def create_user(username, hashed_password):
    db = get_db()
    if db.users.find_one({"username": username}):
        return False
    db.users.insert_one({
        "username": username,
        "password": hashed_password,
        "created_at": datetime.now().isoformat()
    })
    return True


def get_user(username):
    return get_db().users.find_one({"username": username})


# ── Chat Memory ────────────────────────────────────────────────────

def save_message(session_id, role, message, username="anonymous", is_crisis=False):
    db = get_db()
    db.chat_history.insert_one({
        "session_id": session_id,
        "username": username,
        "role": role,
        "message": message,
        "is_crisis": is_crisis,
        "created_at": datetime.now().isoformat()
    })


def get_recent_history(session_id, limit=10):
    db = get_db()
    cursor = db.chat_history.find(
        {"session_id": session_id},
        {"_id": 0, "role": 1, "message": 1}
    ).sort("created_at", -1).limit(limit)
    rows = list(cursor)
    rows.reverse()
    return rows


def get_all_sessions(username="anonymous"):
    db = get_db()
    pipeline = [
        {"$match": {"username": username}},
        {"$sort": {"created_at": 1}},
        {
            "$group": {
                "_id": "$session_id",
                "created_at": {"$first": "$created_at"},
                "messages": {"$push": "$$ROOT"}
            }
        },
        {"$sort": {"created_at": -1}}
    ]
    
    results = list(db.chat_history.aggregate(pipeline))
    sessions = []
    
    for r in results:
        session_id = r["_id"]
        created_at = r["created_at"]
        first_message_str = "New Chat"
        
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


def get_session_messages(session_id, username="anonymous"):
    db = get_db()
    cursor = db.chat_history.find(
        {"session_id": session_id, "username": username},
        {"_id": 0, "role": 1, "message": 1, "created_at": 1}
    ).sort("created_at", 1)
    return list(cursor)


# ── Admin Dashboard ────────────────────────────────────────────────

def get_admin_stats():
    db = get_db()
    total_users = db.users.count_documents({})
    total_messages = db.chat_history.count_documents({})
    total_crises = db.chat_history.count_documents({"is_crisis": True})
    total_sessions = len(db.chat_history.distinct("session_id"))
    
    return {
        "users": total_users,
        "sessions": total_sessions,
        "messages": total_messages,
        "crises": total_crises
    }
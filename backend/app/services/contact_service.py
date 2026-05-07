import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.db.json_manager import read_json, update_json

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_DIR = BASE_DIR / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)

CONTACTS_PATH = str(DB_DIR / "contacts.json")
CHAT_PATH = str(DB_DIR / "chat.json")

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def next_id(items: List[Dict[str, Any]]) -> int:
    if not items:
        return 1
    return max(int(item.get("id", 0)) for item in items) + 1

def create_contact_message(name: str, email: str, message: str) -> Dict[str, Any]:
    def _add_msg(contacts: list):
        contact = {
            "id": next_id(contacts),
            "name": name,
            "email": email,
            "message": message,
            "created_at": now_iso(),
        }
        contacts.append(contact)
        return contacts

    update_json(CONTACTS_PATH, _add_msg)
    return {"success": True, "message": "Message sent successfully."}

def process_send_chat(user: Optional[Dict[str, Any]], thread_id: Optional[str], message: str) -> Dict[str, Any]:
    if user:
        tid = f"user_{user['id']}"
        author = user["name"]
    else:
        tid = thread_id
        if not tid or tid == "undefined" or tid == "null":
            tid = f"anon_{uuid.uuid4().hex[:8]}"
        author = "Guest"
        
    msg = {
        "thread_id": tid,
        "author": author,
        "role": "user",
        "message": message,
        "timestamp": now_iso(),
        "read": False
    }

    def _add_chat(chats: list):
        msg["id"] = next_id(chats)
        chats.append(msg)
        return chats

    update_json(CHAT_PATH, _add_chat)
    return {"success": True, "message": msg, "thread_id": tid}

def fetch_chat_messages(thread_id: str) -> List[Dict[str, Any]]:
    chats = read_json(CHAT_PATH)
    return [c for c in chats if c["thread_id"] == thread_id]

def fetch_admin_chats() -> Dict[str, Any]:
    chats = read_json(CHAT_PATH)
    threads = {}
    for c in chats:
        tid = c["thread_id"]
        if tid not in threads:
            threads[tid] = []
        threads[tid].append(c)
    return threads

def process_admin_reply(thread_id: str, message: str) -> Dict[str, Any]:
    msg = {
        "thread_id": thread_id,
        "author": "Supporting Staff",
        "role": "admin",
        "message": message,
        "timestamp": now_iso(),
        "read": True
    }

    def _add_reply(chats: list):
        msg["id"] = next_id(chats)
        for c in chats:
            if c["thread_id"] == thread_id:
                c["read"] = True
        chats.append(msg)
        return chats

    update_json(CHAT_PATH, _add_reply)
    return {"success": True, "message": msg}


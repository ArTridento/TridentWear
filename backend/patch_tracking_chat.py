"""
Patch script for adding Shiprocket Tracking & Advanced Chat System to TridentWear.
"""
from pathlib import Path

SRC = Path(r"d:\TridentWear\backend\app.py")
text = SRC.read_text(encoding="utf-8")

# ── 1. DB Paths ─────────────────────────────────────────
if "CHAT_PATH" not in text:
    text = text.replace(
        'WISHLIST_PATH = DB_DIR / "wishlist.json"',
        'WISHLIST_PATH = DB_DIR / "wishlist.json"\n'
        'CHAT_PATH = DB_DIR / "chat.json"'
    )

# ── 2. Pydantic Models ────────────────────────────────────────
NEW_MODELS = '''
class ChatMessagePayload(BaseModel):
    message: str
    admin_reply: bool = False
    thread_id: Optional[str] = None
'''
if "class ChatMessagePayload" not in text:
    text = text.replace("class ContactPayload(BaseModel):", NEW_MODELS + "\nclass ContactPayload(BaseModel):")

# ── 3. Helpers ───────────────────────────────────────────
NEW_HELPERS = '''
def load_chat() -> List[Dict[str, Any]]:
    return read_json(CHAT_PATH, [])

def save_chat(chats: List[Dict[str, Any]]) -> None:
    write_json(CHAT_PATH, chats)

def create_shiprocket_shipment(order: Dict[str, Any]) -> Dict[str, Any]:
    """Stub for creating shipment on Shiprocket."""
    # In production, use os.getenv("SHIPROCKET_API_KEY") 
    # and make requests to Shiprocket API.
    return {
        "tracking_id": f"SR{uuid.uuid4().hex[:8].upper()}",
        "courier": "Delhivery",
        "estimated_delivery": (datetime.now(timezone.utc) + timedelta(days=4)).strftime("%Y-%m-%d")
    }
'''
if "def load_chat()" not in text:
    text = text.replace("def load_contacts()", NEW_HELPERS + "\ndef load_contacts()")

# ── 4. Ensure DB file ────────────────────────────────────
if "write_json(CHAT_PATH" not in text:
    text = text.replace(
        'write_json(WISHLIST_PATH, wishlist)',
        'write_json(WISHLIST_PATH, wishlist)\n    chat = read_json(CHAT_PATH, [])\n    write_json(CHAT_PATH, chat)'
    )

# ── 5. Tracking Endpoints & Admin trigger ──────────────────────
# Replace update_order_status
OLD_UPDATE = '''@admin_router.put("/orders/{order_id}")
def update_order_status(order_id: str, payload: OrderStatusUpdate, _: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    orders = load_orders()
    for o in orders:
        if o.get("order_id") == order_id:
            o["status"] = payload.status
            save_orders(orders)
            return {"success": True, "message": "Order status updated.", "order": o}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")'''

NEW_UPDATE = '''@admin_router.put("/orders/{order_id}")
def update_order_status(order_id: str, payload: OrderStatusUpdate, _: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    orders = load_orders()
    for o in orders:
        if o.get("order_id") == order_id:
            o["status"] = payload.status
            # Trigger shipment logic
            if payload.status == "shipped" and not o.get("tracking_id"):
                try:
                    shipment = create_shiprocket_shipment(o)
                    o["tracking_id"] = shipment["tracking_id"]
                    o["courier"] = shipment["courier"]
                    o["estimated_delivery"] = shipment["estimated_delivery"]
                except Exception:
                    pass # Fallback handled by client tracking API

            save_orders(orders)
            return {"success": True, "message": "Order status updated.", "order": o}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

@orders_router.get("/orders/{order_id}/tracking")
def track_order(order_id: str) -> Dict[str, Any]:
    orders = load_orders()
    for o in orders:
        if o.get("order_id") == order_id:
            if o.get("tracking_id"):
                return {
                    "status": "In Transit" if o.get("status") == "shipped" else o.get("status", "Unknown").title(),
                    "courier": o.get("courier", "Standard Courier"),
                    "tracking_id": o.get("tracking_id"),
                    "estimated_delivery": o.get("estimated_delivery", "TBD")
                }
            return {
                "status": o.get("status", "pending").title(),
                "courier": "Pending Allocation",
                "tracking_id": None,
                "estimated_delivery": "Tracking will be updated soon"
            }
    raise HTTPException(status_code=404, detail="Order not found.")
'''
if "track_order(order_id" not in text:
    text = text.replace(OLD_UPDATE, NEW_UPDATE)

# ── 6. Chat API ──────────────────────────────────────────
CHAT_APIS = '''
# ════════════════════════════════════════════════════════════
# CHAT SYSTEM
# ════════════════════════════════════════════════════════════
@app.post("/api/chat/send")
def send_chat(payload: ChatMessagePayload, request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    chats = load_chat()
    
    # If anonymous, identify them by a generic thread_id
    if user:
        thread_id = f"user_{user['id']}"
        author = user["name"]
    else:
        thread_id = payload.thread_id or f"anon_{uuid.uuid4().hex[:8]}"
        author = "Guest"
        
    msg = {
        "id": next_id(chats),
        "thread_id": thread_id,
        "author": author,
        "role": "user",
        "message": payload.message,
        "timestamp": now_iso(),
        "read": False
    }
    chats.append(msg)
    save_chat(chats)
    return {"success": True, "message": msg, "thread_id": thread_id}

@app.get("/api/chat/messages")
def get_chat_messages(thread_id: str) -> List[Dict[str, Any]]:
    chats = load_chat()
    return [c for c in chats if c["thread_id"] == thread_id]

@admin_router.get("/chat")
def admin_get_chats(_: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    chats = load_chat()
    threads = {}
    for c in chats:
        tid = c["thread_id"]
        if tid not in threads:
            threads[tid] = []
        threads[tid].append(c)
    return threads

@admin_router.post("/chat/reply")
def admin_reply_chat(payload: ChatMessagePayload, request: Request, _: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    if not payload.thread_id:
        raise HTTPException(status_code=400, detail="Thread ID required")
    
    chats = load_chat()
    msg = {
        "id": next_id(chats),
        "thread_id": payload.thread_id,
        "author": "Supporting Staff",
        "role": "admin",
        "message": payload.message,
        "timestamp": now_iso(),
        "read": True
    }
    
    # mark whole thread as read by admin
    for c in chats:
        if c["thread_id"] == payload.thread_id:
            c["read"] = True

    chats.append(msg)
    save_chat(chats)
    return {"success": True, "message": msg}
'''
if "/api/chat/send" not in text:
    text += CHAT_APIS

SRC.write_text(text, encoding="utf-8")
print("✅ apply_tracking_chat.py completed.")

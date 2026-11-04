import sqlite3
import random
import string
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

DB_FILE = Path(__file__).parent / "diwali_party.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Guests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            pass_count INTEGER NOT NULL DEFAULT 1,
            pass_type TEXT NOT NULL DEFAULT 'General',
            notes TEXT,
            created_at TEXT NOT NULL,
            checked_in INTEGER NOT NULL DEFAULT 0,
            checked_in_at TEXT,
            checked_in_by TEXT
        )
    """)
    
    # One-Time Claim Tokens for Buyers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claim_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            pass_count INTEGER NOT NULL DEFAULT 1,
            pass_type TEXT NOT NULL DEFAULT 'General Pass',
            buyer_note TEXT,
            created_at TEXT NOT NULL,
            is_used INTEGER NOT NULL DEFAULT 0,
            used_at TEXT,
            used_by_name TEXT,
            used_by_phone TEXT,
            generated_pass_code TEXT
        )
    """)
    
    # Event settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    # Insert default settings if not exists
    defaults = {
        "event_name": "Diwali Dhoom & Gala Night 🪔",
        "event_date": "Saturday, November 7, 2026",
        "event_time": "7:00 PM Onwards",
        "event_venue": "Urban Forest Cafe and Restaurant",
        "event_location_url": "https://share.google/jryj9S1RXIgA4fnN7",
        "event_contact": "+91 63750 96687",
        "event_description": "Join us for an evening of festive lights, music, DJ, delicious dinner, fireworks and celebrations!",
        "admin_pin": "diwali2026"
    }
    
    for k, v in defaults.items():
        cursor.execute("INSERT OR IGNORE INTO event_settings (key, value) VALUES (?, ?)", (k, v))
        
    conn.commit()
    conn.close()

def generate_unique_code(prefix: str = "DWL") -> str:
    # Character set avoiding ambiguous 0, O, 1, I
    chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    conn = get_connection()
    cursor = conn.cursor()
    
    while True:
        suffix = "".join(random.choices(chars, k=5))
        candidate = f"{prefix}-{suffix}"
        cursor.execute("SELECT 1 FROM guests WHERE code = ?", (candidate,))
        if not cursor.fetchone():
            conn.close()
            return candidate

def get_settings() -> Dict[str, str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM event_settings")
    rows = cursor.fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}

def update_settings(settings: Dict[str, str]):
    conn = get_connection()
    cursor = conn.cursor()
    for k, v in settings.items():
        cursor.execute("""
            INSERT INTO event_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (k, v))
    conn.commit()
    conn.close()

def add_guest(name: str, phone: str, email: Optional[str] = None, 
              pass_count: int = 1, pass_type: str = "General", 
              notes: Optional[str] = None) -> Dict[str, Any]:
    code = generate_unique_code()
    now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO guests (code, name, phone, email, pass_count, pass_type, notes, created_at, checked_in)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (code, name.strip(), phone.strip(), (email or "").strip(), max(1, pass_count), pass_type, notes, now_str))
    guest_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute("SELECT * FROM guests WHERE id = ?", (guest_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

def get_guest_by_code(code: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM guests WHERE UPPER(code) = UPPER(?)", (code.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_guest_by_id(guest_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM guests WHERE id = ?", (guest_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def check_in_guest(code: str, checked_by: str = "Gate Staff") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM guests WHERE UPPER(code) = UPPER(?)", (code.strip(),))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return {"success": False, "error": "Invalid Pass Code. Guest not found."}
    
    guest = dict(row)
    if guest["checked_in"]:
        conn.close()
        return {
            "success": False,
            "already_checked_in": True,
            "guest": guest,
            "error": f"Already checked in at {guest.get('checked_in_at', 'earlier')}!"
        }
    
    now_str = datetime.now().strftime("%I:%M %p, %b %d")
    cursor.execute("""
        UPDATE guests
        SET checked_in = 1, checked_in_at = ?, checked_in_by = ?
        WHERE id = ?
    """, (now_str, checked_by, guest["id"]))
    conn.commit()
    
    cursor.execute("SELECT * FROM guests WHERE id = ?", (guest["id"],))
    updated_guest = dict(cursor.fetchone())
    conn.close()
    
    return {
        "success": True,
        "guest": updated_guest,
        "message": f"Welcome {updated_guest['name']}! Pass verified."
    }

def toggle_check_in(guest_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM guests WHERE id = ?", (guest_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    guest = dict(row)
    new_status = 0 if guest["checked_in"] else 1
    now_str = datetime.now().strftime("%I:%M %p, %b %d") if new_status else None
    
    cursor.execute("""
        UPDATE guests
        SET checked_in = ?, checked_in_at = ?, checked_in_by = ?
        WHERE id = ?
    """, (new_status, now_str, "Admin" if new_status else None, guest_id))
    conn.commit()
    
    cursor.execute("SELECT * FROM guests WHERE id = ?", (guest_id,))
    updated = dict(cursor.fetchone())
    conn.close()
    return updated

def delete_guest(guest_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM guests WHERE id = ?", (guest_id,))
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count > 0

def list_guests(search: Optional[str] = None, filter_status: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM guests WHERE 1=1"
    params = []
    
    if search:
        search_pattern = f"%{search.strip()}%"
        query += " AND (name LIKE ? OR phone LIKE ? OR code LIKE ? OR email LIKE ?)"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
        
    if filter_status == "checked_in":
        query += " AND checked_in = 1"
    elif filter_status == "pending":
        query += " AND checked_in = 0"
        
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_stats() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total_registrations, COALESCE(SUM(pass_count), 0) AS total_passes FROM guests")
    row1 = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) AS checked_in_registrations, COALESCE(SUM(pass_count), 0) AS checked_in_passes FROM guests WHERE checked_in = 1")
    row2 = cursor.fetchone()
    
    conn.close()
    
    total_reg = row1["total_registrations"]
    total_passes = row1["total_passes"]
    checked_in_reg = row2["checked_in_registrations"]
    checked_in_passes = row2["checked_in_passes"]
    
    return {
        "total_registrations": total_reg,
        "total_passes": total_passes,
        "checked_in_registrations": checked_in_reg,
        "checked_in_passes": checked_in_passes,
        "pending_registrations": total_reg - checked_in_reg,
        "pending_passes": total_passes - checked_in_passes
    }

# --- One-Time Claim Token Functions ---

def generate_claim_token(pass_count: int = 1, pass_type: str = "General Pass", buyer_note: Optional[str] = None) -> Dict[str, Any]:
    chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    conn = get_connection()
    cursor = conn.cursor()
    
    while True:
        suffix = "".join(random.choices(chars, k=6))
        token = f"INV-{suffix}"
        cursor.execute("SELECT 1 FROM claim_tokens WHERE token = ?", (token,))
        if not cursor.fetchone():
            break
            
    now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    cursor.execute("""
        INSERT INTO claim_tokens (token, pass_count, pass_type, buyer_note, created_at, is_used)
        VALUES (?, ?, ?, ?, ?, 0)
    """, (token, max(1, pass_count), pass_type, buyer_note, now_str))
    token_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute("SELECT * FROM claim_tokens WHERE id = ?", (token_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

def get_claim_token(token: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM claim_tokens WHERE UPPER(token) = UPPER(?)", (token.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def claim_token_and_create_guest(token_str: str, name: str, phone: str, 
                                 email: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM claim_tokens WHERE UPPER(token) = UPPER(?)", (token_str.strip(),))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return {"success": False, "error": "Invalid invite token. Please check the link or contact the organizer."}
        
    token_data = dict(row)
    if token_data["is_used"]:
        conn.close()
        return {
            "success": False,
            "already_claimed": True,
            "token": token_data,
            "error": f"This link was already claimed by {token_data['used_by_name']} on {token_data['used_at']}."
        }
        
    # Generate unique guest pass code
    pass_code = generate_unique_code()
    now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    # 1. Insert into guests
    cursor.execute("""
        INSERT INTO guests (code, name, phone, email, pass_count, pass_type, notes, created_at, checked_in)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        pass_code,
        name.strip(),
        phone.strip(),
        (email or "").strip(),
        token_data["pass_count"],
        token_data["pass_type"],
        notes or token_data.get("buyer_note"),
        now_str
    ))
    guest_id = cursor.lastrowid
    
    # 2. Mark token as used
    cursor.execute("""
        UPDATE claim_tokens
        SET is_used = 1, used_at = ?, used_by_name = ?, used_by_phone = ?, generated_pass_code = ?
        WHERE id = ?
    """, (now_str, name.strip(), phone.strip(), pass_code, token_data["id"]))
    
    conn.commit()
    
    cursor.execute("SELECT * FROM guests WHERE id = ?", (guest_id,))
    guest = dict(cursor.fetchone())
    conn.close()
    
    return {
        "success": True,
        "guest": guest,
        "token": token_data
    }

def list_claim_tokens() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM claim_tokens ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_claim_token(token_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM claim_tokens WHERE id = ?", (token_id,))
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count > 0

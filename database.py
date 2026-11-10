import os
import sqlite3
import random
import string
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

IS_POSTGRES = bool(DATABASE_URL)

if IS_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor

DB_FILE = Path(__file__).parent / "diwali_party.db"

def get_connection():
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

def execute_query(sql: str, params: tuple = (), fetch: str = "none", commit: bool = False, returning_id: bool = False):
    conn = get_connection()
    try:
        if IS_POSTGRES:
            formatted_sql = sql.replace("?", "%s")
            if returning_id:
                formatted_sql += " RETURNING id"
            cursor = conn.cursor()
            cursor.execute(formatted_sql, params)
            if commit:
                conn.commit()
            if returning_id:
                res = cursor.fetchone()
                return res["id"] if res else None
            if fetch == "one":
                row = cursor.fetchone()
                return dict(row) if row else None
            elif fetch == "all":
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
            return cursor.rowcount
        else:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            if commit:
                conn.commit()
            if returning_id:
                return cursor.lastrowid
            if fetch == "one":
                row = cursor.fetchone()
                return dict(row) if row else None
            elif fetch == "all":
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
            return cursor.rowcount
    finally:
        conn.close()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if IS_POSTGRES:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS guests (
                    id SERIAL PRIMARY KEY,
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
                );
                CREATE TABLE IF NOT EXISTS claim_tokens (
                    id SERIAL PRIMARY KEY,
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
                );
                CREATE TABLE IF NOT EXISTS event_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)
        else:
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
                );
            """)
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
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)

        defaults = {
            "event_name": "Izhar-e-Diwali 🌙🪔✨",
            "event_date": "Wednesday, November 11, 2026",
            "event_time": "7:00 PM Onwards",
            "event_venue": "Urban Forest Cafe and Restaurant",
            "event_location_url": "https://share.google/jryj9S1RXIgA4fnN7",
            "event_contact": "+91 63750 96687",
            "event_description": "An enchanting evening of soulful Sufi music, live poetry, acoustic melodies, and festive dining under the stars at Urban Forest Cafe!",
            "admin_pin": "urban2026"
        }

        insert_setting_sql = "INSERT INTO event_settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING" if IS_POSTGRES else "INSERT OR IGNORE INTO event_settings (key, value) VALUES (?, ?)"

        for k, v in defaults.items():
            cursor.execute(insert_setting_sql, (k, v))

        conn.commit()
    finally:
        conn.close()

def generate_unique_code(prefix: str = "IZHAR") -> str:
    chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    while True:
        suffix = "".join(random.choices(chars, k=5))
        candidate = f"{prefix}-{suffix}"
        if not execute_query("SELECT 1 FROM guests WHERE code = ?", (candidate,), fetch="one"):
            return candidate

def get_settings() -> Dict[str, str]:
    rows = execute_query("SELECT key, value FROM event_settings", fetch="all")
    return {row["key"]: row["value"] for row in rows}

def update_settings(settings: Dict[str, str]):
    sql = "INSERT INTO event_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value"
    for k, v in settings.items():
        execute_query(sql, (k, v), commit=True)

def add_guest(name: str, phone: str, email: Optional[str] = None, 
              pass_count: int = 1, pass_type: str = "General Pass", 
              notes: Optional[str] = None) -> Dict[str, Any]:
    code = generate_unique_code()
    now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    sql = """
        INSERT INTO guests (code, name, phone, email, pass_count, pass_type, notes, created_at, checked_in)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    """
    guest_id = execute_query(
        sql, 
        (code, name.strip(), phone.strip(), (email or "").strip(), max(1, pass_count), pass_type, notes, now_str),
        commit=True,
        returning_id=True
    )
    return get_guest_by_id(guest_id)

def get_guest_by_id(guest_id: int) -> Optional[Dict[str, Any]]:
    return execute_query("SELECT * FROM guests WHERE id = ?", (guest_id,), fetch="one")

def get_guest_by_code(code: str) -> Optional[Dict[str, Any]]:
    query = code.strip()
    
    # 1. Direct code match
    row = execute_query("SELECT * FROM guests WHERE UPPER(code) = UPPER(?)", (query,), fetch="one")
    
    # 2. Match without 'IZHAR-', 'SUFI-' or 'DWL-' prefix
    if not row:
        for pfx in ["IZHAR-", "SUFI-", "DWL-"]:
            if not query.upper().startswith(pfx):
                row = execute_query("SELECT * FROM guests WHERE UPPER(code) = UPPER(?)", (f"{pfx}{query}",), fetch="one")
                if row:
                    break
        
    # 3. Match by Phone Number
    if not row:
        clean_phone = "".join(filter(str.isdigit, query))
        if len(clean_phone) >= 7:
            row = execute_query("SELECT * FROM guests WHERE phone LIKE ? ORDER BY id DESC LIMIT 1", (f"%{clean_phone}%",), fetch="one")
            
    # 4. Match by Claim Token (INV-XXXXX)
    if not row:
        tok_row = execute_query("SELECT generated_pass_code FROM claim_tokens WHERE UPPER(token) = UPPER(?) AND is_used = 1", (query,), fetch="one")
        if tok_row and tok_row.get("generated_pass_code"):
            row = execute_query("SELECT * FROM guests WHERE code = ?", (tok_row["generated_pass_code"],), fetch="one")
            
    return row

def check_in_guest(code: str, checked_by: str = "Gate Staff") -> Dict[str, Any]:
    query = code.strip()
    
    # Extract code if passed as a URL
    if "/pass/" in query:
        query = query.split("/pass/").pop().split("?")[0].split("#")[0].strip()
    elif "/claim/" in query:
        query = query.split("/claim/").pop().split("?")[0].split("#")[0].strip()
        
    # 1. Direct pass code
    row = execute_query("SELECT * FROM guests WHERE UPPER(code) = UPPER(?)", (query,), fetch="one")
    
    # 2. Pass code without prefix
    if not row:
        for pfx in ["IZHAR-", "SUFI-", "DWL-"]:
            if not query.upper().startswith(pfx):
                row = execute_query("SELECT * FROM guests WHERE UPPER(code) = UPPER(?)", (f"{pfx}{query}",), fetch="one")
                if row:
                    break
        
    # 3. Match phone number
    if not row:
        clean_phone = "".join(filter(str.isdigit, query))
        if len(clean_phone) >= 7:
            row = execute_query("SELECT * FROM guests WHERE phone LIKE ? ORDER BY id DESC LIMIT 1", (f"%{clean_phone}%",), fetch="one")
            
    # 4. Match claim token
    if not row:
        tok_row = execute_query("SELECT * FROM claim_tokens WHERE UPPER(token) = UPPER(?)", (query,), fetch="one")
        if tok_row:
            if tok_row["is_used"] and tok_row.get("generated_pass_code"):
                row = execute_query("SELECT * FROM guests WHERE code = ?", (tok_row["generated_pass_code"],), fetch="one")
            else:
                # Token was never claimed by the buyer online! Auto-admit right at gate:
                now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
                gate_code = generate_unique_code()
                buyer_label = tok_row.get("buyer_note") or f"Guest ({tok_row['token']})"
                
                sql_insert = """
                    INSERT INTO guests (code, name, phone, pass_count, pass_type, notes, created_at, checked_in, checked_in_at, checked_in_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """
                new_id = execute_query(
                    sql_insert,
                    (
                        gate_code,
                        buyer_label,
                        "Verified via Token",
                        tok_row["pass_count"],
                        tok_row["pass_type"],
                        f"Admitted via Token {tok_row['token']}",
                        now_str,
                        datetime.now().strftime("%I:%M %p, %b %d"),
                        checked_by
                    ),
                    commit=True,
                    returning_id=True
                )
                
                execute_query(
                    "UPDATE claim_tokens SET is_used = 1, used_at = ?, used_by_name = ?, generated_pass_code = ? WHERE id = ?",
                    (now_str, buyer_label, gate_code, tok_row["id"]),
                    commit=True
                )
                
                new_guest = get_guest_by_id(new_id)
                return {
                    "success": True,
                    "guest": new_guest,
                    "message": f"Invite verified! Welcome {new_guest['name']} (Admit: {new_guest['pass_count']})."
                }

    # 5. Match guest name
    if not row:
        row = execute_query("SELECT * FROM guests WHERE UPPER(name) LIKE ? ORDER BY id DESC LIMIT 1", (f"%{query}%",), fetch="one")
        
    if not row:
        return {"success": False, "error": f"No guest record found for '{code}'."}
        
    guest = row
    if guest["checked_in"]:
        return {
            "success": False,
            "already_checked_in": True,
            "guest": guest,
            "error": f"Already checked in at {guest.get('checked_in_at', 'earlier')}!"
        }
        
    now_str = datetime.now().strftime("%I:%M %p, %b %d")
    execute_query(
        "UPDATE guests SET checked_in = 1, checked_in_at = ?, checked_in_by = ? WHERE id = ?",
        (now_str, checked_by, guest["id"]),
        commit=True
    )
    
    updated_guest = get_guest_by_id(guest["id"])
    return {
        "success": True,
        "guest": updated_guest,
        "message": f"Welcome {updated_guest['name']}! Pass verified."
    }

def toggle_check_in(guest_id: int) -> Optional[Dict[str, Any]]:
    guest = get_guest_by_id(guest_id)
    if not guest:
        return None
        
    new_status = 0 if guest["checked_in"] else 1
    now_str = datetime.now().strftime("%I:%M %p, %b %d") if new_status else None
    
    execute_query(
        "UPDATE guests SET checked_in = ?, checked_in_at = ?, checked_in_by = ? WHERE id = ?",
        (new_status, now_str, "Admin" if new_status else None, guest_id),
        commit=True
    )
    return get_guest_by_id(guest_id)

def delete_guest(guest_id: int) -> bool:
    count = execute_query("DELETE FROM guests WHERE id = ?", (guest_id,), commit=True)
    return count > 0

def list_guests(search: Optional[str] = None, filter_status: Optional[str] = None) -> List[Dict[str, Any]]:
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
    return execute_query(query, tuple(params), fetch="all")

def get_stats() -> Dict[str, Any]:
    row1 = execute_query("SELECT COUNT(*) AS total_registrations, COALESCE(SUM(pass_count), 0) AS total_passes FROM guests", fetch="one")
    row2 = execute_query("SELECT COUNT(*) AS checked_in_registrations, COALESCE(SUM(pass_count), 0) AS checked_in_passes FROM guests WHERE checked_in = 1", fetch="one")
    
    total_reg = row1["total_registrations"] if row1 else 0
    total_passes = row1["total_passes"] if row1 else 0
    checked_in_reg = row2["checked_in_registrations"] if row2 else 0
    checked_in_passes = row2["checked_in_passes"] if row2 else 0
    
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
    while True:
        suffix = "".join(random.choices(chars, k=6))
        token = f"INV-{suffix}"
        if not execute_query("SELECT 1 FROM claim_tokens WHERE token = ?", (token,), fetch="one"):
            break
            
    now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    sql = """
        INSERT INTO claim_tokens (token, pass_count, pass_type, buyer_note, created_at, is_used)
        VALUES (?, ?, ?, ?, ?, 0)
    """
    token_id = execute_query(sql, (token, max(1, pass_count), pass_type, buyer_note, now_str), commit=True, returning_id=True)
    return execute_query("SELECT * FROM claim_tokens WHERE id = ?", (token_id,), fetch="one")

def get_claim_token(token: str) -> Optional[Dict[str, Any]]:
    return execute_query("SELECT * FROM claim_tokens WHERE UPPER(token) = UPPER(?)", (token.strip(),), fetch="one")

def claim_token_and_create_guest(token_str: str, name: str, phone: str, 
                                 email: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
    token_data = get_claim_token(token_str)
    
    if not token_data:
        return {"success": False, "error": "Invalid invite token. Please check the link or contact the organizer."}
        
    if token_data["is_used"]:
        return {
            "success": False,
            "already_claimed": True,
            "token": token_data,
            "error": f"This link was already claimed by {token_data['used_by_name']} on {token_data['used_at']}."
        }
        
    pass_code = generate_unique_code()
    now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    # 1. Insert into guests
    sql_guest = """
        INSERT INTO guests (code, name, phone, email, pass_count, pass_type, notes, created_at, checked_in)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    """
    guest_id = execute_query(
        sql_guest,
        (
            pass_code,
            name.strip(),
            phone.strip(),
            (email or "").strip(),
            token_data["pass_count"],
            token_data["pass_type"],
            notes or token_data.get("buyer_note"),
            now_str
        ),
        commit=True,
        returning_id=True
    )
    
    # 2. Mark token as used
    execute_query(
        "UPDATE claim_tokens SET is_used = 1, used_at = ?, used_by_name = ?, used_by_phone = ?, generated_pass_code = ? WHERE id = ?",
        (now_str, name.strip(), phone.strip(), pass_code, token_data["id"]),
        commit=True
    )
    
    guest = get_guest_by_id(guest_id)
    return {
        "success": True,
        "guest": guest,
        "token": token_data
    }

def list_claim_tokens() -> List[Dict[str, Any]]:
    return execute_query("SELECT * FROM claim_tokens ORDER BY id DESC", fetch="all")

def delete_claim_token(token_id: int) -> bool:
    count = execute_query("DELETE FROM claim_tokens WHERE id = ?", (token_id,), commit=True)
    return count > 0

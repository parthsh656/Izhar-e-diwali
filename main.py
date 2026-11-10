import csv
import io
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends, Query, status
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from database import (
    init_db,
    get_settings,
    update_settings,
    add_guest,
    get_guest_by_code,
    get_guest_by_id,
    check_in_guest,
    toggle_check_in,
    delete_guest,
    list_guests,
    get_stats,
    get_connection,
    generate_claim_token,
    get_claim_token,
    claim_token_and_create_guest,
    list_claim_tokens,
    delete_claim_token
)

# Initialize Database
init_db()

app = FastAPI(title="Diwali Party Pass Portal")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# --- Pydantic Models ---
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=7)
    email: Optional[str] = None
    pass_count: int = Field(default=1, ge=1, le=20)
    pass_type: str = "General Pass"
    notes: Optional[str] = None

class CheckInRequest(BaseModel):
    code: str
    pin: Optional[str] = None

class WalkInRequest(BaseModel):
    name: str
    phone: str
    pass_count: int = 1
    pass_type: str = "General Pass"
    check_in_now: bool = True
    pin: Optional[str] = None

class SettingsUpdateRequest(BaseModel):
    event_name: str
    event_date: str
    event_time: str
    event_venue: str
    admin_pin: str
    pin: Optional[str] = None

class ClaimRequest(BaseModel):
    token: str
    name: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=7)
    notes: Optional[str] = None

class CreateTokenRequest(BaseModel):
    pass_count: int = Field(default=1, ge=1, le=20)
    pass_type: str = "General Pass"
    buyer_note: Optional[str] = None
    pin: Optional[str] = None

def verify_pin_internal(pin: Optional[str]) -> bool:
    if not pin:
        return False
    settings = get_settings()
    correct_pin = settings.get("admin_pin", "urban2026")
    return pin in (correct_pin, "urban2026", "diwali2026")

# --- Public Endpoints ---

@app.get("/claim/{token}", response_class=HTMLResponse)
async def claim_page(token: str, request: Request):
    token_data = get_claim_token(token)
    settings = get_settings()
    return templates.TemplateResponse(
        request=request,
        name="claim.html",
        context={
            "token": token_data,
            "token_found": token_data is not None,
            "settings": settings
        }
    )

@app.post("/api/claim")
async def claim_pass(data: ClaimRequest):
    result = claim_token_and_create_guest(
        token_str=data.token,
        name=data.name,
        phone=data.phone,
        notes=data.notes
    )
    return result

@app.get("/api/claim/{token}")
async def check_claim_token(token: str):
    token_data = get_claim_token(token)
    if not token_data:
        raise HTTPException(status_code=404, detail="Token not found")
    return token_data

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse(request=request, name="index.html", context={"settings": settings})

@app.post("/api/register")
async def register_guest(data: RegisterRequest):
    try:
        guest = add_guest(
            name=data.name,
            phone=data.phone,
            email=data.email,
            pass_count=data.pass_count,
            pass_type=data.pass_type,
            notes=data.notes
        )
        return {
            "success": True,
            "guest": guest,
            "pass_url": f"/pass/{guest['code']}"
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.get("/api/lookup")
async def lookup_pass(q: str = Query(...)):
    query = q.strip()
    # Check by code
    guest = get_guest_by_code(query)
    if not guest:
        # Check by phone
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM guests WHERE phone = ? ORDER BY id DESC LIMIT 1", (query,))
        row = cur.fetchone()
        conn.close()
        if row:
            guest = dict(row)
            
    if guest:
        return {"found": True, "guest": guest}
    return {"found": False}

@app.get("/pass/{code}", response_class=HTMLResponse)
async def view_pass(code: str, request: Request):
    guest = get_guest_by_code(code)
    settings = get_settings()
    if not guest:
        return HTMLResponse(
            """
            <body style="background:#0F051D;color:#F3F4F6;font-family:sans-serif;text-align:center;padding:50px;">
                <h1 style="color:#F59E0B;">🪔 Pass Not Found</h1>
                <p>No valid Diwali pass found for code <b>""" + code + """</b>.</p>
                <a href="/" style="color:#FFD700;">Back to Registration</a>
            </body>
            """,
            status_code=404
        )
    return templates.TemplateResponse(request=request, name="pass.html", context={"guest": guest, "settings": settings})

@app.get("/api/pass/{code}")
async def get_pass_json(code: str):
    guest = get_guest_by_code(code)
    if not guest:
        raise HTTPException(status_code=404, detail="Pass not found")
    return guest

# --- Admin & Gate Scanner Endpoints ---

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse(request=request, name="admin.html", context={"settings": settings})

@app.get("/api/admin/verify-pin")
async def verify_pin(pin: str = Query(...)):
    valid = verify_pin_internal(pin)
    return {"valid": valid}

@app.get("/api/admin/stats")
async def admin_stats(pin: Optional[str] = Query(None)):
    if not verify_pin_internal(pin):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return get_stats()

@app.get("/api/admin/guests")
async def admin_guests(
    pin: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    filter: Optional[str] = Query(None)
):
    if not verify_pin_internal(pin):
        raise HTTPException(status_code=401, detail="Unauthorized")
    guests = list_guests(search=search, filter_status=filter)
    return {"guests": guests}

@app.post("/api/admin/checkin")
async def admin_checkin(data: CheckInRequest):
    if not verify_pin_internal(data.pin):
        raise HTTPException(status_code=401, detail="Unauthorized")
    result = check_in_guest(data.code)
    return result

@app.post("/api/admin/toggle-checkin/{guest_id}")
async def admin_toggle(guest_id: int, pin: Optional[str] = Query(None)):
    if not verify_pin_internal(pin):
        raise HTTPException(status_code=401, detail="Unauthorized")
    updated = toggle_check_in(guest_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Guest not found")
    return {"success": True, "guest": updated}

@app.post("/api/admin/guests/walkin")
async def admin_walkin(data: WalkInRequest):
    if not verify_pin_internal(data.pin):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    guest = add_guest(
        name=data.name,
        phone=data.phone,
        pass_count=data.pass_count,
        pass_type=data.pass_type,
        notes="Walk-in Entry"
    )
    
    if data.check_in_now:
        check_in_guest(guest["code"], checked_by="Gate (Walk-in)")
        guest = get_guest_by_id(guest["id"])
        
    return {"success": True, "guest": guest}

@app.delete("/api/admin/guests/{guest_id}")
async def admin_delete_guest(guest_id: int, pin: Optional[str] = Query(None)):
    if not verify_pin_internal(pin):
        raise HTTPException(status_code=401, detail="Unauthorized")
    success = delete_guest(guest_id)
    return {"success": success}

@app.get("/api/admin/settings")
async def admin_get_settings():
    settings = get_settings()
    return settings

@app.post("/api/admin/settings")
async def admin_update_settings(data: SettingsUpdateRequest):
    if not verify_pin_internal(data.pin):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    new_settings = {
        "event_name": data.event_name,
        "event_date": data.event_date,
        "event_time": data.event_time,
        "event_venue": data.event_venue,
        "admin_pin": data.admin_pin
    }
    update_settings(new_settings)
    return {"success": True, "settings": get_settings()}

@app.get("/api/admin/export-csv")
async def export_csv(pin: Optional[str] = Query(None)):
    if not verify_pin_internal(pin):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    guests = list_guests()
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        "Pass Code", 
        "Guest Name", 
        "Phone Number", 
        "Email", 
        "Admit Count", 
        "Pass Type", 
        "Checked In", 
        "Check-in Time", 
        "Registration Date", 
        "Notes"
    ])
    
    for g in guests:
        writer.writerow([
            g["code"],
            g["name"],
            g["phone"],
            g["email"] or "",
            g["pass_count"],
            g["pass_type"],
            "YES" if g["checked_in"] else "NO",
            g["checked_in_at"] or "",
            g["created_at"],
            g["notes"] or ""
        ])
        
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=diwali_party_guestlist.csv"
        }
    )

@app.post("/api/admin/tokens")
async def admin_create_token(data: CreateTokenRequest):
    if not verify_pin_internal(data.pin):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token_row = generate_claim_token(
        pass_count=data.pass_count,
        pass_type=data.pass_type,
        buyer_note=data.buyer_note
    )
    return {"success": True, "token": token_row}

@app.get("/api/admin/tokens")
async def admin_list_tokens(pin: Optional[str] = Query(None)):
    if not verify_pin_internal(pin):
        raise HTTPException(status_code=401, detail="Unauthorized")
    tokens = list_claim_tokens()
    return {"tokens": tokens}

@app.delete("/api/admin/tokens/{token_id}")
async def admin_delete_token(token_id: int, pin: Optional[str] = Query(None)):
    if not verify_pin_internal(pin):
        raise HTTPException(status_code=401, detail="Unauthorized")
    success = delete_claim_token(token_id)
    return {"success": success}

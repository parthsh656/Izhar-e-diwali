# 🌙 Sufi Night Live - Pass & Guestlist Portal (Urban Forest Cafe) 🎶

A complete pass generation, single-use buyer link, and guestlist management system for **Sufi Night Live** at **Urban Forest Cafe and Restaurant**.

---

## 📍 Event Details
- **Event:** Sufi Night Live 🌙✨
- **Date:** Wednesday, 11th November 2026
- **Time:** 7:00 PM Onwards
- **Venue:** Urban Forest Cafe and Restaurant ([Google Maps Directions](https://share.google/jryj9S1RXIgA4fnN7))
- **Host Contact:** +91 63750 96687

---

## 🚀 How to Run

From this folder (`d:\iAssist\urban`):

```bash
python run.py
```
or with `uv`:
```bash
uv run python run.py
```

- **Public Pass Booking Link:** `http://localhost:8000`
- **Organizer Gate Scanner & Guestlist:** `http://localhost:8000/admin`
  - **Admin PIN:** `urban2026` (also accepts `diwali2026`)

---

## 🌟 Key Features
1. **Sufi Night Pass Generator (`/`):**
   - Unique pass code generation (e.g. `SUFI-9M4TK`).
   - High-resolution dynamic QR code on an emerald & gold mystic Sufi night card.
   - 1-click **Download Pass (PNG)** to mobile gallery.
   - 1-click **Share on WhatsApp**.
   - Direct clickable **Google Maps** link to Urban Forest Cafe.
   - **Find My Pass** retrieval by phone number or pass code.
2. **Single-Use Buyer Links (`/claim/{token}`):**
   - Pre-sets number of passes paid for (e.g., Couple Pass, VIP Table).
   - Once claimed, the link self-destructs to prevent forwarding abuse.
3. **Individual Pass View (`/pass/{code}`):**
   - Scannable entry pass with live active/used status.
4. **Organizer Gate Scanner (`/admin`):**
   - Live camera QR code scanner (using phone or laptop camera).
   - Instant verification with audio chimes.
   - Duplicate entry blocker (warns if a screenshot or reused pass is scanned).
   - Searchable and filterable guest records.
   - 1-click Walk-in pass issuance.
   - 1-click Export to Excel / CSV.

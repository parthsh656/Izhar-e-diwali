# 🪔 Diwali Party Pass Portal (Urban Forest Cafe)

A complete pass generation and guestlist management system for the Diwali celebration at **Urban Forest Cafe and Restaurant**.

---

## 📍 Event Details
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

- **Public Pass Registration Link:** `http://localhost:8000`
- **Organizer Gate Scanner & Guestlist:** `http://localhost:8000/admin`
  - **Admin PIN:** `diwali2026`

---

## 🌟 Key Features
1. **Pass Generator (`/`):**
   - Unique pass code generation (e.g. `DWL-W9JXQ`).
   - High-resolution dynamic QR code on an aesthetic Diwali card.
   - 1-click **Download Pass (PNG)** to mobile gallery.
   - 1-click **Share on WhatsApp**.
   - Direct clickable **Google Maps** link to Urban Forest Cafe.
   - **Find My Pass** retrieval by phone number or pass code.
2. **Individual Pass View (`/pass/{code}`):**
   - Scannable entry pass with live active/used status.
3. **Organizer Gate Scanner (`/admin`):**
   - Live camera QR code scanner (using phone or laptop camera).
   - Instant verification with audio chimes.
   - Duplicate entry blocker (warns if a screenshot or reused pass is scanned).
   - Searchable and filterable guest records.
   - 1-click Walk-in pass issuance.
   - 1-click Export to Excel / CSV.

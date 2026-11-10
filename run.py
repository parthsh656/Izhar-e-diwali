import os
import sys
from pathlib import Path

# Configure utf-8 encoding for Windows console if possible
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project directory to sys.path
project_dir = Path(__file__).resolve().parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print("\n" + "=" * 55)
    print("Sufi Night Pass Portal (Urban Forest) is starting up!")
    print("=" * 55)
    print(f"Public Pass Registration: http://localhost:{port}")
    print(f"Organizer & Gate Scanner: http://localhost:{port}/admin")
    print(f"Default Admin PIN: urban2026")
    print("=" * 55 + "\n")
    uvicorn.run("main:app", host=host, port=port, reload=True)

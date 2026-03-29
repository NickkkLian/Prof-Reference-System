"""
launcher.py — Entry point for PyInstaller bundle.
Starts Flask server and opens browser automatically.
"""

import sys
import os
import threading
import webbrowser
import time

# ── Set base path ──────────────────────────────────────────
# When frozen by PyInstaller, files are in sys._MEIPASS (temp).
# The data/ folder must sit NEXT TO the .app / .exe file.
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    # The .app file is at: MehranRosterSystem.app
    # We want data/ to be NEXT TO the .app, not inside it
    # sys.executable = .../MehranRosterSystem.app/Contents/MacOS/MehranRosterSystem
    # So we go up 3 levels to get the folder containing the .app
    app_path    = os.path.abspath(sys.executable)
    macos_dir   = os.path.dirname(app_path)          # MacOS/
    contents    = os.path.dirname(macos_dir)          # Contents/
    dot_app     = os.path.dirname(contents)           # MehranRosterSystem.app
    BUNDLE_DIR  = os.path.dirname(dot_app)            # folder containing .app
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tell the app where to find data/
os.environ['ROSTER_DATA_DIR'] = os.path.join(BUNDLE_DIR, 'data')

# Add bundle dir to path so app.py and friends can be found
sys.path.insert(0, BUNDLE_DIR)

# ── Import Flask app ────────────────────────────────────────
from app import app

# ── Port ────────────────────────────────────────────────────
PORT = 5001
URL  = f"http://127.0.0.1:{PORT}"

def open_browser():
    """Wait for Flask to start, then open professor dashboard."""
    time.sleep(1.5)
    # Read the professor token from data/prof_token.txt
    token_file = os.path.join(os.environ.get('ROSTER_DATA_DIR',
                              os.path.join(BUNDLE_DIR, 'data')), 'prof_token.txt')
    try:
        with open(token_file) as f:
            token = f.read().strip()
        webbrowser.open(f"{URL}/prof/{token}")
    except Exception:
        webbrowser.open(URL)  # fallback to student page

def main():
    print("=" * 50)
    print("  Mehran's Roster System")
    print(f"  Opening at {URL}")
    print("  Close this window to stop the app.")
    print("=" * 50)

    threading.Thread(target=open_browser, daemon=True).start()

    app.run(
        host="127.0.0.1",
        port=PORT,
        debug=False,
        use_reloader=False,
    )

if __name__ == "__main__":
    main()

import os, secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# When running as PyInstaller bundle, data dir is set by launcher.py
# Otherwise default to data/ next to this file
DATA_DIR = os.environ.get('ROSTER_DATA_DIR',
                           os.path.join(BASE_DIR, 'data'))

# ── Eligibility thresholds ───────────────────────────────────
MIN_GRADE_PERCENT:      float = 80.0
MIN_ATTENDANCE_PERCENT: float = 75.0

# ── Paths ────────────────────────────────────────────────────
ATTENDANCE_INPUT_DIR  = os.path.join(DATA_DIR, 'attendance_input')
DB_PATH               = os.path.join(DATA_DIR, 'professor_reference.db')
TRANSCRIPT_UPLOAD_DIR = os.path.join(DATA_DIR, 'uploads', 'transcripts')
LETTER_UPLOAD_DIR     = os.path.join(DATA_DIR, 'uploads', 'letters')

ALLOWED_TRANSCRIPT_EXT = {'.pdf'}
ALLOWED_LETTER_EXT     = {'.pdf'}

# ── Email notification settings ──────────────────────────────
# Loaded at runtime from data/email_settings.txt
# ── Email notification settings ──────────────────────────────
NOTIFY_EMAIL  = ""   # where to receive notifications (can be any email)
SENDER_EMAIL  = ""   # verified sender email in Brevo (set once, never changes)
BREVO_API_KEY = ""   # from brevo.com → Settings → API Keys

_email_file = os.path.join(DATA_DIR, 'email_settings.txt')

def load_email_settings():
    global NOTIFY_EMAIL, SENDER_EMAIL, BREVO_API_KEY
    if os.path.exists(_email_file):
        try:
            lines = open(_email_file).read().splitlines()
            NOTIFY_EMAIL  = lines[0].strip() if len(lines) > 0 else ""
            BREVO_API_KEY = lines[1].strip() if len(lines) > 1 else ""
            SENDER_EMAIL  = lines[2].strip() if len(lines) > 2 else lines[0].strip()
        except Exception:
            pass

def save_email_settings(notify_email: str, brevo_api_key: str, sender_email: str = ""):
    global NOTIFY_EMAIL, SENDER_EMAIL, BREVO_API_KEY
    NOTIFY_EMAIL  = notify_email
    BREVO_API_KEY = brevo_api_key
    # Sender stays as the first email ever entered (verified by Brevo)
    # Only update sender if explicitly provided or if it's not set yet
    if sender_email:
        SENDER_EMAIL = sender_email
    elif not SENDER_EMAIL:
        SENDER_EMAIL = notify_email
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(_email_file, 'w') as f:
        f.write(f"{NOTIFY_EMAIL}\n{BREVO_API_KEY}\n{SENDER_EMAIL}\n")

# ── Secret professor token ───────────────────────────────────
_token_file = os.path.join(DATA_DIR, 'prof_token.txt')

def get_prof_token() -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(_token_file):
        return open(_token_file).read().strip()
    token = secrets.token_urlsafe(24)
    with open(_token_file, 'w') as f:
        f.write(token)
    return token


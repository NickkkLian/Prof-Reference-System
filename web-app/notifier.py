"""
notifier.py
-----------
Sends email notifications via Brevo (formerly Sendinblue) API.
No SMTP setup, no app passwords — just a free Brevo API key.

Setup:
  1. Sign up free at brevo.com
  2. Go to Settings → SMTP & API → API Keys → Create API key
  3. Paste the key into the Settings page
"""

import urllib.request, urllib.error, json
import config


def _send(subject: str, body: str) -> tuple[bool, str]:
    config.load_email_settings()

    if not config.NOTIFY_EMAIL:
        return False, "No notification email configured"
    if not config.BREVO_API_KEY:
        return False, "Brevo API key not configured"

    # Always send FROM the verified sender email, TO the notification email
    sender = config.SENDER_EMAIL if config.SENDER_EMAIL else config.NOTIFY_EMAIL

    payload = json.dumps({
        "sender":      {"name": "Mehran's Roster System", "email": sender},
        "to":          [{"email": config.NOTIFY_EMAIL}],
        "subject":     subject,
        "textContent": body.strip(),
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=payload,
        headers={
            "Content-Type":  "application/json",
            "api-key":       config.BREVO_API_KEY,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 201):
                return True, "Notification sent"
            return False, f"Brevo returned status {resp.status}"
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode())
            return False, f"Brevo error {e.code}: {detail.get('message', str(detail))}"
        except Exception:
            return False, f"Brevo HTTP error {e.code}: {e.reason}"
    except Exception as e:
        return False, f"Request error: {e}"


def send_submission_notification(student_number: str, student_name: str,
                                  trans_fname: str,
                                  letter_fname: str) -> tuple[bool, str]:
    subject = f"New Submission: Student {student_number}"
    body = f"""A student has submitted their documents for reference letter consideration.

Student Number : {student_number}
Student Name   : {student_name or 'N/A'}
Transcript     : {trans_fname or 'Not provided'}
Letter         : {letter_fname or 'Not provided'}

You can view all submissions in your dashboard."""
    return _send(subject, body)


def test_email() -> tuple[bool, str]:
    config.load_email_settings()
    if not config.NOTIFY_EMAIL:
        return False, "Please enter a notification email first"
    if not config.BREVO_API_KEY:
        return False, "Please enter your Brevo API key first"
    ok, msg = _send(
        subject="Test — Mehran's Roster System",
        body="This is a test email from Mehran's Roster System.\n"
             "If you received this, email notifications are working correctly."
    )
    if ok:
        return True, f"Test email sent successfully to {config.NOTIFY_EMAIL}"
    return False, msg

# Prof Reference System — Web App

Flask web application for server-side deployment. Designed to be hosted on an institutional server (e.g. university IT infrastructure) to ensure FIPPA compliance.

## Setup

```bash
cd web-app
pip install -r requirements.txt
python3 create_sample_data.py
python3 app.py
```

URLs printed on startup:
```
Professor dashboard: http://localhost:5000/prof/<your-token>
Student portal:      http://localhost:5000
```

## Production Deployment

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Roster File Format

Excel files (`.xlsx`) with these columns (case-insensitive, any order):

| Column | Required | Accepted Names |
|---|---|---|
| Student Number | ✅ | Student #, Student No, ID |
| First Name | ✅ | First Name, First, Given Name |
| Last Name | ✅ | Last Name, Last, Surname |
| Attendance % | ✅ | Abs, %Abs, Absence Rate |
| Grade | Optional | Grade, Final Grade, Mark, Score |

Course, Section, Year, and Term are entered in the Import form.

## Email Notifications

Uses [Brevo](https://www.brevo.com) API (free, 300 emails/day). Configure in professor Settings page.

## Prerequisites

- Python 3.10+
- For OCR (optional): `brew install tesseract` (Mac) or [Tesseract Windows installer](https://github.com/UB-Mannheim/tesseract/wiki)

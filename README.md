# Prof Reference System

A full-stack web application that automates student eligibility screening for professor reference letters. Built with Python/Flask, SQLite, and a custom HTML/CSS frontend.

This repository contains two versions of the same application, demonstrating different deployment approaches:

| Version | Folder | Best For |
|---|---|---|
| **Web App** | `web-app/` | Institutional server hosting (e.g. university IT infrastructure) |
| **Desktop App** | `desktop-app/` | Local use — runs on your own computer, all data stays local |

---

## Features

### Student Portal
- Enter student number to check eligibility
- Automatic eligibility check against imported roster
- Consent acknowledgement before submission
- Upload letter of interest (PDF)
- Automatic email notification sent to professor on submission

### Professor Dashboard
- **Roster Management** — Import Excel roster files per course/section/term
- **Eligibility Check** — Inline check by student number with grade auto-filled from database
- **Eligible Students List** — Pending and completed sections with reference done checkbox
- **Documents** — View, download, and delete submitted letters side by side
- **Settings** — Adjustable grade and attendance thresholds; email notification configuration
- **Dark Mode** — Black/orange theme, persisted across sessions

### Eligibility Logic
All three criteria must pass:
1. Student number found in the imported roster database
2. Overall grade ≥ minimum grade threshold (default 80%)
3. Attendance ≥ minimum attendance threshold (default 75%) across all enrolments

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Flask |
| Database | SQLite |
| Frontend | HTML, CSS, Jinja2 |
| Excel parsing | openpyxl |
| Email | Brevo API |
| Desktop packaging | PyInstaller |

---

## Privacy Considerations

This system handles student personal information. Deployment must comply with applicable privacy legislation (e.g. BC FIPPA).

- **Web App version** — intended for institutional server hosting on Canadian infrastructure
- **Desktop App version** — all data stays on the local computer; fully privacy compliant

---

## Quick Start

See the README inside each subfolder:
- [`web-app/README.md`](web-app/README.md)
- [`desktop-app/README.md`](desktop-app/README.md)

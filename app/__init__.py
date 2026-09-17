"""Letterkeep — reference-letter eligibility for one course.

One package, two entry points: run_web.py (a server) and run_desktop.py (the professor's own machine). Until
2026-09-17 the repository carried this code twice, as web-app/ and desktop-app/, byte for byte identical apart from
the launcher and the packaging spec.

  config              paths, thresholds, the app name, the professor token
  database            SQLite schema and queries
  attendance_manager  roster (.xlsx) import
  transcript_parser   grade extraction from a transcript PDF (OCR is optional, see the README)
  eligibility         the rule: on the roster, grade >= threshold, attendance >= threshold in every enrolment
  notifier            e-mail notification through Brevo (no key configured = nothing is sent)
  seed                demo data: 15 students in 2 courses
  web                 the Flask application (student page + professor pages)
"""

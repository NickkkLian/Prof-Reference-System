"""Every test runs against its own empty data folder: the tests must never touch a real roster, and one test's
enrolments must not decide another's. ROSTER_DATA_DIR is set before app.config is imported, because config reads it
once to build the paths; the paths are then repointed per test and the database file is created fresh."""
import importlib
import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("ROSTER_DATA_DIR", tempfile.mkdtemp(prefix="letterkeep-tests-"))


@pytest.fixture()
def data_dir(tmp_path, monkeypatch):
    """An empty data folder for one test, with the package's paths pointing into it."""
    from app import config, database as db

    for name, value in {
        "DATA_DIR": tmp_path,
        "ATTENDANCE_INPUT_DIR": tmp_path / "attendance_input",
        "DB_PATH": tmp_path / "letterkeep.db",
        "TRANSCRIPT_UPLOAD_DIR": tmp_path / "uploads" / "transcripts",
        "LETTER_UPLOAD_DIR": tmp_path / "uploads" / "letters",
    }.items():
        monkeypatch.setattr(config, name, str(value))
    for d in ("ATTENDANCE_INPUT_DIR", "TRANSCRIPT_UPLOAD_DIR", "LETTER_UPLOAD_DIR"):
        os.makedirs(getattr(config, d), exist_ok=True)

    importlib.reload(db) if False else None          # the modules read config at call time; no reload needed
    db.init_db()
    return tmp_path


@pytest.fixture()
def enrol(data_dir):
    """add(student, course, attendance_pct, grade) — one enrolment row, the way the roster import writes it."""
    from app import database as db

    def add(student_number: str, course: str, attendance_pct: float, grade=None, name="Test Student"):
        first, _, last = name.partition(" ")
        db.upsert_enrolment({
            "identifier": f"{course.replace(' ', '')}_101_2025_W1_{student_number}",
            "course": course, "section": "101", "year": "2025", "term": "W1",
            "student_number": student_number, "student_name": name,
            "first_name": first, "last_name": last,
            "absence_rate_pct": None if attendance_pct is None else round(100 - attendance_pct, 4),
            "attendance_rate_pct": attendance_pct, "grade": grade,
            "source_file": "test.xlsx",
        })
    return add

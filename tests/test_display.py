"""Pin permanent B.C. time and shared file-size labels at their visible call sites."""

from datetime import datetime, timedelta
import io
import os
from pathlib import Path

from flask import template_rendered
import pytest

from app import config, database as db, display


def freeze_clock(monkeypatch, utc):
    clock = {"now": datetime.fromisoformat(utc)}

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            assert tz is not None, "Vancouver time must not depend on the host zone"
            return clock["now"].astimezone(tz)

    monkeypatch.setattr(display, "datetime", FrozenDatetime)
    return clock


@pytest.mark.parametrize("utc, expected", [
    ("2026-10-31T23:59:00+00:00", "2026-10-31 16:59"),
    ("2026-11-01T08:59:00+00:00", "2026-11-01 01:59"),
    ("2026-11-01T09:00:00+00:00", "2026-11-01 02:00"),
    ("2026-11-05T08:05:00+00:00", "2026-11-05 01:05"),
    ("2027-01-15T06:05:00+00:00", "2027-01-14 23:05"),
    ("2027-03-14T10:00:00+00:00", "2027-03-14 03:00"),
    ("2027-11-07T09:00:00+00:00", "2027-11-07 02:00"),
])
def test_vancouver_stays_at_utc_minus_seven_across_old_dst_boundaries(monkeypatch, utc, expected):
    clock = freeze_clock(monkeypatch, utc)
    for value in (display.vancouver_time(), display.vancouver_time(clock["now"].timestamp())):
        assert value.utcoffset() == timedelta(hours=-7)
        assert value.strftime("%Y-%m-%d %H:%M") == expected


@pytest.mark.parametrize("size, expected", [
    (0, "0 B"), (30, "30 B"), (1023, "1023 B"), (1024, "1.0 KB"),
    (1536, "1.5 KB"), (1024**2, "1.0 MB"), (3 * 1024**2 // 2, "1.5 MB"),
])
def test_file_size_units(size, expected):
    assert display.format_file_size(size) == expected


@pytest.mark.parametrize("utc, expected", [
    ("2026-11-01T08:59:00+00:00", "2026-11-01 01:59"),
    ("2026-11-01T09:00:00+00:00", "2026-11-01 02:00"),
    ("2026-11-05T08:05:00+00:00", "2026-11-05 01:05"),
    ("2027-01-15T06:05:00+00:00", "2027-01-14 23:05"),
])
def test_all_visible_times_and_file_sizes_agree(data_dir, enrol, monkeypatch, utc, expected):
    from app import web

    monkeypatch.setattr(config, "MIN_GRADE_PERCENT", 80)
    monkeypatch.setattr(config, "MIN_ATTENDANCE_PERCENT", 75)
    monkeypatch.setattr(web, "send_submission_notification", lambda **kwargs: None)
    clock = freeze_clock(monkeypatch, utc)
    instant = clock["now"]
    clock["now"] -= timedelta(hours=1)
    enrol("10001009", "DEMO 310", attendance_pct=94, grade=None)
    assert db.get_all_enrolments()[0]["updated_at"] == (
        datetime.fromisoformat(expected) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    clock["now"] = instant
    record = db.get_all_enrolments()[0]
    record["grade"] = 87
    db.upsert_enrolment(record)
    assert db.get_all_enrolments()[0]["updated_at"] == expected
    Path(config.ATTENDANCE_INPUT_DIR, "test.xlsx").write_bytes(b"x" * 30)
    pdf = b"%PDF-1.4\n" + b" " * 15 + b"%%EOF\n"
    assert len(pdf) == 30
    rendered = {}

    def capture(sender, template, context, **extra):
        rendered[template.name] = context

    web.app.config.update(TESTING=True)
    with template_rendered.connected_to(capture, web.app), web.app.test_client() as client:
        result = client.post("/check", data={
            "student_number": "10001009", "consent": "on",
            "transcript": (io.BytesIO(pdf), "10001009_transcript.pdf"),
            "letter": (io.BytesIO(pdf), "10001009_letter.pdf"),
        })
        assert result.status_code == 200
        assert rendered["student_result.html"]["checked_at"] == expected
        assert expected in result.get_data(as_text=True)
        assert db.get_all_eligible()[0]["checked_at"] == expected
        assert db.toggle_reference_done("10001009") is True
        assert db.get_all_eligible()[0]["reference_done_at"] == expected
        for directory in (config.TRANSCRIPT_UPLOAD_DIR, config.LETTER_UPLOAD_DIR,
                          config.ATTENDANCE_INPUT_DIR):
            for file in Path(directory).iterdir():
                os.utime(file, (instant.timestamp(), instant.timestamp()))
        prefix = f"/prof/{web.PROF_TOKEN}"
        for suffix in ("", "/eligible", "/documents", "/files"):
            response = client.get(prefix + suffix)
            assert response.status_code == 200
            assert expected in response.get_data(as_text=True)

    dashboard = rendered["prof_dashboard.html"]
    assert dashboard["recent"][0]["checked_at"] == expected
    for key in ("transcripts", "letters", "rosters"):
        assert dashboard["storage"][key] == "30 B"
    assert rendered["prof_eligible.html"]["rows"][0]["checked_at"] == expected
    documents = rendered["prof_documents.html"]
    for file in documents["letters"] + documents["transcripts"]:
        assert file["modified"] == expected
        assert file["size"] == "30 B"
    roster = rendered["prof_files.html"]
    assert roster["disk_files"][0]["modified"] == expected
    assert roster["disk_files"][0]["size"] == "30 B"
    assert roster["db_files"]["test.xlsx"]["last_updated"] == expected


def test_one_submission_keeps_one_timestamp_even_if_notification_is_delayed(data_dir, enrol, monkeypatch):
    from app import web

    clock = freeze_clock(monkeypatch, "2026-11-05T08:05:00+00:00")
    monkeypatch.setattr(config, "MIN_GRADE_PERCENT", 80)
    monkeypatch.setattr(config, "MIN_ATTENDANCE_PERCENT", 75)
    enrol("10001009", "DEMO 310", attendance_pct=94, grade=87)

    def delayed_notification(**kwargs):
        clock["now"] += timedelta(minutes=2)

    monkeypatch.setattr(web, "send_submission_notification", delayed_notification)
    with web.app.test_request_context("/check"):
        result = web._run_eligibility("10001009", 87, "database", "", "", "")
    assert "2026-11-05 01:05" in result
    assert "2026-11-05 01:07" not in result
    assert db.get_all_eligible()[0]["checked_at"] == "2026-11-05 01:05"

"""What the pages give away. The student's result page can be opened by anyone who knows a student number, so it shows
the answer and which condition is met, but no name, enrolment or figure from the roster; a grade appears only when the
student supplied it. The professor's settings page never puts the saved Brevo key into the HTML."""
import io
import re

import pytest


@pytest.fixture()
def client(data_dir):
    from app import web
    web.app.config.update(TESTING=True)
    return web.app.test_client()


def submit(client, student_number):
    pdf = b"%PDF-1.4\n%%EOF\n"   # the files are stored, not read, when the grade is already in the course records
    return client.post("/check", content_type="multipart/form-data", data={
        "student_number": student_number, "consent": "on",
        "transcript": (io.BytesIO(pdf), f"{student_number}_transcript.pdf"),
        "letter": (io.BytesIO(pdf), f"{student_number}_letter.pdf"),
    })


def short_conditions(html):
    """The first word of every condition the page marks as not met."""
    return re.findall(r'<li class="short">\s*<span>(\w+)', html)


def test_a_qualifying_student_sees_the_answer_and_nothing_from_the_roster(client, enrol):
    enrol("10000101", "DEMO 310", attendance_pct=96.0, grade=88.5, name="Alice Example")
    html = submit(client, "10000101").get_data(as_text=True)
    assert "You qualify for a reference letter." in html
    assert short_conditions(html) == []
    for roster_detail in ("Alice", "Example", "88.5", "96.0", "DEMO310", "DEMO 310"):
        assert roster_detail not in html, roster_detail


def test_the_short_condition_is_named_without_its_figure(client, enrol):
    enrol("10000102", "DEMO 310", attendance_pct=96.0, grade=88.5, name="Bob Example")
    enrol("10000102", "DEMO 320", attendance_pct=61.5, grade=88.5, name="Bob Example")
    html = submit(client, "10000102").get_data(as_text=True)
    assert "You do not qualify yet." in html
    assert short_conditions(html) == ["Attendance"]
    for roster_detail in ("Bob", "61.5", "96.0", "88.5", "DEMO320", "DEMO 320"):
        assert roster_detail not in html, roster_detail


def test_a_number_not_on_the_roster_says_so_and_nothing_else(client, data_dir):
    html = submit(client, "10000999")
    # no grade in the records and none in a blank PDF: the student is asked to type it
    assert "The transcript did not give up a grade" in html.get_data(as_text=True)
    html = client.post("/check/manual-grade", data={"student_number": "10000999", "manual_grade": "91",
                                                    "trans_fname": "", "letter_fname": ""}).get_data(as_text=True)
    assert short_conditions(html) == ["On", "Attendance"]
    assert "91.0%, as you entered it" in html   # the figure the student supplied is theirs to see


def test_the_settings_page_never_contains_the_saved_brevo_key(client, monkeypatch):
    from app import config, web
    monkeypatch.setattr(config, "load_email_settings", lambda: None)
    monkeypatch.setattr(config, "BREVO_API_KEY", "xkeysib-test-0123456789abcdef")
    monkeypatch.setattr(config, "NOTIFY_EMAIL", "prof@example.com")
    html = client.get(f"/prof/{web.PROF_TOKEN}/settings").get_data(as_text=True)
    assert "xkeysib-test-0123456789abcdef" not in html
    assert "a key is saved" in html

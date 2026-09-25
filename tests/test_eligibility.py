"""The rule, as the professor stated it: a student is eligible when they are on the roster, their grade reaches the
grade threshold, and their attendance reaches the attendance threshold **in every enrolment** — one course short is
not eligible. The thresholds themselves are settings; these tests pin the rule, not the numbers."""
import pytest

from app import config, eligibility


@pytest.fixture(autouse=True)
def thresholds(monkeypatch):
    monkeypatch.setattr(config, "MIN_GRADE_PERCENT", 80.0)
    monkeypatch.setattr(config, "MIN_ATTENDANCE_PERCENT", 75.0)


def test_not_on_the_roster_is_never_eligible(data_dir):
    r = eligibility.check("99999999", grade=95.0)
    assert r["in_db"] is False and r["eligible"] is False
    assert r["identifiers"] == []


@pytest.mark.parametrize("grade, expected", [(95.0, True), (80.0, True), (79.9, False), (None, False)])
def test_grade_against_the_threshold(enrol, grade, expected):
    enrol("10000001", "DEMO 310", attendance_pct=90.0, grade=grade)
    r = eligibility.check("10000001", grade=grade)
    assert r["grade_ok"] is expected
    assert r["eligible"] is expected


@pytest.mark.parametrize("attendance, expected", [(100.0, True), (75.0, True), (74.9, False)])
def test_attendance_against_the_threshold(enrol, attendance, expected):
    enrol("10000002", "DEMO 310", attendance_pct=attendance, grade=88.0)
    r = eligibility.check("10000002", grade=88.0)
    assert r["att_ok"] is expected
    assert r["eligible"] is expected


def test_every_enrolment_has_to_pass_attendance(enrol):
    """Two courses, one of them short: not eligible. This is the case the rule exists for."""
    enrol("10000003", "DEMO 310", attendance_pct=96.0, grade=91.0)
    enrol("10000003", "DEMO 320", attendance_pct=60.0, grade=91.0)
    r = eligibility.check("10000003", grade=91.0)
    assert len(r["identifiers"]) == 2
    assert len(r["passing_ids"]) == 1
    assert r["att_ok"] is False and r["eligible"] is False


def test_all_enrolments_passing_is_eligible(enrol):
    enrol("10000004", "DEMO 310", attendance_pct=96.0, grade=91.0)
    enrol("10000004", "DEMO 320", attendance_pct=88.0, grade=91.0)
    r = eligibility.check("10000004", grade=91.0)
    assert r["passing_ids"] == r["identifiers"] and r["eligible"] is True


def test_missing_attendance_is_not_a_pass(enrol):
    """A row with no attendance figure must not count as meeting the threshold."""
    enrol("10000005", "DEMO 310", attendance_pct=None, grade=91.0)
    r = eligibility.check("10000005", grade=91.0)
    assert r["att_results"] == {"DEMO310_101_2025_Fall_10000005": None}
    assert r["att_ok"] is False and r["eligible"] is False


def test_the_result_carries_the_thresholds_it_used(enrol):
    enrol("10000006", "DEMO 310", attendance_pct=96.0, grade=91.0)
    r = eligibility.check("10000006", grade=91.0, grade_source="transcript")
    assert (r["min_grade"], r["min_att"]) == (80.0, 75.0)
    assert r["grade_source"] == "transcript"
    assert r["student_name"] == "Test Student"

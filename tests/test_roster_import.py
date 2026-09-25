"""Roster files come out of different systems. The README promises a set of spellings for each column; these tests
hold the parser to that promise, and pin the two conversions a reader would otherwise have to guess: an absence
figure may arrive as a fraction (0.02) or as a percentage (2), and attendance is 100 minus absence."""
import openpyxl
import pytest

from app import attendance_manager as am


def roster(path, headers, rows, sheet="Roster"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(headers)
    for r in rows:
        ws.append(r)
    wb.save(path)
    return str(path)


SPELLINGS = [
    (["Student #", "First Name", "Last Name", "%Abs", "Grade"], "the sample roster's own header"),
    (["Student No", "First", "Surname", "Absence Rate", "Final Grade"], "a registrar-style export"),
    (["ID", "Given Name", "Last", "Abs%", "Mark"], "a short header"),
]


@pytest.mark.parametrize("headers, what", SPELLINGS, ids=[s[1] for s in SPELLINGS])
def test_the_documented_spellings_all_parse(tmp_path, data_dir, headers, what):
    path = roster(tmp_path / "r.xlsx", headers, [["10000001", "Alice", "Chen", 0.04, 88.5]])
    records = am.parse_roster_file(path, course="DEMO 310", section="101", year="2025", term="Fall")
    assert len(records) == 1, what
    r = records[0]
    assert r["student_number"] == "10000001"
    assert r["student_name"] == "Alice Chen"
    assert r["grade"] == 88.5
    assert r["attendance_rate_pct"] == pytest.approx(96.0)


def test_absence_as_a_percentage_and_as_a_fraction_mean_the_same(tmp_path, data_dir):
    a = roster(tmp_path / "frac.xlsx", ["Student #", "First Name", "Last Name", "%Abs"], [["1", "A", "B", 0.04]])
    b = roster(tmp_path / "pct.xlsx", ["Student #", "First Name", "Last Name", "%Abs"], [["1", "A", "B", 4]])
    meta = dict(course="DEMO 310", section="101", year="2025", term="Fall")
    assert (am.parse_roster_file(a, **meta)[0]["attendance_rate_pct"]
            == pytest.approx(am.parse_roster_file(b, **meta)[0]["attendance_rate_pct"])
            == pytest.approx(96.0))


def test_a_missing_required_column_is_refused_by_name(tmp_path, data_dir):
    path = roster(tmp_path / "no-abs.xlsx", ["Student #", "First Name", "Last Name"], [["1", "A", "B"]])
    with pytest.raises(ValueError) as e:
        am.parse_roster_file(path, course="DEMO 310", section="101", year="2025", term="Fall")
    assert "%abs" in str(e.value)


def test_rows_without_a_student_number_are_skipped(tmp_path, data_dir):
    path = roster(tmp_path / "gaps.xlsx", ["Student #", "First Name", "Last Name", "%Abs"],
                  [["10000001", "Alice", "Chen", 0.0], [None, "", "", None], ["10000002", "Bo", "Li", 0.5]])
    records = am.parse_roster_file(path, course="DEMO 310", section="101", year="2025", term="Fall")
    assert [r["student_number"] for r in records] == ["10000001", "10000002"]


def test_the_import_writes_what_the_rule_reads(tmp_path, data_dir):
    """End to end: a file on disk becomes enrolments the eligibility rule can answer from."""
    from app import database as db, eligibility

    path = roster(tmp_path / "class.xlsx", ["Student #", "First Name", "Last Name", "%Abs", "Grade"],
                  [["10000001", "Alice", "Chen", 0.04, 88.5], ["10000002", "Bo", "Li", 0.40, 91.0]])
    am.import_file(path, course="DEMO 310", section="101", year="2025", term="Fall", verbose=False)

    assert db.count_enrolments() == 2
    good = eligibility.check("10000001", grade=88.5)
    short = eligibility.check("10000002", grade=91.0)
    assert good["eligible"] is True
    assert short["att_ok"] is False and short["eligible"] is False      # 60% attendance

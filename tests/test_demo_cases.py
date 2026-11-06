"""The public cases must make the same decisions as the actual local rule."""
import json
import subprocess
from pathlib import Path

import pytest

from app import config, eligibility

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "docs/cases.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_public_case_matches_local_rule(enrol, monkeypatch, case):
    monkeypatch.setattr(config, "MIN_GRADE_PERCENT", 80)
    monkeypatch.setattr(config, "MIN_ATTENDANCE_PERCENT", 75)
    for course in case["enrolments"]:
        enrol(case["number"], course["course"], course["attendance"], case["grade"], case["name"])
    actual = eligibility.check(case["number"], case["grade"], case["grade_source"])
    browser = json.loads(subprocess.check_output(
        ["node", "-e", "const rule=require('./docs/eligibility.js'); console.log(JSON.stringify(rule.check(JSON.parse(process.argv[1]))))", json.dumps(case)],
        cwd=ROOT, text=True))
    assert browser == dict(inRoster=actual["in_db"], gradeOK=actual["grade_ok"],
                           attendanceOK=actual["att_ok"], eligible=actual["eligible"])
    assert browser["eligible"] is case["expected"]
    assert actual["grade_source"] == case["grade_source"]


@pytest.mark.parametrize("grade,attendance,expected", [(80,75,True),(79.9,75,False),(80,74.9,False),(None,90,False),(90,None,False)])
def test_browser_rule_keeps_boundary_and_missing_data(grade, attendance, expected):
    case = dict(grade=grade, enrolments=[dict(attendance=attendance)])
    result = json.loads(subprocess.check_output(
        ["node", "-e", "console.log(JSON.stringify(require('./docs/eligibility.js').check(JSON.parse(process.argv[1]))))", json.dumps(case)],
        cwd=ROOT, text=True))
    assert result["eligible"] is expected

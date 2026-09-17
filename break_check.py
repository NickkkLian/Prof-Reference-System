#!/usr/bin/env python3
"""break_check.py — break the rule on purpose and require the tests to catch it.

    python3 break_check.py          exits 0 only if every break below is caught by the test that should catch it

A green test suite only means something if it can go red. Each break is applied to a copy of the code in a temporary
folder — the repository is never touched — and it is "caught" only when **the named test** fails: a break that turns
the whole suite red for some unrelated reason (a dependency that moved, a typo in the copy) is reported as not caught,
because then the test that was supposed to notice never got the chance.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

BREAKS = [
    ("attendance: one course short is good enough",
     "app/eligibility.py",
     "att_ok   = len(identifiers) > 0 and len(passing) == len(identifiers)",
     "att_ok   = len(identifiers) > 0 and len(passing) > 0",
     "test_every_enrolment_has_to_pass_attendance"),
    ("grade: any grade at all passes",
     "app/eligibility.py",
     "grade_ok = grade is not None and grade >= config.MIN_GRADE_PERCENT",
     "grade_ok = grade is not None",
     "test_grade_against_the_threshold"),
    ("attendance: a row with no figure counts as a pass",
     "app/eligibility.py",
     "if r is not None and r >= config.MIN_ATTENDANCE_PERCENT]",
     "if r is None or r >= config.MIN_ATTENDANCE_PERCENT]",
     "test_missing_attendance_is_not_a_pass"),
    ("roster: only this file's own spelling of the headers is accepted",
     "app/attendance_manager.py",
     '        found = next((h for h in raw if h in names), None)',
     '        found = None',
     "test_the_documented_spellings_all_parse"),
    ("notifier: sends even when nothing is configured",
     "app/notifier.py",
     '    if not config.NOTIFY_EMAIL:\n        return False, "No notification email configured"',
     '    if False:\n        return False, "No notification email configured"',
     "test_no_address_configured_sends_nothing"),
]


def run_tests(root: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests", "-p", "no:cacheprovider", "-q"],
                       cwd=root, capture_output=True, text=True, timeout=600)
    return r.returncode, r.stdout + r.stderr


def failing_tests(output: str) -> set[str]:
    return set(re.findall(r"^FAILED tests/\S+::(\w+)", output, re.M))


def main() -> int:
    print("Baseline: the tests as they are.")
    code, out = run_tests(HERE)
    print("  " + out.strip().splitlines()[-1])
    if code != 0:
        print("RESULT: the tests are not green to begin with — fix that before breaking anything.")
        return 1

    caught = []
    for name, rel, before, after, expect in BREAKS:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "copy"
            shutil.copytree(HERE, root, ignore=shutil.ignore_patterns(
                "__pycache__", ".git", ".pytest_cache", "data", "*.egg-info"))
            target = root / rel
            source = target.read_text(encoding="utf-8")
            if source.count(before) != 1:
                print(f"NOT APPLIED  {name} — the line it edits is not in {rel} exactly once "
                      f"({source.count(before)} matches)")
                caught.append(False)
                continue
            target.write_text(source.replace(before, after), encoding="utf-8")
            code, out = run_tests(root)
            failed = failing_tests(out)
            ok = code != 0 and expect in failed
            print(f"{'CAUGHT     ' if ok else 'NOT CAUGHT '} {name}\n"
                  f"             expected {expect} to fail; failing tests: {sorted(failed) or 'none'}")
            caught.append(ok)

    n = sum(caught)
    print(f"RESULT: {n}/{len(BREAKS)} breaks caught by the test that should catch them")
    return 0 if all(caught) else 1


if __name__ == "__main__":
    sys.exit(main())

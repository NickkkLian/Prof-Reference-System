"""
eligibility.py
--------------
Core eligibility logic.

Grade priority is resolved BEFORE this function is called (in app.py):
  1. DB grade
  2. Transcript extraction
  3. Manual entry
The grade_source parameter records which method was used.
"""

import config, database as db

def check(student_number: str, grade=None, grade_source="submitted"):
    identifiers  = db.get_identifiers_by_student(student_number)
    student_name = db.get_student_name(student_number) or student_number

    in_db    = len(identifiers) > 0
    grade_ok = grade is not None and grade >= config.MIN_GRADE_PERCENT

    att_results = {iid: db.get_attendance_rate(iid) for iid in identifiers}
    passing     = [iid for iid, r in att_results.items()
                   if r is not None and r >= config.MIN_ATTENDANCE_PERCENT]

    # ALL enrolments must meet attendance threshold
    att_ok   = len(identifiers) > 0 and len(passing) == len(identifiers)
    eligible = in_db and grade_ok and att_ok

    result = dict(
        student_number=student_number,
        student_name=student_name,
        grade=grade,
        grade_source=grade_source,
        identifiers=identifiers,
        att_results=att_results,
        in_db=in_db,
        grade_ok=grade_ok,
        att_ok=att_ok,
        passing_ids=passing,
        eligible=eligible,
        min_grade=config.MIN_GRADE_PERCENT,
        min_att=config.MIN_ATTENDANCE_PERCENT,
    )
    return result

/* Browser counterpart of app/eligibility.py; parity is tested with cases.json. */
(function (root) {
  function check(student, minGrade = 80, minAttendance = 75) {
    const inRoster = student.enrolments.length > 0;
    const gradeOK = student.grade !== null && student.grade >= minGrade;
    const attendanceOK = inRoster && student.enrolments.every(e => e.attendance !== null && e.attendance >= minAttendance);
    return { inRoster, gradeOK, attendanceOK, eligible: inRoster && gradeOK && attendanceOK };
  }
  if (typeof module !== 'undefined') module.exports = { check };
  else root.LetterkeepEligibility = { check };
})(typeof window === 'undefined' ? globalThis : window);

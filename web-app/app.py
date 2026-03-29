"""
app.py  —  Professor Reference Letter System
Flask web application — student portal + professor dashboard
"""

import os, uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Vancouver = Pacific Time (UTC-8 standard, UTC-7 daylight saving)
# Use a simple offset approach — works without pytz
import time as _time

def _vancouver_now() -> datetime:
    """Return current datetime in Vancouver (Pacific) time."""
    # Check if daylight saving is active using local system — 
    # or just calculate from UTC with proper DST offset
    utc_now = datetime.now(timezone.utc)
    # Pacific Standard Time = UTC-8, Pacific Daylight Time = UTC-7
    # DST in effect second Sunday of March to first Sunday of November
    year = utc_now.year
    # Second Sunday of March
    dst_start = datetime(year, 3, 8, 2, 0, tzinfo=timezone.utc)
    dst_start += timedelta(days=(6 - dst_start.weekday()) % 7)
    # First Sunday of November
    dst_end = datetime(year, 11, 1, 2, 0, tzinfo=timezone.utc)
    dst_end += timedelta(days=(6 - dst_end.weekday()) % 7)
    offset = -7 if dst_start <= utc_now < dst_end else -8
    return utc_now + timedelta(hours=offset)


from flask import (Flask, render_template, request, redirect,
                   url_for, flash, send_from_directory, abort, jsonify)
from werkzeug.utils import secure_filename

import config, database as db, eligibility as elig
from transcript_parser import extract_grade_from_pdf
from attendance_manager import import_file, import_all
from notifier import send_submission_notification, test_email

# ── App setup ────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.urandom(32)

for d in [config.ATTENDANCE_INPUT_DIR,
          config.TRANSCRIPT_UPLOAD_DIR,
          config.LETTER_UPLOAD_DIR]:
    os.makedirs(d, exist_ok=True)

db.init_db()
config.load_email_settings()
PROF_TOKEN = config.get_prof_token()


# ── Helpers ──────────────────────────────────────────────────
def _ext(filename): return Path(filename).suffix.lower()

def _save(file, directory, prefix):
    # Use the original filename the student gave
    original_name = secure_filename(file.filename)
    dest = os.path.join(directory, original_name)
    # If a file with that name already exists, add a short suffix to avoid overwriting
    if os.path.exists(dest):
        ext  = _ext(original_name)
        stem = original_name[:-len(ext)] if ext else original_name
        name = f"{stem}_{uuid.uuid4().hex[:6]}{ext}"
        dest = os.path.join(directory, name)
    else:
        name = original_name
    file.save(dest)
    return name

def _require_prof(token):
    if token != PROF_TOKEN:
        abort(404)


# ════════════════════════════════════════════════════════════
#  STUDENT PORTAL
# ════════════════════════════════════════════════════════════

@app.route("/")
def student_home():
    return render_template("student_home.html", prefill_sno=None)


@app.route("/check", methods=["POST"])
def student_check():
    sno        = request.form.get("student_number", "").strip()
    transcript = request.files.get("transcript")
    letter     = request.files.get("letter")

    if not sno:
        flash("Please enter your student number.", "error")
        return redirect(url_for("student_home"))

    # ── Validate consent ─────────────────────────────────────
    if not request.form.get("consent"):
        flash("Please consent to data usage before proceeding.", "error")
        return redirect(url_for("student_home"))

    # ── Validate transcript ──────────────────────────────────
    if not transcript or transcript.filename == "":
        flash("Please upload your official transcript (PDF).", "error")
        return redirect(url_for("student_home"))
    if _ext(transcript.filename) not in config.ALLOWED_TRANSCRIPT_EXT:
        flash("Transcript must be a PDF file.", "error")
        return redirect(url_for("student_home"))

    # ── Validate letter ──────────────────────────────────────
    if not letter or letter.filename == "":
        flash("Please upload your letter of interest.", "error")
        return redirect(url_for("student_home"))
    if _ext(letter.filename) not in config.ALLOWED_LETTER_EXT:
        flash("Letter must be a PDF file.", "error")
        return redirect(url_for("student_home"))

    # ── Save both files ──────────────────────────────────────
    trans_fname  = _save(transcript, config.TRANSCRIPT_UPLOAD_DIR, sno)
    letter_fname = _save(letter,     config.LETTER_UPLOAD_DIR,     sno)

    # ── Priority 1: Check if grade already exists in DB ─────
    db_grades = db.get_grades_by_student(sno)
    valid_db  = [v for v in db_grades.values() if v is not None]
    if valid_db:
        grade     = round(sum(valid_db) / len(valid_db), 2)
        grade_note = f"Your grade ({grade:.1f}%) was found in the course records."
        return _run_eligibility(sno, grade, "database",
                                trans_fname, letter_fname, grade_note)

    # ── Priority 2: Extract grade from uploaded transcript ───
    auto_grade, method = extract_grade_from_pdf(
        os.path.join(config.TRANSCRIPT_UPLOAD_DIR, trans_fname))

    if auto_grade is not None:
        grade_note = f"Grade extracted from transcript: {auto_grade:.1f}% ({method})."
        return _run_eligibility(sno, auto_grade, "transcript",
                                trans_fname, letter_fname, grade_note)

    # ── Priority 3: Auto-extraction failed → ask for manual input ──
    return render_template("student_manual_grade.html",
                           student_number=sno,
                           trans_fname=trans_fname,
                           letter_fname=letter_fname)


@app.route("/check/manual-grade", methods=["POST"])
def student_manual_grade():
    sno          = request.form.get("student_number", "").strip()
    trans_fname  = request.form.get("trans_fname",    "").strip()
    letter_fname = request.form.get("letter_fname",   "").strip()
    grade_str    = request.form.get("manual_grade",   "").strip()

    if not grade_str:
        flash("Please enter your grade.", "error")
        return render_template("student_manual_grade.html",
                               student_number=sno,
                               trans_fname=trans_fname,
                               letter_fname=letter_fname)
    try:
        grade = float(grade_str)
        if not (0 <= grade <= 100):
            raise ValueError
    except ValueError:
        flash("Please enter a valid number between 0 and 100.", "error")
        return render_template("student_manual_grade.html",
                               student_number=sno,
                               trans_fname=trans_fname,
                               letter_fname=letter_fname)

    return _run_eligibility(sno, grade, "manual",
                            trans_fname, letter_fname,
                            f"Grade manually entered as {grade:.1f}%. ⚠️ Pending professor verification.")


def _run_eligibility(sno, grade, grade_source, trans_fname, letter_fname, grade_note):
    """Shared logic — run check and render result."""
    result = elig.check(sno, grade, grade_source)

    if result["eligible"]:
        db.upsert_eligible(
            student_number=sno,
            student_name=result["student_name"],
            grade=result["grade"],
            grade_source=result["grade_source"],
            eligible_identifiers=result["passing_ids"],
            attendance_rates=result["att_results"],
            transcript_file=trans_fname,
            letter_file=letter_fname,
        )

    # Send email notification regardless of eligibility
    try:
        send_submission_notification(
            student_number=sno,
            student_name=result["student_name"],
            trans_fname=trans_fname,
            letter_fname=letter_fname,
        )
    except Exception:
        pass  # Never let email failure break the student flow

    return render_template("student_result.html",
                           r=result,
                           grade_note=grade_note,
                           checked_at=_vancouver_now().strftime("%Y-%m-%d %H:%M"))


# ════════════════════════════════════════════════════════════
#  PROFESSOR DASHBOARD  (secret URL)
# ════════════════════════════════════════════════════════════

@app.route("/prof/<token>", methods=["GET","POST"])
def prof_dashboard(token):
    _require_prof(token)
    stats    = db.get_summary_stats()
    eligible = db.count_eligible()
    recent   = db.get_all_eligible()[:5]
    check_result = None

    if request.method == "POST":
        sno       = request.form.get("student_number", "").strip()
        grade_str = request.form.get("manual_grade",   "").strip()
        if sno:
            if grade_str:
                try:
                    grade        = float(grade_str)
                    grade_source = "manual (professor)"
                except ValueError:
                    grade        = None
                    grade_source = "unknown"
            else:
                db_grades = db.get_grades_by_student(sno)
                valid     = [v for v in db_grades.values() if v is not None]
                if valid:
                    grade        = round(sum(valid) / len(valid), 2)
                    grade_source = "database"
                else:
                    grade        = None
                    grade_source = "not found"
            check_result = elig.check(sno, grade, grade_source)

    def _dir_size(path):
        total = 0
        if os.path.exists(path):
            for f in os.listdir(path):
                fp = os.path.join(path, f)
                if os.path.isfile(fp):
                    total += os.path.getsize(fp)
        return total

    db_size          = os.path.getsize(config.DB_PATH) if os.path.exists(config.DB_PATH) else 0
    transcripts_size = _dir_size(config.TRANSCRIPT_UPLOAD_DIR)
    letters_size     = _dir_size(config.LETTER_UPLOAD_DIR)
    rosters_size     = _dir_size(config.ATTENDANCE_INPUT_DIR)
    total_size       = db_size + transcripts_size + letters_size + rosters_size

    def _fmt(b):
        if b < 1024:    return f"{b} B"
        if b < 1024**2: return f"{b/1024:.1f} KB"
        return              f"{b/1024**2:.1f} MB"

    storage = {
        "db":          _fmt(db_size),
        "transcripts": _fmt(transcripts_size),
        "letters":     _fmt(letters_size),
        "rosters":     _fmt(rosters_size),
        "total":       _fmt(total_size),
        "total_mb":    round(total_size / 1024**2, 2),
        "limit_mb":    512,
        "pct":         round(total_size / (512 * 1024**2) * 100, 1),
    }

    return render_template("prof_dashboard.html",
                           token=token, stats=stats,
                           eligible_count=eligible,
                           recent=recent, storage=storage,
                           check_result=check_result)


@app.route("/prof/<token>/roster")
def prof_roster(token):
    _require_prof(token)
    rows = db.get_all_enrolments()
    return render_template("prof_roster.html", token=token, rows=rows,
                           min_att=config.MIN_ATTENDANCE_PERCENT,
                           min_grade=config.MIN_GRADE_PERCENT)


@app.route("/prof/<token>/eligible")
def prof_eligible(token):
    _require_prof(token)
    rows = db.get_all_eligible()
    return render_template("prof_eligible.html", token=token, rows=rows)


@app.route("/prof/<token>/letters/download/<filename>")
def prof_download_letter(token, filename):
    _require_prof(token)
    safe = secure_filename(filename)
    filepath = os.path.join(config.LETTER_UPLOAD_DIR, safe)
    if not os.path.exists(filepath):
        flash(f"File not found: {safe}", "error")
        return redirect(url_for("prof_documents", token=token))
    return send_from_directory(
        os.path.abspath(config.LETTER_UPLOAD_DIR),
        safe, as_attachment=True
    )


@app.route("/prof/<token>/documents")
def prof_documents(token):
    _require_prof(token)

    def _get_files(directory):
        files = []
        if os.path.exists(directory):
            for fname in sorted(os.listdir(directory)):
                fpath = os.path.join(directory, fname)
                files.append({
                    "name":     fname,
                    "size":     f"{os.path.getsize(fpath)/1024:.1f} KB",
                    "modified": (datetime.fromtimestamp(os.path.getmtime(fpath), tz=timezone.utc)
                                 + timedelta(hours=-7)).strftime("%Y-%m-%d %H:%M"),
                })
        return files

    return render_template("prof_documents.html", token=token,
                           letters=_get_files(config.LETTER_UPLOAD_DIR),
                           transcripts=_get_files(config.TRANSCRIPT_UPLOAD_DIR))


@app.route("/prof/<token>/transcripts/download/<filename>")
def prof_download_transcript(token, filename):
    _require_prof(token)
    safe     = secure_filename(filename)
    filepath = os.path.join(config.TRANSCRIPT_UPLOAD_DIR, safe)
    if not os.path.exists(filepath):
        flash(f"File not found: {safe}", "error")
        return redirect(url_for("prof_documents", token=token))
    return send_from_directory(
        os.path.abspath(config.TRANSCRIPT_UPLOAD_DIR),
        safe, as_attachment=True
    )


@app.route("/prof/<token>/transcripts/delete/<filename>", methods=["POST"])
def prof_delete_transcript(token, filename):
    _require_prof(token)
    safe     = secure_filename(filename)
    filepath = os.path.join(config.TRANSCRIPT_UPLOAD_DIR, safe)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"✅ Deleted transcript: {safe}", "success")
    else:
        flash(f"File not found: {safe}", "error")
    return redirect(url_for("prof_documents", token=token))



@app.route("/prof/<token>/import", methods=["GET","POST"])
def prof_import(token):
    _require_prof(token)
    results = []
    form_vals = {}

    if request.method == "POST":
        # Metadata from form
        course  = request.form.get("course",  "").strip()
        section = request.form.get("section", "").strip()
        year    = request.form.get("year",    "").strip()
        term    = request.form.get("term",    "").strip()
        form_vals = {"course": course, "section": section,
                     "year": year, "term": term}

        # Pass metadata only if all 4 are provided
        meta_from_form = all([course, section, year, term])

        files = request.files.getlist("roster_files")
        for f in files:
            if not f.filename: continue
            if not f.filename.lower().endswith(".xlsx"):
                results.append({"file": f.filename, "total": 0, "new": 0,
                                 "status": "error: file must be .xlsx"})
                continue
            dest = os.path.join(config.ATTENDANCE_INPUT_DIR,
                                secure_filename(f.filename))
            f.save(dest)
            try:
                r = import_file(
                    dest,
                    course  = course  if meta_from_form else None,
                    section = section if meta_from_form else None,
                    year    = year    if meta_from_form else None,
                    term    = term    if meta_from_form else None,
                )
                r["file"]   = f.filename
                r["status"] = "ok"
                if meta_from_form:
                    r["meta"] = f"{course} | Section {section} | {year} {term}"
            except Exception as e:
                r = {"file": f.filename, "total": 0, "new": 0,
                     "status": f"error: {e}"}
            results.append(r)

    return render_template("prof_import.html", token=token,
                           results=results, form_vals=form_vals)




@app.route("/prof/<token>/files")
def prof_files(token):
    _require_prof(token)
    disk_files = []
    if os.path.exists(config.ATTENDANCE_INPUT_DIR):
        for fname in sorted(os.listdir(config.ATTENDANCE_INPUT_DIR)):
            if fname.lower().endswith(".xlsx"):
                fpath = os.path.join(config.ATTENDANCE_INPUT_DIR, fname)
                disk_files.append({
                    "name":     fname,
                    "size":     f"{os.path.getsize(fpath)/1024:.1f} KB",
                    "modified": (datetime.fromtimestamp(os.path.getmtime(fpath), tz=timezone.utc)
                                 + timedelta(hours=-7)).strftime("%Y-%m-%d %H:%M"),
                })
    db_files = {r["source_file"]: r for r in db.get_source_files()}
    return render_template("prof_files.html", token=token,
                           disk_files=disk_files, db_files=db_files)


@app.route("/prof/<token>/check", methods=["GET","POST"])
def prof_check(token):
    _require_prof(token)
    result = None
    if request.method == "POST":
        sno       = request.form.get("student_number", "").strip()
        grade_str = request.form.get("manual_grade",   "").strip()

        if sno:
            # Priority 1: manual override from prof
            if grade_str:
                try:
                    grade        = float(grade_str)
                    grade_source = "manual (professor)"
                except ValueError:
                    grade        = None
                    grade_source = "unknown"
            else:
                # Priority 2: look up grade from DB
                db_grades = db.get_grades_by_student(sno)
                valid     = [v for v in db_grades.values() if v is not None]
                if valid:
                    grade        = round(sum(valid) / len(valid), 2)
                    grade_source = "database"
                else:
                    grade        = None
                    grade_source = "not found"

            result = elig.check(sno, grade, grade_source)

    return render_template("prof_check.html", token=token, result=result)


@app.route("/prof/<token>/eligible/toggle-done/<student_number>", methods=["POST"])
def prof_toggle_done(token, student_number):
    _require_prof(token)
    db.toggle_reference_done(student_number)
    return redirect(url_for("prof_eligible", token=token))


@app.route("/prof/<token>/eligible/delete/<student_number>", methods=["POST"])
def prof_delete_eligible(token, student_number):
    _require_prof(token)
    db.delete_eligible(student_number)
    flash(f"✅ Removed student {student_number} from the eligible list.", "success")
    return redirect(url_for("prof_eligible", token=token))


@app.route("/prof/<token>/files/delete/<filename>", methods=["POST"])
def prof_delete_file(token, filename):
    _require_prof(token)
    safe     = secure_filename(filename)
    filepath = os.path.join(config.ATTENDANCE_INPUT_DIR, safe)
    result   = {"file": safe, "deleted_enrolments": 0,
                "removed_eligible": 0, "file_deleted": False}

    # Remove from DB first
    db_result = db.delete_by_source_file(safe)
    result.update(db_result)

    # Remove file from disk
    if os.path.exists(filepath):
        os.remove(filepath)
        result["file_deleted"] = True

    flash(
        f"✅ Deleted '{safe}': "
        f"{result['deleted_enrolments']} enrolment(s) removed, "
        f"{result['removed_eligible']} student(s) removed from eligible list.",
        "success"
    )
    return redirect(url_for("prof_files", token=token))



@app.route("/prof/<token>/settings", methods=["GET","POST"])
def prof_settings(token):
    _require_prof(token)
    msg      = None
    msg_type = "success"

    if request.method == "POST":
        try:
            g = float(request.form["min_grade"])
            a = float(request.form["min_att"])
            config.MIN_GRADE_PERCENT      = g
            config.MIN_ATTENDANCE_PERCENT = a
            _save_thresholds(g, a)

            action = request.form.get("action", "save")

            if action == "save_and_recheck":
                # Re-check all pending eligible students (skip reference_done)
                all_eligible = db.get_all_eligible()
                removed = []
                for row in all_eligible:
                    if row.get("reference_done"):
                        continue  # skip completed ones
                    sno   = row["student_number"]
                    grade = row.get("overall_grade_pct")
                    grade_source = row.get("grade_source", "database")
                    result = elig.check(sno, grade, grade_source)
                    if not result["eligible"]:
                        db.delete_eligible(sno)
                        removed.append(f"{row['student_name']} ({sno})")

                if removed:
                    msg = (f"✅ Thresholds saved — Min grade: {g}%, Min attendance: {a}%.<br>"
                           f"🗑 Removed {len(removed)} student(s) who no longer qualify:<br>"
                           + "<br>".join(f"&nbsp;&nbsp;• {r}" for r in removed))
                else:
                    msg = (f"✅ Thresholds saved — Min grade: {g}%, Min attendance: {a}%.<br>"
                           f"All pending eligible students still qualify under the new thresholds.")
            else:
                msg = f"✅ Saved — Min grade: {g}%, Min attendance: {a}%"

        except Exception as e:
            msg      = f"❌ Error: {e}"
            msg_type = "error"

    return render_template("prof_settings.html", token=token,
                           min_grade=config.MIN_GRADE_PERCENT,
                           min_att=config.MIN_ATTENDANCE_PERCENT,
                           msg=msg, msg_type=msg_type,
                           notify_email=config.NOTIFY_EMAIL,
                           brevo_api_key=config.BREVO_API_KEY)


@app.route("/prof/<token>/settings/email", methods=["POST"])
def prof_save_email(token):
    _require_prof(token)
    config.load_email_settings()
    notify_email  = request.form.get("notify_email",  "").strip()
    new_key       = request.form.get("brevo_api_key", "").strip()
    # Use new key if provided, otherwise keep existing
    brevo_api_key = new_key if new_key else config.BREVO_API_KEY
    config.save_email_settings(notify_email, brevo_api_key)
    flash("✅ Email settings saved.", "success")
    return redirect(url_for("prof_settings", token=token))


@app.route("/prof/<token>/settings/test-email", methods=["POST"])
def prof_test_email(token):
    _require_prof(token)
    config.load_email_settings()
    notify_email = request.form.get("notify_email", "").strip()
    if notify_email and notify_email != config.NOTIFY_EMAIL:
        config.save_email_settings(notify_email, config.BREVO_API_KEY)
    ok, msg = test_email()
    flash(("✅ " if ok else "❌ ") + msg, "success" if ok else "error")
    return redirect(url_for("prof_settings", token=token))



@app.route("/prof/<token>/letters/delete/<filename>", methods=["POST"])
def prof_delete_letter(token, filename):
    _require_prof(token)
    safe = secure_filename(filename)
    path = os.path.join(config.LETTER_UPLOAD_DIR, safe)
    if os.path.exists(path):
        os.remove(path)
        flash(f"✅ Deleted: {safe}", "success")
    else:
        flash(f"File not found: {safe}", "error")
    return redirect(url_for("prof_documents", token=token))


@app.route("/prof/<token>/letters/delete-all", methods=["POST"])
def prof_delete_all_letters(token):
    _require_prof(token)
    for fname in os.listdir(config.LETTER_UPLOAD_DIR):
        os.remove(os.path.join(config.LETTER_UPLOAD_DIR, fname))
    flash("✅ All letter files deleted.", "success")
    return redirect(url_for("prof_documents", token=token))


def _save_thresholds(g, a):
    path = os.path.join(config.DATA_DIR, "saved_thresholds.txt")
    with open(path, "w") as f:
        f.write(f"{g}\n{a}\n")


def _load_thresholds():
    path = os.path.join(config.DATA_DIR, "saved_thresholds.txt")
    if os.path.exists(path):
        try:
            lines = open(path).read().splitlines()
            config.MIN_GRADE_PERCENT      = float(lines[0])
            config.MIN_ATTENDANCE_PERCENT = float(lines[1])
        except Exception:
            pass

_load_thresholds()

# ── Run ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  PROFESSOR REFERENCE SYSTEM")
    print(f"  Professor URL: http://localhost:5000/prof/{PROF_TOKEN}")
    print(f"  Student URL:   http://localhost:5000")
    print("=" * 55)
    app.run(debug=False, host="0.0.0.0", port=5000)

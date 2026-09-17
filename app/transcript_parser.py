"""
transcript_parser.py
--------------------
Extracts overall average grade from a student transcript PDF.

Priority:
  1. pdfplumber text extraction → look for average/GPA patterns
  2. OCR via pdfplumber image rendering + pytesseract (for scanned PDFs)
  3. Calculate from individual course grades if enough found
  4. Return None → caller shows manual entry form
"""

import re
import pdfplumber

_AVG_PATTERNS = [
    r"average[:\s]+(\d{1,3}(?:\.\d{1,2})?)\s*%",
    r"(?:overall|cumulative|weighted|final|general|session|term)\s+average[:\s]+(\d{1,3}(?:\.\d{1,2})?)\s*%?",
    r"average\s+grade[:\s]+(\d{1,3}(?:\.\d{1,2})?)\s*%?",
    r"grade\s+average[:\s\t]+(\d{1,3}(?:\.\d{1,2})?)\s*%?",
    r"(?:avg|average)[^\d]{0,10}(\d{1,3}(?:\.\d{1,2})?)\s*%",
]

_GPA_4_PATTERNS = [
    r"(?:cumulative\s+)?(?:gpa|cgpa)[:\s]+(\d(?:\.\d{1,2})?)\s*(?:/\s*4(?:\.0)?)?",
    r"grade\s+point\s+average[:\s]+(\d(?:\.\d{1,2})?)\s*(?:/\s*4(?:\.0)?)?",
]

_GPA_TO_PCT = {
    4.33: 90, 4.30: 89, 4.20: 88, 4.10: 87, 4.00: 86,
    3.95: 85, 3.90: 84, 3.85: 83, 3.80: 82, 3.75: 81, 3.70: 80,
    3.60: 79, 3.50: 78, 3.40: 77, 3.30: 76,
    3.20: 75, 3.10: 74, 3.00: 73,
    2.95: 72, 2.90: 71, 2.80: 70,
    2.70: 69, 2.65: 68, 2.60: 67, 2.55: 66, 2.50: 65,
    2.40: 64, 2.30: 63, 2.20: 62, 2.10: 61, 2.00: 60,
    1.90: 59, 1.80: 58, 1.70: 57, 1.60: 56, 1.50: 55,
    1.40: 54, 1.30: 53, 1.20: 52, 1.10: 51, 1.00: 50,
}

_LETTER_TO_PCT = {
    "A+": 95, "A": 87, "A-": 82,
    "B+": 77, "B":  73, "B-": 69,
    "C+": 65, "C":  61, "C-": 57,
    "D":  52, "F":  25,
}

_SKIP_GRADES = {"cip", "w", "exg", "p", "cr", "nc", "s", "u", "ip", "ae", "wf"}

def _gpa4_to_percent(gpa: float) -> float:
    if gpa in _GPA_TO_PCT:
        return float(_GPA_TO_PCT[gpa])
    closest = min(_GPA_TO_PCT.keys(), key=lambda k: abs(k - gpa))
    return float(_GPA_TO_PCT[closest])

def _find_average_in_text(text: str) -> tuple[float | None, str]:
    text_lower = text.lower()
    for pat in _AVG_PATTERNS:
        matches = list(re.finditer(pat, text_lower))
        if matches:
            m = matches[-1]
            val = float(m.group(1))
            if 0 <= val <= 100:
                return val, f"Cumulative average found in transcript: {val:.1f}%"
    for pat in _GPA_4_PATTERNS:
        m = re.search(pat, text_lower)
        if m:
            gpa = float(m.group(1))
            if 0 <= gpa <= 4.0:
                pct = _gpa4_to_percent(gpa)
                return pct, f"Converted from GPA {gpa}/4.0 → {pct:.1f}%"
    m = re.search(r"overall[:\s]+([A-F][+-]?)\s*\((\d{1,3})%\)", text, re.IGNORECASE)
    if m:
        val = float(m.group(2))
        if 0 <= val <= 100:
            return val, f"Extracted from letter-grade annotation: {val:.1f}%"
    return None, ""

_SKIP_LINE_PATTERNS = [
    r"^\d{4}$", r"^20\d{2}", r"credit", r"unit", r"hour",
    r"total", r"attempted", r"earned", r"gpa", r"cgpa",
    r"program", r"degree", r"student", r"page", r"date",
    r"class\s+avg", r"class\s+size", r"rec",
]

def _calc_from_individual_grades(text: str) -> tuple[float | None, str]:
    grades = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if any(re.search(p, lower) for p in _SKIP_LINE_PATTERNS):
            continue
        if any(f" {g} " in f" {lower} " for g in _SKIP_GRADES):
            continue
        m = re.search(r'\b(\d{1,3}(?:\.\d)?)\s*$', stripped)
        if m:
            val = float(m.group(1))
            if 0 <= val <= 100 and len(stripped.replace(m.group(1), "").strip()) > 4:
                grades.append(val)
            continue
        m2 = re.search(r'\b([A-F][+-]?)\s+(\d{1,3}(?:\.\d)?)\s*$', stripped)
        if m2:
            val = float(m2.group(2))
            if 0 <= val <= 100:
                grades.append(val)
    if len(grades) >= 3:
        avg = round(sum(grades) / len(grades), 2)
        if 0 <= avg <= 100:
            return avg, f"Calculated from {len(grades)} individual course grades: {avg:.1f}%"
    return None, ""

def _ocr_pdf(filepath: str) -> str:
    """
    Render PDF pages to images using pdfplumber (no poppler needed),
    then run OCR via pytesseract.
    Returns empty string if pytesseract not available.
    """
    try:
        import pytesseract
        text_parts = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                img = page.to_image(resolution=200).original
                text_parts.append(pytesseract.image_to_string(img))
        return "\n".join(text_parts)
    except Exception:
        return ""

def extract_grade_from_pdf(filepath: str) -> tuple[float | None, str]:
    # Step 1: Try text extraction (fast, works for digital PDFs)
    try:
        with pdfplumber.open(filepath) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        return None, f"Could not open PDF: {e}"

    if text.strip():
        grade, method = _find_average_in_text(text)
        if grade is not None:
            return grade, method
        grade, method = _calc_from_individual_grades(text)
        if grade is not None:
            return grade, method

    # Step 2: OCR for scanned/image-based PDFs
    ocr_text = _ocr_pdf(filepath)
    if ocr_text.strip():
        grade, method = _find_average_in_text(ocr_text)
        if grade is not None:
            return grade, f"[OCR] {method}"
        grade, method = _calc_from_individual_grades(ocr_text)
        if grade is not None:
            return grade, f"[OCR] {method}"

    return None, "Could not extract grade automatically — please enter manually"

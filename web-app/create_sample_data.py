"""
create_sample_data.py
---------------------
Run this script once to populate the system with dummy data for demonstration.
Usage: python3 create_sample_data.py
"""

import os, sys, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config, database as db
from attendance_manager import import_file
import openpyxl
from datetime import datetime

def create_sample_roster():
    """Create a sample roster Excel file with fake student data."""
    os.makedirs(config.ATTENDANCE_INPUT_DIR, exist_ok=True)
    path = os.path.join(config.ATTENDANCE_INPUT_DIR, 'Sample_Roster_COMM436_2025_W1.xlsx')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Roster"

    headers = ['Student #', 'First Name', 'Last Name', 'Year', 'Term',
               'Course', 'Section', '%Abs', 'Grade']
    ws.append(headers)

    students = [
        ('10001001', 'Alice',   'Chen',      '2025', 'W1', 'COMM 436', '101', 0.02, 88.5),
        ('10001002', 'Bob',     'Martinez',  '2025', 'W1', 'COMM 436', '101', 0.05, 92.0),
        ('10001003', 'Carol',   'Smith',     '2025', 'W1', 'COMM 436', '101', 0.30, 85.0),
        ('10001004', 'David',   'Kim',       '2025', 'W1', 'COMM 436', '101', 0.08, 74.0),
        ('10001005', 'Emma',    'Johnson',   '2025', 'W1', 'COMM 436', '101', 0.04, 91.5),
        ('10001006', 'Frank',   'Lee',       '2025', 'W1', 'COMM 436', '101', 0.12, 79.0),
        ('10001007', 'Grace',   'Wang',      '2025', 'W1', 'COMM 436', '101', 0.03, 95.0),
        ('10001008', 'Henry',   'Brown',     '2025', 'W1', 'COMM 436', '101', 0.25, 83.0),
        ('10001009', 'Iris',    'Davis',     '2025', 'W1', 'COMM 436', '101', 0.06, 87.0),
        ('10001010', 'James',   'Wilson',    '2025', 'W1', 'COMM 436', '101', 0.40, 90.0),
        ('10002001', 'Karen',   'Taylor',    '2025', 'W1', 'COMM 437', '201', 0.03, 89.0),
        ('10002002', 'Liam',    'Anderson',  '2025', 'W1', 'COMM 437', '201', 0.07, 82.5),
        ('10002003', 'Mia',     'Thomas',    '2025', 'W1', 'COMM 437', '201', 0.02, 94.0),
        ('10002004', 'Noah',    'Jackson',   '2025', 'W1', 'COMM 437', '201', 0.15, 76.0),
        ('10002005', 'Olivia',  'White',     '2025', 'W1', 'COMM 437', '201', 0.04, 88.0),
    ]

    for s in students:
        ws.append(s)

    wb.save(path)
    print(f"✅ Created sample roster: {path}")
    return path


def create_eligible_students():
    """Add some sample eligible students to the database."""
    eligible = [
        {
            'student_number': '10001001',
            'student_name': 'Alice Chen',
            'grade': 88.5,
            'grade_source': 'database',
            'identifiers': ['COMM436_101_2025_W1_10001001'],
            'att_rates': {'COMM436_101_2025_W1_10001001': 98.0},
        },
        {
            'student_number': '10001002',
            'student_name': 'Bob Martinez',
            'grade': 92.0,
            'grade_source': 'database',
            'identifiers': ['COMM436_101_2025_W1_10001002'],
            'att_rates': {'COMM436_101_2025_W1_10001002': 95.0},
        },
        {
            'student_number': '10002003',
            'student_name': 'Mia Thomas',
            'grade': 94.0,
            'grade_source': 'database',
            'identifiers': ['COMM437_201_2025_W1_10002003'],
            'att_rates': {'COMM437_201_2025_W1_10002003': 98.0},
        },
    ]

    for e in eligible:
        db.upsert_eligible(
            student_number=e['student_number'],
            student_name=e['student_name'],
            grade=e['grade'],
            grade_source=e['grade_source'],
            eligible_identifiers=e['identifiers'],
            attendance_rates=e['att_rates'],
            transcript_file='',
            letter_file='',
        )
    print(f"✅ Added {len(eligible)} sample eligible students")


def create_thresholds():
    """Save default threshold settings."""
    path = os.path.join(config.DATA_DIR, 'saved_thresholds.txt')
    with open(path, 'w') as f:
        f.write("80.0\n75.0\n")
    print("✅ Created default thresholds (Grade: 80%, Attendance: 75%)")


def create_prof_token():
    """Create a sample professor token."""
    token_path = os.path.join(config.DATA_DIR, 'prof_token.txt')
    if not os.path.exists(token_path):
        import secrets
        token = secrets.token_urlsafe(24)
        os.makedirs(config.DATA_DIR, exist_ok=True)
        with open(token_path, 'w') as f:
            f.write(token)
        print(f"✅ Created professor token")
    else:
        print("✅ Professor token already exists")


if __name__ == '__main__':
    print("\n=== Prof Reference System — Sample Data Setup ===\n")
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.TRANSCRIPT_UPLOAD_DIR, exist_ok=True)
    os.makedirs(config.LETTER_UPLOAD_DIR, exist_ok=True)
    os.makedirs(config.ATTENDANCE_INPUT_DIR, exist_ok=True)

    db.init_db()
    create_prof_token()
    create_thresholds()

    roster_path = create_sample_roster()
    import_file(roster_path, verbose=True)
    create_eligible_students()

    token = open(os.path.join(config.DATA_DIR, 'prof_token.txt')).read().strip()
    print(f"\n=== Setup complete! ===")
    print(f"Run: python3 app.py")
    print(f"Student portal: http://localhost:5000")
    print(f"Professor dashboard: http://localhost:5000/prof/{token}")
    print()

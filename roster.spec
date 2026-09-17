# roster.spec — PyInstaller build configuration for the desktop packaging
# Run: pyinstaller roster.spec        (untested on the machine this was rewritten on, 2026-09-17)

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = [
    ('app/templates', 'app/templates'),
]

try:
    from PyInstaller.utils.hooks import collect_data_files
    datas += collect_data_files('pdfplumber')
    datas += collect_data_files('pdfminer')
except Exception:
    pass

hidden_imports = [
    'flask', 'jinja2', 'werkzeug', 'openpyxl',
    'pdfplumber', 'pdfminer', 'pdfminer.high_level',
    'pdfminer.layout', 'pdfminer.converter',
    'pdfminer.pdfpage', 'pdfminer.pdfinterp',
    'pytesseract', 'PIL', 'PIL.Image',
    'sqlite3', 'smtplib', 'email',
    'email.mime', 'email.mime.text', 'email.mime.multipart',
    'urllib', 'urllib.request', 'urllib.error',
    'app', 'app.config', 'app.database', 'app.eligibility',
    'app.transcript_parser', 'app.attendance_manager', 'app.notifier', 'app.seed', 'app.web',
]

a = Analysis(
    ['run_desktop.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['PyQt5', 'PySide6', 'PySide2', 'PyQt6',
              'matplotlib', 'numpy', 'pandas', 'IPython',
              'jupyter', 'notebook', 'sphinx', 'pytest'],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == 'darwin':
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True,
              name='Letterkeep', debug=False,
              bootloader_ignore_signals=False, strip=False, upx=True, console=True)
    coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas,
                   strip=False, upx=True, name='Letterkeep')
    app = BUNDLE(coll, name='Letterkeep.app', icon=None,
                 bundle_identifier='com.letterkeep.roster',
                 info_plist={
                     'CFBundleName': 'Letterkeep',
                     'CFBundleShortVersionString': '1.0.0',
                     'NSHighResolutionCapable': True,
                 })
else:
    exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
              name='Letterkeep', debug=False,
              bootloader_ignore_signals=False, strip=False, upx=True, console=True)

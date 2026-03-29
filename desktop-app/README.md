# Prof Reference System — Desktop App

Standalone desktop application built with PyInstaller. Runs entirely on your local computer — no server needed, all student data stays on your machine.

## Running from Source

```bash
cd desktop-app
pip install -r requirements.txt
python3 create_sample_data.py
python3 launcher.py
```

The app opens automatically in your browser at the **professor dashboard**.
Both portals run simultaneously from the same app:

| Portal | URL |
|---|---|
| Professor dashboard | `http://127.0.0.1:5001/prof/<your-token>` (opens automatically) |
| Student portal | `http://127.0.0.1:5001` |

The professor token is generated on first run and saved to `data/prof_token.txt`.
Share the student portal URL with students — they access it from the same network,
or via a tunneling tool like ngrok for remote access.

## Building the Desktop App

### Prerequisites

```bash
pip install pyinstaller pdfplumber pillow pytesseract
```

OCR support (optional):
- **Mac**: `brew install tesseract`
- **Windows**: [Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki)

### Build

```bash
# Mac — creates ProfReferenceSystem.app
pyinstaller roster.spec

# Windows — creates ProfReferenceSystem.exe
pyinstaller roster.spec
```

Output in `dist/` folder.

## Distributing

Send the recipient a folder containing:
```
ProfReferenceSystem/
├── ProfReferenceSystem.app   (Mac) or ProfReferenceSystem.exe (Windows)
└── data/                     (your data, or empty for a fresh install)
```

The `data/` folder must always sit next to the app file.

## Notes

- Port 5001 is used to avoid conflict with macOS AirPlay (which uses 5000)
- The app opens the professor dashboard automatically on launch
- First launch on Mac may require right-click → Open to bypass Gatekeeper

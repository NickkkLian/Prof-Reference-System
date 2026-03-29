# Prof Reference System — Desktop App

Standalone desktop application built with PyInstaller. Runs entirely on your local computer — no server needed, all student data stays on your machine.

## Running from Source

```bash
cd desktop-app
pip install -r requirements.txt
python3 create_sample_data.py
python3 launcher.py
```

Browser opens automatically at `http://127.0.0.1:5001/prof/<your-token>`

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

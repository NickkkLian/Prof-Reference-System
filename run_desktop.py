#!/usr/bin/env python3
"""run_desktop.py — start Letterkeep on the professor's own machine and open the dashboard in a browser.

    python3 run_desktop.py [--seed] [--port 5001]

Same application as run_web.py; the difference is the packaging. Bound to 127.0.0.1 and never to the network, and the
data folder sits next to the program: next to this file when run from a checkout, next to the .app / .exe when the
PyInstaller bundle (roster.spec) runs it, so a professor's roster and uploads stay where they can see them and are not
swallowed by the bundle's temporary folder.

Packaging with PyInstaller is untested on the machine this was rewritten on; the checkout path is the one that is run.
"""
import argparse
import os
import sys
import threading
import time
import webbrowser


def data_root() -> str:
    """Next to the .app / .exe when frozen (sys.executable is inside MyApp.app/Contents/MacOS/), next to this file
    otherwise. PyInstaller unpacks the code into a temporary folder, which is wiped on exit — data must not live there."""
    if getattr(sys, "frozen", False):
        macos_dir = os.path.dirname(os.path.abspath(sys.executable))       # …/Contents/MacOS
        contents = os.path.dirname(macos_dir)                              # …/Contents
        dot_app = os.path.dirname(contents)                                # …/MyApp.app
        return os.path.dirname(dot_app)                                    # the folder that holds MyApp.app
    return os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--seed", action="store_true", help="create the demo data first (safe to repeat)")
    p.add_argument("--port", type=int, default=5001)
    p.add_argument("--no-browser", action="store_true", help="do not open a browser window")
    args = p.parse_args()

    os.environ.setdefault("ROSTER_DATA_DIR", os.path.join(data_root(), "data"))
    if getattr(sys, "frozen", False):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    if args.seed:
        from app import seed
        seed.main()

    from app import config
    from app.web import app

    url = f"http://127.0.0.1:{args.port}"
    token = config.get_prof_token()
    print("=" * 72)
    print(f"  {config.APP_NAME}")
    print(f"  Opening {url}/prof/<token>")
    print(f"  Data folder: {config.DATA_DIR}")
    print("  Close this window to stop.")
    print("=" * 72)

    if not args.no_browser:
        def open_later():
            time.sleep(1.5)
            webbrowser.open(f"{url}/prof/{token}")
        threading.Thread(target=open_later, daemon=True).start()

    app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())

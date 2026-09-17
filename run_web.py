#!/usr/bin/env python3
"""run_web.py — start Letterkeep as a web app (one command, no setup).

    python3 run_web.py --seed        demo data (15 students, 2 courses), then serve on http://127.0.0.1:5001
    python3 run_web.py               serve whatever is already in data/
    python3 run_web.py --port 8000 --host 0.0.0.0     serve to the network as well (see the note below)

The professor's page lives behind a token in the URL; the token is printed on startup and kept in data/prof_token.txt.
Default host is 127.0.0.1: this machine only. --host 0.0.0.0 makes the roster reachable by anyone on the same network
who knows (or guesses their way to) that URL, so it is a choice, not the default. For a real deployment behind a
server, point gunicorn at the same app object:  gunicorn -w 4 -b 127.0.0.1:8000 app.web:app
"""
import argparse
import os
import socket
import sys

from pyversion import too_old


def free(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--seed", action="store_true", help="create the demo data first (safe to repeat)")
    p.add_argument("--host", default="127.0.0.1", help="interface to bind (default: this machine only)")
    p.add_argument("--port", type=int, default=5001, help="port (default: 5001; 5000 is taken by AirPlay on macOS)")
    p.add_argument("--data-dir", help="where the database, the roster files and the uploads live (default: app/data)")
    args = p.parse_args()

    old = too_old()
    if old:
        print(old, file=sys.stderr)
        return 2

    if args.data_dir:                                  # read by app.config at import time
        os.environ["ROSTER_DATA_DIR"] = os.path.abspath(args.data_dir)

    if args.seed:
        from app import seed
        seed.main()

    from app import config
    from app.web import app

    if not free(args.host, args.port):
        print(f"Port {args.port} on {args.host} is already in use — start again with --port <free port>.\n"
              f"(On macOS, port 5000 belongs to AirPlay Receiver unless you turn it off in System Settings.)")
        return 2

    token = config.get_prof_token()
    print("=" * 72)
    print(f"  {config.APP_NAME}")
    print(f"  Student page:        http://{args.host}:{args.port}/")
    print(f"  Professor dashboard: http://{args.host}:{args.port}/prof/{token}")
    print(f"  Data folder:         {config.DATA_DIR}")
    print("  Stop with Ctrl-C.")
    print("=" * 72)
    app.run(host=args.host, port=args.port, debug=False, use_reloader=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())

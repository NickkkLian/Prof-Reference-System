"""The two entry points refuse to start on a Python that cannot import the application, and say which version to get.

macOS ships 3.9 as /usr/bin/python3 and the modules under app/ annotate with `float | None`, which 3.9 cannot evaluate
at import time. Without the guard the first thing a reader following the README sees is a TypeError six frames deep in
app/database.py. These tests ask what a 3.9 reader is told without being run on 3.9, and then check that both entry
points actually consult the guard before they import anything of the application's.
"""
import re
from pathlib import Path

from pyversion import MIN_PYTHON, too_old

ROOT = Path(__file__).resolve().parent.parent


def test_a_new_enough_interpreter_is_not_stopped():
    assert too_old((3, 13, 1)) == ""
    assert too_old(MIN_PYTHON + (0,)) == ""


def test_an_old_interpreter_is_told_what_it_has_and_what_it_needs():
    msg = too_old((3, 9, 6))
    assert "3.10" in msg, "the message has to name the version to install"
    assert "3.9.6" in msg, "and the one that is running, or the reader cannot tell which python ran"


def test_both_entry_points_check_before_importing_the_app():
    """Order is the whole point: a check after `from app import ...` never runs on the version it is there for."""
    for name in ("run_web.py", "run_desktop.py"):
        source = (ROOT / name).read_text(encoding="utf-8")
        guard = source.index("too_old()")
        first_app_import = min(
            m.start() for m in re.finditer(r"^\s*from app(\.|\s+import)", source, re.M)
        )
        assert guard < first_app_import, f"{name} imports the app before checking the Python version"

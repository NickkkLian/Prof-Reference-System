"""pyversion.py — the one thing both entry points check before they import anything of the application's.

The modules under app/ annotate with `float | None`, which Python 3.9 cannot evaluate at import time, and macOS still
ships 3.9 as /usr/bin/python3. Without this check the first thing a reader following the README sees is a TypeError
raised inside app/database.py, six frames deep and about an operand, instead of a sentence naming the version they
need. This file, and the two entry points that import it, stay parseable by 3.9 on purpose — so keep the annotations
here to the old syntax.
"""
import sys

MIN_PYTHON = (3, 10)


def too_old(version=None):
    """The message to print instead of letting the import fail, or "" when this interpreter is new enough.

    `version` is the three-part version to judge, so a test can ask what a 3.9 reader would be told without being
    run on 3.9; the entry points pass nothing and get this interpreter."""
    version = tuple(version or sys.version_info[:3])
    if version >= MIN_PYTHON:
        return ""
    have = "%d.%d.%d" % version
    return ("Letterkeep needs Python %d.%d or newer; this interpreter is %s (%s).\n"
            "macOS ships 3.9 as /usr/bin/python3 — install a newer Python (python.org, Homebrew or pyenv) and run\n"
            "the same command with that one." % (MIN_PYTHON[0], MIN_PYTHON[1], have, sys.executable))

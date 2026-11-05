"""Shared Vancouver timestamps and file-size labels."""

from datetime import datetime, timedelta, timezone


# Since 2026-11-01, B.C. stays on UTC-7 year-round instead of falling back.
# Use a fixed offset: the host's time-zone database may still contain old rules.
_VANCOUVER = timezone(timedelta(hours=-7))


def vancouver_time(timestamp: float | None = None) -> datetime:
    """Return an aware UTC-7 datetime for now, or for a POSIX file timestamp."""
    if timestamp is None:
        return datetime.now(_VANCOUVER)
    return datetime.fromtimestamp(timestamp, _VANCOUVER)


def format_file_size(size: int) -> str:
    """Use bytes for small files and one decimal place for KB and MB."""
    if size < 1024:
        return f"{size} B"
    if size < 1024**2:
        return f"{size / 1024:.1f} KB"
    return f"{size / 1024**2:.1f} MB"

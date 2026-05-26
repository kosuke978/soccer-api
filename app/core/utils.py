from __future__ import annotations

from datetime import datetime, timezone


def normalize_text(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def parse_iso_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def format_datetime(value: str | None, tz: timezone | None = None) -> str:
    if not value:
        return ""
    dt = parse_iso_datetime(value)
    if tz:
        dt = dt.astimezone(tz)
    return dt.strftime("%Y-%m-%d %H:%M")


def slot_label(slot: str) -> str:
    if slot.startswith("Best3rd-"):
        _, ordinal = slot.split("-", maxsplit=1)
        return f"Best 3rd {ordinal}"
    if slot.startswith("W-"):
        return f"Winner {slot[2:]}"
    if slot.startswith("L-"):
        return f"Loser {slot[2:]}"
    if len(slot) == 2 and slot[0].isalpha() and slot[1].isdigit():
        group = slot[0].upper()
        rank = slot[1]
        suffix = "th"
        if rank == "1":
            suffix = "st"
        elif rank == "2":
            suffix = "nd"
        elif rank == "3":
            suffix = "rd"
        return f"Group {group} {rank}{suffix}"
    return slot

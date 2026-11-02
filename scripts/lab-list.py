#!/usr/bin/env python3
"""Pretty lab list with Unicode-aware column widths."""
from __future__ import annotations

import pathlib
import sys
import unicodedata

root = pathlib.Path(sys.argv[1])


def width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text: str, size: int) -> str:
    return text + " " * max(0, size - width(text))


rows = []
for directory in sorted((root / "labs").glob("*/")):
    env = directory / "lab.env"
    if not env.exists():
        continue
    values = {}
    for line in env.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"')
    verified = (directory / "evidence" / "DONE").exists()
    noted = (directory / "evidence" / "note.md").exists()
    done = "x" if (verified and noted) else ("!" if verified else " ")
    rows.append(
        (
            values.get("LAB_ID", "?"),
            values.get("LAB_TITLE", ""),
            values.get("DOMAIN", ""),
            values.get("MINUTES", "?"),
            done,
        )
    )

w_id, w_title, w_domain, w_time = 2, 48, 22, 4
print(f"{pad('ID', w_id)}  {pad('TITLE', w_title)}  {pad('DOMAIN', w_domain)}  {pad('TIME', w_time)}  DONE")
for lab_id, title, domain, minutes, done in rows:
    if width(title) > w_title:
        title = title[: w_title - 1].rstrip() + "…"
    print(
        f"{pad(lab_id, w_id)}  {pad(title, w_title)}  {pad(domain, w_domain)}  "
        f"{pad(str(minutes) + 'm', w_time)}  [{done}]"
    )
verified_only = sum(1 for row in rows if row[4] == "!")
print(f"\n{sum(1 for row in rows if row[4] == 'x')}/{len(rows)} labs complete")
if verified_only:
    print(f"{verified_only} lab(s) verified but missing evidence/note.md  ->  ./bin/lab note <id>")

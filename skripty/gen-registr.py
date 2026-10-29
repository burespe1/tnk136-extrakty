#!/usr/bin/env python3
"""Sestaví extrakty.json z metadat (YAML hlavičky) Markdownu v extrakty/<WG>/*.md.

Použití:
    python skripty/gen-registr.py
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import yaml

KOREN = Path(__file__).resolve().parent.parent
EXTRAKTY = KOREN / "extrakty"
REGISTR = KOREN / "extrakty.json"
POLE = ["kod", "wg", "typ", "oznaceni", "zkratka", "nazev", "vydani", "stran", "zpracovano", "upraveno", "ics"]


def metadata(md: Path) -> dict:
    text = md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise SystemExit(f"{md.relative_to(KOREN)}: chybí hlavička s metadaty (--- … ---)")
    meta = yaml.safe_load(text.split("---", 2)[1]) or {}
    for povinne in ("kod", "wg", "typ", "oznaceni", "nazev", "vydani", "zpracovano"):
        if not meta.get(povinne):
            raise SystemExit(f"{md.relative_to(KOREN)}: v metadatech chybí „{povinne}“")
    ocekavany = f"{meta['kod']}_{meta['vydani']}"
    if md.stem != ocekavany:
        print(f"pozor: {md.relative_to(KOREN)} by se podle metadat měl jmenovat {ocekavany}.md")
    z = {k: meta.get(k) for k in POLE if meta.get(k) not in (None, "")}
    z["md"] = md.relative_to(KOREN).as_posix()
    return z


def klic(z: dict):
    return (z["wg"], [int(c) for c in re.findall(r"\d+", str(z["kod"]))], int(z["vydani"]))


def main() -> int:
    polozky = sorted((metadata(md) for md in EXTRAKTY.glob("TC*/*.md")), key=klic)
    REGISTR.write_text(json.dumps({"vygenerovano": date.today().isoformat(), "extrakty": polozky},
                                  ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Zapsáno {REGISTR.name}: {len(polozky)} extraktů.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

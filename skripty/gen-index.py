#!/usr/bin/env python3
"""Přegeneruje index.md z registru extrakty.json.

Použití:
    python skripty/gen-index.py
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

KOREN = Path(__file__).resolve().parent.parent
REGISTR = KOREN / "extrakty.json"
INDEX = KOREN / "index.md"

NAZVY_WG = {
    "TC278WG4": "WG4 – Dopravní a cestovní informace (TTI)",
    "TC278WG5": "WG5 – Elektronický výběr poplatků (EFC)",
    "TC278WG7": "WG7 – Geografické datové soubory a určování polohy",
    "TC278WG12": "WG12 – Automatická identifikace vozidel a zařízení (AVI/AEI)",
}
PORADI_WG = ["TC278WG4", "TC278WG5", "TC278WG7", "TC278WG12"]


def radek(z: dict) -> str:
    extrakt = str(z["zpracovano"]) + (f" (akt. {z['upraveno']})" if z.get("upraveno") else "")
    nazev = str(z["nazev"]).replace("|", "\\|")
    return (f"| {z['oznaceni']}:{z['vydani']} | {z.get('zkratka') or ''} | {nazev} | {extrakt} "
            f"| [{Path(z['md']).name}]({z['md']}) |")


def main() -> int:
    if not REGISTR.exists():
        raise SystemExit("Chybí extrakty.json – spusť nejdřív skripty/gen-registr.py.")
    polozky = json.loads(REGISTR.read_text(encoding="utf-8"))["extrakty"]
    radky = [
        "# 📚 Index extraktů",
        "",
        "Přehled extraktů z technických norem pro ITS. Sloupec **Norma** uvádí popisované",
        "vydání ISO/CEN, sloupec **Extrakt** rok zpracování (a poslední věcné úpravy) extraktu.",
        "",
        f"Soubor je generovaný skriptem `skripty/gen-index.py`, naposledy {date.today().isoformat()}.",
        "Needituj ho ručně – změny se při příštím běhu ztratí.",
        "",
    ]
    wgs = sorted({z["wg"] for z in polozky}, key=lambda w: (PORADI_WG.index(w) if w in PORADI_WG else 99, w))
    for wg in wgs:
        radky += [f"## {NAZVY_WG.get(wg, wg)}", "",
                  "| Norma | Zkratka | Název | Extrakt | Markdown |", "|---|---|---|---|---|"]
        radky += [radek(z) for z in polozky if z["wg"] == wg]
        radky.append("")
    radky += ["---", "", f"Celkem {len(polozky)} extraktů.", ""]
    INDEX.write_text("\n".join(radky), encoding="utf-8")
    print(f"Zapsáno {INDEX.name}: {len(polozky)} extraktů.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

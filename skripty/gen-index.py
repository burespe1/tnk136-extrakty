#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Přegeneruje index.md z registru extrakty.json.

Použití:
    python skripty/gen-index.py
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

KOREN = Path(__file__).resolve().parent.parent
REGISTR = KOREN / "extrakty.json"
INDEX = KOREN / "index.md"

NAZVY_WG = {
    "TC278WG4": "WG4 – Dopravní a cestovní informace (TTI)",
    "TC278WG7": "WG7 – Geografické datové soubory a určování polohy",
    "TC278WG12": "WG12 – Automatický výběr poplatků a kontrola přístupu",
}


def odkaz_cesta(cesta: str) -> str:
    """Závorky v názvech souborů by rozbily odkaz, proto je zakóduje."""
    return cesta.replace("(", "%28").replace(")", "%29").replace(" ", "%20")


def radek(z: dict) -> str:
    md_cesta = KOREN / z["md"]
    if md_cesta.exists():
        odkaz = f"[{Path(z['md']).name}]({odkaz_cesta(z['md'])})"
    else:
        odkaz = "–"
    doc = f"[.{Path(z['doc']).suffix.lstrip('.')}]({odkaz_cesta(z['doc'])})" if z.get("doc") else "–"
    rok = z.get("rok_vydani") or z.get("rok_extraktu") or ""
    return "| {kod} | {rok} | {zkratka} | {nazev} | {md} | {doc} |".format(
        kod=z["kod"], rok=rok, zkratka=z.get("zkratka") or "",
        nazev=z.get("nazev") or z.get("oznaceni") or "", md=odkaz, doc=doc,
    )


def main() -> int:
    if not REGISTR.exists():
        raise SystemExit("Chybí extrakty.json – spusť nejdřív skripty/gen-registr.py.")
    polozky = json.loads(REGISTR.read_text(encoding="utf-8"))["extrakty"]

    radky = [
        "# 📚 Index extraktů",
        "",
        "Přehled extraktů z technických norem pro ITS. Sloupec **Markdown** vede na",
        "vygenerovaný extrakt, sloupec **Zdroj** na originál ve Wordu, ze kterého vznikl.",
        "",
        f"Soubor je generovaný skriptem `skripty/gen-index.py`, naposledy {date.today().isoformat()}.",
        "Needituj ho ručně – změny se při příštím běhu ztratí.",
        "",
    ]

    for wg in sorted({z["wg"] for z in polozky}):
        vybrane = [z for z in polozky if z["wg"] == wg]
        vybrane.sort(key=lambda z: [int(c) for c in re.findall(r"\d+", z["kod"])])
        radky += [
            f"## {NAZVY_WG.get(wg, wg)}",
            "",
            "| Norma | Vydání | Zkratka | Název | Markdown | Zdroj |",
            "|---|---|---|---|---|---|",
        ]
        radky += [radek(z) for z in vybrane]
        radky.append("")

    celkem = len(polozky)
    s_md = sum(1 for z in polozky if (KOREN / z["md"]).exists())
    radky += [
        "---",
        "",
        f"Celkem {celkem} extraktů, z toho {s_md} dostupných v Markdownu.",
        "",
    ]

    INDEX.write_text("\n".join(radky), encoding="utf-8")
    print(f"Zapsáno {INDEX.name}: {celkem} extraktů, {s_md} v Markdownu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sestaví extrakty.json – registr všech extraktů v repozitáři.

Projde extrakty/doc/<WG>/ a extrakty/md/<WG>/, spáruje je podle kódu normy
a doplní metadata z extrakty/list-of-stds.txt a z index.md.

Stávající názvy .md souborů zůstávají zachovány – registr se jim přizpůsobí,
aby se při první konverzi nic nepřejmenovalo. Nový extrakt dostane název
podle svého .docx: extract_<kod>_(<rok>).docx → <kod>_<rok>.md

Použití:
    python skripty/gen-registr.py
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

KOREN = Path(__file__).resolve().parent.parent
DOC_DIR = KOREN / "extrakty" / "doc"
MD_DIR = KOREN / "extrakty" / "md"
SEZNAM = KOREN / "extrakty" / "list-of-stds.txt"
INDEX = KOREN / "index.md"
REGISTR = KOREN / "extrakty.json"

DOC_VZOR = re.compile(r"^extract_(?P<kod>\d{4,5}(?:-\d+)?)_\((?P<rok>\d{4})\)$", re.I)
MD_VZOR = re.compile(r"^(?P<kod>\d{4,5}(?:-\d+)?)_+(?P<rok>\d{4})$")


def klic(kod: str) -> str:
    """Sjednotí zápis kódu: 21219-05 i 21219-5 dají 21219-5."""
    if "-" in kod:
        zaklad, cast = kod.split("-", 1)
        return f"{zaklad}-{int(cast)}"
    return kod


def nacti_seznam_norem() -> dict[str, str]:
    """Z list-of-stds.txt vrátí kód → označení normy (ČSN EN ISO …)."""
    if not SEZNAM.exists():
        return {}
    vysledek: dict[str, str] = {}
    for radek in SEZNAM.read_text(encoding="utf-8-sig").splitlines()[1:]:
        if "\t" not in radek:
            continue
        _, norma = radek.split("\t", 1)
        norma = norma.strip()
        m = re.search(r"(\d{4,5}(?:-\d+)?)", norma)
        if m:
            vysledek.setdefault(klic(m.group(1)), norma)
    return vysledek


def nacti_index() -> dict[str, dict]:
    """Ze stávajícího index.md vytáhne zkratku a název, ať se neztratí."""
    if not INDEX.exists():
        return {}
    vysledek: dict[str, dict] = {}
    for radek in INDEX.read_text(encoding="utf-8").splitlines():
        if not radek.startswith("|"):
            continue
        bunky = [b.strip() for b in radek.strip().strip("|").split("|")]
        if len(bunky) < 4 or not re.match(r"^\d{4,5}", bunky[0]):
            continue
        vysledek[klic(bunky[0])] = {"zkratka": bunky[2], "nazev": bunky[3]}
    return vysledek


def metadata_z_md(cesta: Path) -> dict:
    """Z Markdownu vytáhne rok vydání a počet stran."""
    if not cesta.exists():
        return {}
    for radek in cesta.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^Vydána\s+(\d{4})(?:,\s*(\d+)\s*stran)?", radek.strip())
        if m:
            out: dict = {"rok_vydani": int(m.group(1))}
            if m.group(2):
                out["stran"] = int(m.group(2))
            return out
    return {}


def main() -> int:
    oznaceni = nacti_seznam_norem()
    z_indexu = nacti_index()

    # --- Markdown, který už existuje: jeho název je závazný -----------------
    md_podle_klice: dict[tuple[str, str], Path] = {}
    for cesta in sorted(MD_DIR.rglob("*.md")):
        m = MD_VZOR.match(cesta.stem)
        if not m:
            print(f"Pozor: název {cesta.relative_to(KOREN)} neodpovídá konvenci, vynechávám.")
            continue
        md_podle_klice[(cesta.parent.name, klic(m.group("kod")))] = cesta

    # --- Word: zdroj pravdy -------------------------------------------------
    podle_klice: dict[tuple[str, str], list[tuple[int, Path]]] = {}
    for cesta in sorted(DOC_DIR.rglob("*")):
        if cesta.suffix.lower() not in {".doc", ".docx"} or cesta.name.startswith("~$"):
            continue
        m = DOC_VZOR.match(cesta.stem)
        if not m:
            print(f"Pozor: název {cesta.relative_to(KOREN)} neodpovídá konvenci, vynechávám.")
            continue
        k = (cesta.parent.name, klic(m.group("kod")))
        podle_klice.setdefault(k, []).append((int(m.group("rok")), cesta))

    polozky: list[dict] = []
    for (wg, k), varianty in sorted(podle_klice.items()):
        varianty.sort()                      # nejstarší první
        rok, docx = varianty[-1]             # platná je nejnovější
        starsi = [str(c.relative_to(KOREN)).replace("\\", "/") for _, c in varianty[:-1]]
        kod_v_nazvu = DOC_VZOR.match(docx.stem).group("kod")

        md = md_podle_klice.pop((wg, k), None)
        if md is None:
            md = MD_DIR / wg / f"{kod_v_nazvu}_{rok}.md"

        zaznam = {
            "kod": k,
            "wg": wg,
            "oznaceni": oznaceni.get(k, ""),
            "nazev": z_indexu.get(k, {}).get("nazev", ""),
            "zkratka": z_indexu.get(k, {}).get("zkratka", ""),
            "rok_extraktu": rok,
            "doc": str(docx.relative_to(KOREN)).replace("\\", "/"),
            "md": str(md.relative_to(KOREN)).replace("\\", "/"),
            "prevoditelny": docx.suffix.lower() == ".docx",
        }
        zaznam.update(metadata_z_md(md))
        if starsi:
            zaznam["starsi_vydani"] = starsi
        polozky.append(zaznam)

    # --- Markdown bez zdrojového Wordu -------------------------------------
    for (wg, k), md in sorted(md_podle_klice.items()):
        zaznam = {
            "kod": k,
            "wg": wg,
            "oznaceni": oznaceni.get(k, ""),
            "nazev": z_indexu.get(k, {}).get("nazev", ""),
            "zkratka": z_indexu.get(k, {}).get("zkratka", ""),
            "doc": None,
            "md": str(md.relative_to(KOREN)).replace("\\", "/"),
            "prevoditelny": False,
        }
        zaznam.update(metadata_z_md(md))
        polozky.append(zaznam)

    polozky.sort(key=lambda z: (z["wg"], [int(c) for c in re.findall(r"\d+", z["kod"])]))

    REGISTR.write_text(
        json.dumps(
            {"vygenerovano": date.today().isoformat(), "extrakty": polozky},
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    s_md = sum(1 for z in polozky if (KOREN / z["md"]).exists())
    k_prevodu = sum(1 for z in polozky if z["prevoditelny"])
    jen_doc = sum(1 for z in polozky if z["doc"] and not z["prevoditelny"])
    print(
        f"Zapsáno {len(polozky)} extraktů do {REGISTR.name}: "
        f"{s_md} má Markdown, {k_prevodu} lze převést z .docx, "
        f"{jen_doc} je jen ve starém .doc."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

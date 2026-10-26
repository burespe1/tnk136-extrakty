#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Převod extraktů z Wordu do Markdownu.

Zdrojem pravdy je .docx v extrakty/doc/<WG>/. Markdown v extrakty/md/<WG>/
a obrázky v extrakty/md/<WG>/img/ se generují tímto skriptem.

Použití:
    python skripty/docx2md.py                 # převede, co je potřeba
    python skripty/docx2md.py 14819-1         # jen vybrané kódy norem
    python skripty/docx2md.py --vse           # převede znovu i to, co je aktuální
    python skripty/docx2md.py --kontrola      # nic nezapisuje, jen ohlásí rozdíly

Vyžaduje pandoc. Staré binární .doc se převedou přes LibreOffice (soffice),
pokud je k dispozici; jinak se přeskočí.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent.parent
REGISTR = KOREN / "extrakty.json"

TITULEK = "EXTRAKT z české technické normy"
OBRAZKOVE_PRIPONY = {".png", ".jpg", ".jpeg", ".gif", ".emf", ".wmf", ".bmp", ".tif", ".tiff"}


def nacti_registr() -> list[dict]:
    if not REGISTR.exists():
        sys.exit(f"Chybí registr {REGISTR}. Spusť nejdřív skripty/gen-registr.py.")
    return json.loads(REGISTR.read_text(encoding="utf-8"))["extrakty"]


# --------------------------------------------------------------------------
# konverze
# --------------------------------------------------------------------------

def doc_na_docx(zdroj: Path, kam: Path) -> Path | None:
    """Starý binární .doc převede přes LibreOffice na .docx."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return None
    subprocess.run(
        [soffice, "--headless", "--convert-to", "docx", "--outdir", str(kam), str(zdroj)],
        check=True, capture_output=True, timeout=300,
    )
    vysledek = kam / (zdroj.stem + ".docx")
    return vysledek if vysledek.exists() else None


def titulek_z_docx(docx: Path) -> str:
    """Titulek extraktu je ve Wordu v textovém poli, pandoc ho zahazuje.

    Vytáhneme ho proto přímo z dokumentu. Liší se podle druhu dokumentu
    ("z české technické normy" vs. "z technické specifikace ISO").
    """
    try:
        with zipfile.ZipFile(docx) as z:
            xml = z.read("word/document.xml").decode("utf-8", "replace")
    except Exception:
        return TITULEK
    for odstavec in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
        text = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", odstavec, re.S))
        text = " ".join(html.unescape(re.sub(r"<[^>]+>", "", text)).split())
        # text ze tvarů Wordu občas nese na začátku souřadnice obrazce
        m = re.search(r"EXTRAKT\s+z\s+.{3,80}", text)
        if m:
            return m.group(0).strip()
    return TITULEK


def pandoc(docx: Path, media_dir: Path) -> str:
    hotovo = subprocess.run(
        [
            "pandoc", str(docx),
            "--from", "docx",
            "--to", "gfm",
            "--wrap", "none",
            "--extract-media", str(media_dir),
        ],
        check=True, capture_output=True, timeout=300,
    )
    return hotovo.stdout.decode("utf-8")


# --------------------------------------------------------------------------
# úpravy vygenerovaného Markdownu
# --------------------------------------------------------------------------

def _bez_znacek(s: str) -> str:
    s = re.sub(r"<[^>]+>", "\n", s)
    return html.unescape(s)


def hlavicka(text: str) -> str:
    """Nahradí hlavičkovou tabulku extraktu čitelnými řádky.

    Word má v hlavičce jednořádkovou tabulku: název normy | označení + třídicí
    znak. Pandoc z ní udělá buď syrové HTML, nebo rozbitou pipe tabulku, kde
    označení a třídicí znak splynou ("ČSN EN ISO 14819-101 8253"). Obojí
    převedeme na název tučně a pod ním označení s třídicím znakem.
    """

    def slozeni(nazev: str, zbytek: list[str]) -> str:
        radky = []
        if nazev:
            radky += [f"**{nazev}**", ""]
        oznaceni = tridici = ""
        slepene = " ".join(z for z in zbytek if z)
        m = re.match(r"^(?P<ozn>.*?)\s*(?P<tz>\d{2}\s?\d{4})\s*$", slepene)
        if m:
            oznaceni, tridici = m.group("ozn").strip(), m.group("tz").strip()
        else:
            oznaceni = slepene.strip()
        if oznaceni and tridici:
            radky += [f"{oznaceni} — třídicí znak {tridici}", ""]
        elif oznaceni:
            radky += [oznaceni, ""]
        return "\n".join(radky)

    # a) syrové HTML z pandoku
    def z_html(m: re.Match) -> str:
        bunky = [
            " ".join(_bez_znacek(b).split())
            for b in re.findall(r"<td[^>]*>(.*?)</td>", m.group(0), re.S)
        ]
        if not bunky:
            return m.group(0)
        # druhá buňka má označení a třídicí znak ve dvou odstavcích
        syrove = re.findall(r"<td[^>]*>(.*?)</td>", m.group(0), re.S)
        zbytek: list[str] = []
        for b in syrove[1:]:
            zbytek += [" ".join(_bez_znacek(x).split()) for x in re.split(r"</p>", b)]
        return slozeni(bunky[0], zbytek)

    novy = re.sub(r"<table>.*?</table>", z_html, text, count=1, flags=re.S)
    if novy != text:
        return novy

    # b) pipe tabulka
    radky = text.split("\n")
    for i, radek in enumerate(radky):
        if not radek.startswith("|") or "ČSN" not in radek:
            continue
        if i + 1 >= len(radky) or set(radky[i + 1].replace("|", "").replace(" ", "")) > {"-", ":"}:
            continue
        bunky = [b.strip() for b in radek.strip().strip("|").split("|")]
        nahrada = slozeni(bunky[0] if bunky else "", bunky[1:])
        return "\n".join(radky[:i] + nahrada.split("\n") + radky[i + 2:])
    return text


def bez_zdvojeneho_titulku(text: str, titulek: str) -> str:
    """Titulek bývá v dokumentu i jako tučný odstavec; necháme jen nadpis."""
    vzor = re.compile(
        r"^(?:!\[[^\]]*\]\([^)]*\))?\s*\*\*" + re.escape(titulek) + r"\*\*\s*$",
        re.M,
    )
    return vzor.sub("", text, count=1)


def zanor_nadpisy(text: str) -> str:
    """Posune nadpisy o úroveň níž, ať je titulek extraktu jediná jednička."""
    return re.sub(r"^(#{1,5})(?= )", r"#\1", text, flags=re.M)


def popisky_obrazku(text: str) -> str:
    """Popisek pod obrázkem přenese do alternativního textu a sjednotí jeho zápis.

    Ve Wordu je popisek samostatný odstavec ("Obrázek 3 - Ukázka metody ...").
    V Markdownu z něj uděláme alt text obrázku a řádek "**Obr. 3** Ukázka ...",
    aby byl obrázek popsaný i tam, kde se nenačte.
    """
    vzor = re.compile(
        r"^(?P<pred>>[ \t]*)?(?P<img>!\[\]\((?P<src>[^)]+)\))[ \t]*\n"
        r"\n"
        r"(?P<druh>Obrázek|Obr\.|Tabulka|Tab\.)[ \t]*(?P<cislo>\d+)[ \t]*[-–—:]?[ \t]*(?P<popis>[^\n]+)$",
        re.M,
    )

    def nahrad(m: "re.Match") -> str:
        popis = m.group("popis").strip()
        zkratka = "Tab." if m.group("druh").startswith(("Tabulka", "Tab")) else "Obr."
        alt = popis.replace("[", "(").replace("]", ")")
        return (
            f"{m.group('pred') or ''}![{alt}]({m.group('src')})\n"
            f"**{zkratka} {m.group('cislo')}** {popis}"
        )

    return vzor.sub(nahrad, text)


PREVEST_NA_PNG = {".emf", ".wmf", ".bmp", ".tif", ".tiff"}


def na_png(cesta: Path) -> Path:
    """EMF/WMF a další formáty, které GitHub nezobrazí, převede LibreOffice na PNG.

    Když LibreOffice chybí nebo převod selže, vrátí původní soubor.
    """
    if cesta.suffix.lower() not in PREVEST_NA_PNG:
        return cesta
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return cesta
    try:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "png", "--outdir", str(cesta.parent), str(cesta)],
            capture_output=True, timeout=120, check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return cesta
    png = cesta.with_suffix(".png")
    return png if png.exists() and png.stat().st_size > 0 else cesta


def presun_obrazky(text: str, media_dir: Path, img_dir: Path, zaklad: str) -> str:
    """Média vytažená pandocem přejmenuje na <zaklad>_imageN.<ext> a přesune do img/.

    Číslují se podle pořadí výskytu v textu; obrázky, na které po úklidu nic
    neodkazuje (typicky pozadí textových polí), se nekopírují.
    """
    dostupne = {
        p.name: p
        for p in media_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in OBRAZKOVE_PRIPONY
    }
    if not dostupne:
        return text
    dostupne = {jmeno: na_png(cesta) for jmeno, cesta in dostupne.items()}

    prejmenovani: dict[str, str] = {}

    def oprav(m: "re.Match") -> str:
        jmeno = re.split(r"[\\/]", m.group("cesta"))[-1]
        if jmeno not in dostupne:
            return m.group(0)
        novy = prejmenovani.get(jmeno)
        if novy is None:
            novy = f"{zaklad}_image{len(prejmenovani) + 1}{dostupne[jmeno].suffix.lower()}"
            prejmenovani[jmeno] = novy
        return f"{m.group('pred')}(./img/{novy})"

    text = re.sub(r"(?P<pred>!\[[^\]]*\])\((?P<cesta>[^)]+)\)", oprav, text)

    # obrázky uvnitř tabulek, které pandoc nechal v HTML
    def oprav_html(m: "re.Match") -> str:
        nahrada = oprav(re.match(r"(?P<pred>)\((?P<cesta>[^)]+)\)", f"({m.group('cesta')})"))
        return f'{m.group("pred")}{nahrada[1:-1]}"' if nahrada.startswith("(") else m.group(0)

    text = re.sub(r'(?P<pred><img src=")(?P<cesta>[^"]+)"', oprav_html, text)

    if prejmenovani:
        img_dir.mkdir(parents=True, exist_ok=True)
        for puvodni, novy in prejmenovani.items():
            shutil.copy2(dostupne[puvodni], img_dir / novy)
    return text


def kurziva_podtrzitkem(text: str) -> str:
    """Pandoc píše kurzívu hvězdičkami, v repozitáři se drží podtržítka."""
    return re.sub(r"(?<!\*)\*(?!\*)([^*\n]+?)\*(?!\*)", r"_\1_", text)


def uklid_text(text: str) -> str:
    text = kurziva_podtrzitkem(text)
    text = text.replace(" ", " ")
    text = re.sub(r"^\s*[•●]\s+", "- ", text, flags=re.M)
    # podtržení odkazu ve Wordu převádí pandoc na <span class="underline">, v Markdownu je zbytečné
    text = re.sub(r'<span class="underline">(.*?)</span>', r"\1", text)
    text = re.sub(r"[ \t]+$", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def prevod(docx: Path, img_dir: Path, zaklad: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        zdroj = docx
        if docx.suffix.lower() == ".doc":
            prevedeny = doc_na_docx(docx, tmp_path)
            if prevedeny is None:
                raise RuntimeError("starý formát .doc a není k dispozici LibreOffice")
            zdroj = prevedeny
        media_dir = tmp_path / "media"
        titulek = titulek_z_docx(docx)
        text = pandoc(zdroj, media_dir)
        text = text.replace("\u00a0", " ")  # Word sype nezlomitelné mezery
        text = hlavicka(text)
        text = zanor_nadpisy(text)
        text = bez_zdvojeneho_titulku(text, titulek)
        text = popisky_obrazku(text)
        text = presun_obrazky(text, media_dir, img_dir, zaklad)
        return uklid_text(f"# {titulek}\n\n{text}")


# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Převede extrakty z Wordu do Markdownu.")
    ap.add_argument("kody", nargs="*", help="kódy norem k převodu (např. 14819-1); bez nich se bere vše")
    ap.add_argument("--vse", action="store_true", help="převést i to, co je aktuální")
    ap.add_argument("--kontrola", action="store_true", help="nic nezapisovat, jen ohlásit rozdíly")
    ap.add_argument("--soubory", nargs="+", metavar="CESTA",
                    help="převést jen extrakty s těmito zdrojovými Wordy (cesty od kořene repozitáře)")
    args = ap.parse_args()

    if not shutil.which("pandoc"):
        sys.exit("Chybí pandoc. Nainstaluj ho a spusť znovu.")

    polozky = nacti_registr()
    if args.soubory:
        chtene_doc = {Path(s).as_posix() for s in args.soubory}
        polozky = [p for p in polozky if p.get("doc") in chtene_doc]
        args.vse = True                 # v CI nejde spoléhat na čas změny souborů
        if not polozky:
            print("Žádný z uvedených Wordů není v registru, není co převádět.")
            return 0
    if args.kody:
        chtene = set(args.kody)
        polozky = [p for p in polozky if p["kod"] in chtene]
        if not polozky:
            sys.exit("Žádný z uvedených kódů není v registru.")

    prevedeno = aktualni = preskoceno = chyby = 0

    for p in polozky:
        if not p.get("doc"):
            continue
        docx = KOREN / p["doc"]
        md_cil = KOREN / p["md"]
        if not docx.exists():
            print(f"CHYBÍ      {p['kod']}: {p['doc']}")
            chyby += 1
            continue
        if not args.vse and md_cil.exists() and md_cil.stat().st_mtime >= docx.stat().st_mtime:
            aktualni += 1
            continue

        try:
            if args.kontrola:
                # při kontrole se nesmí nic zapsat, ani obrázky
                with tempfile.TemporaryDirectory() as t:
                    text = prevod(docx, Path(t) / "img", md_cil.stem)
            else:
                text = prevod(docx, md_cil.parent / "img", md_cil.stem)
        except RuntimeError as e:
            print(f"PŘESKOČENO {p['kod']}: {e}")
            preskoceno += 1
            continue
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            chyba = getattr(e, "stderr", b"") or b""
            radky = chyba.decode("utf-8", "replace").strip().splitlines()
            print(f"CHYBA      {p['kod']}: {radky[-1] if radky else e}")
            chyby += 1
            continue

        if args.kontrola:
            stary = md_cil.read_text(encoding="utf-8") if md_cil.exists() else ""
            print(f"{'beze změny' if stary == text else 'LIŠÍ SE':11} {p['kod']} → {p['md']}")
        else:
            md_cil.parent.mkdir(parents=True, exist_ok=True)
            md_cil.write_text(text, encoding="utf-8")
            print(f"PŘEVEDENO  {p['kod']} → {p['md']}")
        prevedeno += 1

    print(
        f"\nHotovo: {prevedeno} převedeno, {aktualni} už bylo aktuálních, "
        f"{preskoceno} přeskočeno, {chyby} chyb."
    )
    return 1 if chyby else 0


if __name__ == "__main__":
    raise SystemExit(main())

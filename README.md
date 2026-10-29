## 📘 Extrakty z technických norem pro ITS

Tento projekt slouží k přípravě, správě a publikaci extraktů z technických norem v oblasti Inteligentních dopravních systémů (ITS). Extrakty jsou zjednodušené verze norem, které usnadňují jejich pochopení a aplikaci v praxi.

## 📘 Index extraktů

Seznam všech dostupných extraktů najdete v souboru [index.md](index.md). Obsahuje popisovaná vydání norem a odkazy na jednotlivé extrakty.

Pro strojové zpracování je k dispozici také [extrakty.json](extrakty.json), který obsahuje metadata pro každý extrakt.


## 🌐 Online rozhraní

Hotové extrakty jsou dostupné na [www.standardland.cz](https://www.standardland.cz) – znalostní databázi, která umožňuje:
- Vyhledávání norem podle tématu, oblasti nebo typu
- Prohlížení extraktů ve zkrácené formě (cca 5 stran)
- Práci se slovníkem termínů a encyklopedií ITS
- Orientaci v evropské normalizaci dle Nařízení EP a Rady (EU) č. 1025/2013

## ✍️ Zdrojem pravdy je Markdown

Každý extrakt je jeden soubor `extrakty/<WG>/<kód>_<rok vydání>.md`, obrázky
jsou vedle v `img/`. Rok v názvu je rok vydání popisované normy ISO/CEN
(např. `14815_2005.md` popisuje EN ISO 14815:2005). Když existují extrakty
dvou vydání, jsou to dva soubory (`14819-1_2003.md`, `14819-1_2021.md`).

Na začátku souboru jsou metadata, ze kterých se skládá hlavička extraktu
i registr a index:

```yaml
---
kod: "21219-16"
wg: TC278WG4
typ: technická specifikace ISO     # evropská norma, mezinárodní norma ISO, technická specifikace/zpráva ISO/CEN
oznaceni: ISO/TS 21219-16
zkratka: TPEG2-FPI                 # nepovinné
nazev: "Inteligentní dopravní systémy – …"
vydani: 2016
stran: 62
zpracovano: 2020                   # rok zpracování extraktu
upraveno:                          # rok poslední věcné úpravy extraktu (nepovinné)
ics: "ICS …"                       # nepovinné, jen v registru (do záhlaví se podle metodiky neuvádí)
---
```

Text začíná nadpisem `## Úvod`, kapitoly jsou `##`, články `###`.
Popisky se píší jako samostatný odstavec `**Obr. 1** Text popisku` (pod
obrázkem) a `**Tab. 1** Text popisku` (nad tabulkou). Tabulky se sloučenými
buňkami jsou v HTML (`<table>…</table>`).

### Sestavení Wordu a PDF

```bash
python skripty/md2docx.py                                   # všechny extrakty → build/<WG>/*.docx a *.pdf
python skripty/md2docx.py extrakty/TC278WG4/14819-1_2021.md # jen vybraný
python skripty/md2docx.py extrakty/TC278WG7 --bez-pdf       # složka, jen docx
python skripty/gen-registr.py                               # extrakty.json z metadat
python skripty/gen-index.py                                 # index.md
```

Word se skládá podle šablony TNK 136 (`sablona/reference.docx`, filtr
`sablona/extrakt.lua`). Složka `build/` se do gitu neukládá. Potřebuje
pandoc 3 (`pip install pypandoc_binary`), Python balíčky `python-docx`,
`pyyaml`, `lxml`, `pillow` a pro PDF LibreOffice.

Na GitHubu sestaví totéž workflow `.github/workflows/build.yml`
(Actions → Sestavení extraktů → Run workflow); Word a PDF jsou ke stažení
jako artefakt běhu. Workflow do repozitáře nic nezapisuje.

## 💬 Připomínky

Připomínkuje se ve Wordu, práce s připomínkami do gitu nepatří.

1. Sestav Word (`md2docx.py`) a pošli ho připomínkujícím. Vrácené soubory
   ulož mimo repozitář, např. `C:\work-AI\tnk\pripominky\<kód>\<kód>_<rok>__<jméno>.docx`.
2. `python skripty/pripominky.py <vrácený.docx>` – vedle Wordu zapíše výpis
   komentářů (`.md` s tabulkou k odškrtání), přijme sledované změny a text
   převede zpět do zdrojového `.md` v repozitáři (metadata a obrázky zůstanou).
3. Zkontroluj `git diff`, nechtěné změny vrať, komentáře zapracuj ručně
   do `.md` a commitni. Při věcné úpravě nastav v metadatech `upraveno:`.

Nový extrakt napsaný ve Wordu převede `python skripty/docx2md.py NOVY.docx
extrakty/<WG>/<kód>_<rok>.md`; metadata se doplní podle ostatních extraktů.

## 📂 Struktura projektu

```plaintext
extrakty/<WG>/<kód>_<rok vydání>.md   # extrakt (zdroj pravdy)
extrakty/<WG>/img/                    # obrázky k extraktům
sablona/                              # šablona Wordu a filtr pro pandoc
skripty/
├── md2docx.py        # Markdown → docx a pdf (build/)
├── pripominky.py     # Word s připomínkami → výpis komentářů a text do .md
├── docx2md.py        # převod Word → Markdown (používá pripominky.py)
├── md_upravy.py      # sjednocení nadpisů, popisků a tabulek po převodu z Wordu
├── prijmi_revize.py, smazat_komentare.py
├── gen-registr.py    # sestaví extrakty.json
└── gen-index.py      # přegeneruje index.md
extrakty.json         # registr všech extraktů (generovaný)
index.md              # přehled s odkazy (generovaný)
metodika/             # metodika TNK 136, přílohy A–F a šablona Extrakt_šablona.docx (struktura jako extrakty v repozitáři)
```

Wordy ve stavu před přechodem na Markdown (29. 10. 2026) jsou v archivu
mimo repozitář (`archiv/extrakty-word-2026-10`) a v historii gitu.

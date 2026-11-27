# Pokyny pro práci v repozitáři tnk136-extrakty

Extrakty z technických norem ITS pro TNK 136 (Petr Bureš). Repozitář: GitHub `burespe1/tnk136-extrakty`
(starý remote `gitlab` už se nepoužívá). Lokální kopie: `C:\work-AI\tnk\extrakty\tnk136-extrakty`.

## Zásady

- **Zdrojem pravdy je Markdown** `extrakty/<WG>/<kód>_<rok vydání>.md`, obrázky v `extrakty/<WG>/img/`.
  Word a PDF se generují (`skripty/md2docx.py` → `build/`, není v gitu). Rok v názvu = rok vydání popisované normy ISO/CEN.
- **Metadata v YAML hlavičce** (kod, wg, typ, oznaceni, zkratka, nazev, vydani, stran, zpracovano, upraveno, ics).
  Hlavička extraktu uvádí vydání ISO/CEN, které extrakt popisuje (u CEN-ISO shodné), **ne české vydání**;
  ČSN, třídicí znak ani ICS se do záhlaví neuvádějí (ICS jen v metadatech). Zdroj údajů: standards.iteh.ai
  a Národní plán sekretariátu TNK 136.
- **Struktura extraktu:** Úvod (končí „Poznámka: Extrakt uvádí vybrané kapitoly popisovaného dokumentu a přejímá původní
  číslování kapitol.“), Užití, 1 Předmět, 2 Souvisící normy, 3 Termíny a definice (konec: „Další termíny a zkratky z oboru ITS
  jsou obsaženy ve slovníku ITS terminology.“), 4 Symboly a zkratky (konec: táž věta s „(www.ITSterminology.org)“),
  další kapitoly, přílohy. Čísla a názvy kapitol podle normy.
  Kapitola zkratek má vždy název „Symboly a zkratky“, i když ji norma nazývá „Abbreviated terms“ (číslo podle normy).
  Norma bez kapitoly „Normative references“: oddíl „Souvisící normy“ **bez čísla**, ostatní kapitoly číslované podle normy.
- **Obrázky** z norem se ponechávají v původním jazyce (nepřekládají se). Velikost: bez `{width=…}` je md2docx
  zmenší na nejvýš 12 × 8 cm; větší či menší rozměr zadat v md (`![popis](img/x.png){width=10cm}`).
- **Pole `zkratka`** v hlavičce (např. TPEG2-UMR, TPEG1-SSF) se uvádí, má-li ji norma v názvu.
- **Rozsah kapitol:** u kapitol (od kap. 5), příloh a klíčových článků uvádět rozsah ve stranách
  („Kapitola (rozsah 3 strany) stanovuje …“, „Příloha o rozsahu 7 stran …“).
- **Souvislý text:** souvětí se spojkami a návazností, ne holé věty; středníky v běžném textu nepoužívat (jen ve výčtech).
- **Popis kapitol – co, jak a do jakého detailu:** u delších kapitol, příloh a klíčových článků uvádět nejen, co stanovují,
  ale i jak (text, diagramy UML, tabulky polí, schémata XML, příklady) a do jaké podrobnosti (např. „každý atribut s definicí,
  oborem hodnot a jednotkou“), aby čtenář věděl, co v normě najde.
- **Normy zmíněné v textu** extraktu (předchozí vydání, navazující části souboru, přejaté koncepty) uvádět i v oddílu
  „Souvisící normy“ (normativní odkazy, nebo větou o bibliografii „… mj. …“).
- **Příklad:** krátký příklad (jedna věta, malý výpis nebo tabulka z normy) uvést tam, kde zásadně zlepší pochopení
  principu (zápis časové domény, struktura záznamu); jinak příklady nepřidávat.
- **Extrakt z FDIS** (vydaný text není k dispozici) lze převzít do repa; počet stran a ICS podle katalogu ISO/iteh.
- **Vložené prvky:** obrázky, tabulky a výpisy kódu číslované každé zvlášť od 1 v pořadí v extraktu; popisek v md
  `**Obr. N** text (obr. X popisovaného dokumentu)` pod obrázkem, `**Tab. N** …` nad tabulkou, `**Výpis N** …` pod blokem kódu;
  na každý prvek odkaz v textu („na obrázku 1“, „v tabulce 1“, „ve výpisu 1“).
  **Výpis kódu je text**, ne obrázek: blok ```` ```xml ````, ```` ```dtd ````, ```` ```asn1 ```` (zvýraznění syntaxe), pseudokód TPEG bez jazyka.
  **Tabulka je tabulka** (pipe, se sloučenými buňkami HTML); obrázek tabulky jen u složitých (piktogramy, diagram v buňce).
  Přečíslování a odkazy: `python skripty/precisluj.py SOUBOR.md [--nahled]`.
- **Metodika** v `metodika/` (přílohy A–F v0.2, `Extrakt_šablona.docx`) odpovídá této struktuře.
- **Texty norem nepatří do repozitáře** (autorská práva) – jsou v `C:\work-AI\tnk\normy\docs`.
- **Práce s připomínkami nepatří do gitu** (vrácené Wordy, výpisy komentářů) – ukládat mimo repo,
  např. `C:\work-AI\tnk\pripominky\<kód>\`. Do repa jen výsledný text.
- **Extrakty WG5 (EFC)** už nejsou v Petrově odpovědnosti – neupravovat bez výslovného pokynu.
- Styl textu: „extrakt není pohádka“ – zhuštěná informace, tvrdé věty (stanovuje, ne ukazuje/uvádí),
  „popisovaný dokument“ místo „norma“, výčet článků kapitoly jednou větou.

## Git

- Commituje Claude lokálně, **pushuje Petr sám**. Autor: `Petr Bures <burespe1@gmail.com>`.
- Zprávy commitů česky, s trailerem `Co-Authored-By: Claude …` a `Claude-Session: …`.
- Workflow `.github/workflows/build.yml` se spouští jen ručně a do repa nic nezapisuje.

## Nástroje

```bash
python skripty/md2docx.py [soubory|složky] [--bez-pdf]   # md → build/<WG>/*.docx, *.pdf (pandoc 3 přes pypandoc_binary, LibreOffice)
python skripty/pripominky.py VRACENY.docx [ZDROJ.md]       # Word s připomínkami → výpis komentářů + text do .md (kontrola git diff)
python skripty/docx2md.py NOVY.docx extrakty/<WG>/<kód>_<rok>.md   # nový extrakt z Wordu (pak doplnit metadata)
python skripty/gen-registr.py && python skripty/gen-index.py       # extrakty.json a index.md z metadat
```

Převod md → docx → md je stabilní (druhý průchod nic nemění); po ruční úpravě md lze kanonizovat
`md2docx.preved(md, pdf=False)` + `pripominky.prevezmi_text(docx, md)`.

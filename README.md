## 📘 Extrakty z technických norem pro ITS

Tento projekt slouží k přípravě, správě a publikaci extraktů z technických norem v oblasti Inteligentních dopravních systémů (ITS). Extrakty jsou zjednodušené verze norem, které usnadňují jejich pochopení a aplikaci v praxi.

## 📘 Index extraktů

Seznam všech dostupných extraktů najdete v souboru [index.md](index.md). Obsahuje přehled verzí a přímé odkazy na jednotlivé soubory.

Pro strojové zpracování je k dispozici také [extrakty.json](extrakty.json), který obsahuje metadata pro každý extrakt.


## 🌐 Online rozhraní

Hotové extrakty jsou dostupné na [www.standardland.cz](https://www.standardland.cz) – znalostní databázi, která umožňuje:
- Vyhledávání norem podle tématu, oblasti nebo typu
- Prohlížení extraktů ve zkrácené formě (cca 5 stran)
- Práci se slovníkem termínů a encyklopedií ITS
- Orientaci v evropské normalizaci dle Nařízení EP a Rady (EU) č. 1025/2013

## 🔄 Jak vzniká Markdown

Zdrojem pravdy je **Word**. Markdown v `extrakty/md/` a obrázky v
`extrakty/md/<WG>/img/` se generují – needituj je ručně, při příštím
převodu se změny ztratí. Opravy patří do `.docx` v `extrakty/doc/`.

```bash
python skripty/gen-registr.py        # sestaví extrakty.json ze souborů na disku
python skripty/docx2md.py            # převede, co se od posledně změnilo
python skripty/docx2md.py 14819-1    # jen vybraný extrakt
python skripty/docx2md.py --kontrola # nic nezapíše, jen ohlásí rozdíly
python skripty/docx2md.py --soubory extrakty/doc/TC278WG4/extract_14819-1_(2023).docx  # podle Wordu
python skripty/gen-index.py          # přegeneruje index.md
```

Na GitHubu totéž dělá workflow `.github/workflows/docx2md.yml`: po pushi
změněného `.docx` převede právě ty Wordy, které se v pushi změnily, a výsledek
commitne zpět. Ručně spuštěný workflow s volbou „vše“ převede všechno.

Potřebuje **pandoc**; staré binární `.doc` navíc **LibreOffice**.

### Co převod dělá

- titulek extraktu bere přímo z Wordu (je v textovém poli, pandoc ho zahazuje)
- hlavičkovou tabulku rozpadá na název, označení normy a třídicí znak
- popisek pod obrázkem přenáší do alternativního textu a sjednocuje na `**Obr. N**`
- obrázky ukládá jako `<název-extraktu>_imageN.<přípona>`, číslované podle pořadí v textu

## 📂 Struktura projektu

```plaintext
extrakty/
├── doc/<WG>/extract_<kód>_(<rok>).docx   # zdroj – Word
└── md/<WG>/<kód>_<rok>.md                # generovaný Markdown
    └── img/                              # obrázky k němu
skripty/
├── docx2md.py        # převod Word → Markdown
├── gen-registr.py    # sestaví extrakty.json
└── gen-index.py      # přegeneruje index.md
extrakty.json         # registr všech extraktů (generovaný)
index.md              # přehled s odkazy (generovaný)
MIGRACE.md            # přesun repozitáře z GitLabu na GitHub
```

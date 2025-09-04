# 📘 Extrakty z technických norem pro ITS

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

## 📂 Struktura projektu

```plaintext
📁 extrakty/
├── norma-xyz.md       # Markdown extrakt konkrétní normy
├── norma-abc.md       # Další extrakt
📁 skripty/
├── konverze-docx.py   # Skript pro převod DOCX → MD
📁 .
├── seznam-norem.json  # Metadata k extraktům
├── README.md
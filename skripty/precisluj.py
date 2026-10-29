#!/usr/bin/env python3
"""Přečísluje popisky Obr./Tab./Výpis v extraktu podle skutečného druhu prvku a upraví odkazy v textu.

Druh se určuje podle okolí popisku: blok kódu nad popiskem → Výpis, obrázek nad popiskem → Obr.,
tabulka pod popiskem → Tab. Odkazy na prvky popisovaného dokumentu („obr. 4 normy“,
„tabulka 2 popisovaného dokumentu“) se nemění. Použití: python precisluj.py SOUBOR.md [--nahled]
"""
import re, sys
from pathlib import Path

POP = re.compile(r'^\*\*(Obr\.|Tab\.|Výpis) (\d+)\*\*(.*)$')
CIZI = r'(?!\s*(?:popisovan|norm|dokument|ISO|EN|z\b|přílohy|v\s+norm))'

def druh_prvku(r, i, puvodni):
    """Výpis, když nad popiskem končí blok kódu; Tab., když pod ním začíná tabulka; jinak beze změny."""
    j = i - 1
    while j >= 0 and not r[j].strip(): j -= 1
    k = i + 1
    while k < len(r) and not r[k].strip(): k += 1
    if j >= 0 and r[j].strip() == '```': return 'Výpis'
    if k < len(r) and r[k].lstrip().startswith(('|', '<table')): return 'Tab.'
    return puvodni

TVARY = {  # (starý druh) → regex na odkaz v textu
    'Obr.': r'(?P<slovo>obrázek|obrázku|obrázkem|obrázky|obrázcích|obr\.)',
    'Tab.': r'(?P<slovo>tabulka|tabulky|tabulce|tabulku|tabulkou|tab\.)',
    'Výpis': r'(?P<slovo>výpis|výpisu|výpisem)',
}
PADY = {
    'Výpis': {'obrázek': 'výpis', 'obrázku': 'výpisu', 'obrázkem': 'výpisem', 'obr.': 'výpis', 'tabulka': 'výpis', 'tabulky': 'výpisu',
              'tabulce': 'výpisu', 'tabulku': 'výpis', 'tabulkou': 'výpisem', 'tab.': 'výpis'},
    'Tab.': {'obrázek': 'tabulka', 'obrázku': 'tabulce', 'obrázkem': 'tabulkou', 'obr.': 'tab.', 'výpis': 'tabulka', 'výpisu': 'tabulce', 'výpisem': 'tabulkou'},
    'Obr.': {'tabulka': 'obrázek', 'tabulky': 'obrázku', 'tabulce': 'obrázku', 'tabulku': 'obrázek', 'tabulkou': 'obrázkem', 'tab.': 'obr.',
             'výpis': 'obrázek', 'výpisu': 'obrázku', 'výpisem': 'obrázkem'},
}

def zpracuj(path, nahled=False):
    t = Path(path).read_text(encoding='utf-8'); r = t.split('\n')
    pocty = {'Obr.': 0, 'Tab.': 0, 'Výpis': 0}; mapa = {}; kod = False
    for i, l in enumerate(r):
        if l.strip().startswith('```'): kod = not kod; continue
        if kod: continue
        m = POP.match(l.strip())
        if not m: continue
        novy = druh_prvku(r, i, m.group(1))
        pocty[novy] += 1
        mapa.setdefault((m.group(1), m.group(2)), (novy, pocty[novy]))
        r[i] = f'**{novy} {pocty[novy]}**{m.group(3)}'
    zmeny = {k: v for k, v in mapa.items() if (k[0], int(k[1])) != v}
    # odkazy v textu (mimo popisky a kód); dvoufázově přes zástupné značky
    kod = False
    for i, l in enumerate(r):
        if l.strip().startswith('```'): kod = not kod; continue
        if kod or POP.match(l.strip()) or l.lstrip().startswith('!['): continue
        for (sd, sc), (nd, nc) in zmeny.items():
            def nahrad(m, nd=nd, nc=nc, sd=sd):
                slovo = m.group('slovo'); mal = slovo.lower()
                nove = PADY.get(nd, {}).get(mal, mal) if nd != sd else mal
                if slovo[:1].isupper(): nove = nove[:1].upper() + nove[1:]
                predlozka = m.group('pred') or ''
                if nd == 'Výpis' and predlozka.lower() == 'na ': predlozka = 've ' if predlozka[0] == 'n' else 'Ve '
                if nd == 'Tab.' and predlozka.lower() == 'na ': predlozka = 'v ' if predlozka[0] == 'n' else 'V '
                if nd == 'Obr.' and predlozka.lower() in ('v ', 've '): predlozka = 'na ' if predlozka[0] == 'v' else 'Na '
                return f'{predlozka}{nove}\x00{nc}\x00'
            r[i] = re.sub(r'(?P<pred>\b(?:na|v|ve|Na|V|Ve) )?' + r'\b' + TVARY[sd] + r'\s+' + re.escape(sc) + r'\b' + CIZI,
                          nahrad, r[i], flags=re.I)
        r[i] = re.sub(r'\x00(\d+)\x00', r' \1', r[i])
    novy = '\n'.join(r)
    if nahled:
        import difflib; sys.stdout.writelines(difflib.unified_diff(t.splitlines(1), novy.splitlines(1), n=0))
    else:
        Path(path).write_text(novy, encoding='utf-8')
    return zmeny

if __name__ == '__main__':
    for a in [x for x in sys.argv[1:] if not x.startswith('--')]:
        print(a, zpracuj(a, '--nahled' in sys.argv))

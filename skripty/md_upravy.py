"""Společné úpravy Markdownu extraktů: rozpoznání nadpisů, popisků a tabulek
v textu převedeném z Wordu (používá import připomínek)."""
import re

KAT = [('UVOD', r'^úvod$'), ('UZITI', r'^užití$'), ('PREDMLUVA', r'^předmluva$'),
       ('PREDMET', r'^(\d+\.?\s*)?(kapitola\s*\d+\s*)?předmět( normy| technické specifikace| technické zprávy| specifikace)?$'),
       ('SOUVISICI', r'^(\d+\.?\s*)?(souvisící|související) normy( \(výběr\))?$|^(\d+\.?\s*)?citované dokumenty$'
                     r'|^(\d+\.?\s*)?(citované )?normativní (dokumenty|odkazy)$|^(\d+\.?\s*)?informativní odkazy$'),
       ('TERMINY', r'^(\d+\.?\s*)?(termíny a definice|definice|termíny)$'),
       ('ZKRATKY', r'^(\d+\.?\s*)?(symboly a zkratky|zkratky|symboly \(a zkrácené termíny\)|zkrácené termíny'
                   r'|symboly a zkrácené termíny|zkratky a symboly|značky a zkratky|zkratky termínů)$'),
       ('TERMZKR', r'^(\d+\.?\s*)?termíny,? definice a zkratky$|^(\d+\.?\s*)?termíny, definice a zkrácené termíny$'
                   r'|^(\d+\.?\s*)?zkratky a termíny$')]


def kat(t):
    """Druh nadpisu podle textu: UVOD, UZITI, PREDMET, …, KAP (kapitola), PODKAP (článek), PRILOHA, nebo None."""
    s = ' '.join(t.replace(' ', ' ').split()).strip().rstrip(':').lower()
    for k, r in KAT:
        if re.match(r, s): return k
    if re.match(r'^(příloha) [a-z]\b', s): return 'PRILOHA'
    m = re.match(r'^(kapitola\s*)?(\d+)(\.\d+)*\.?\s*\S', s)
    if m: return 'KAP' if not m.group(3) else 'PODKAP'
    return None


def nadpisy(telo, volne=None):
    """Tučné odstavce a nadpisy z převodu Wordu → nadpisy ## (kapitoly) a ### (články).
    Ve volném režimu (Word bez tučných nadpisů, např. revize 14819 z roku 2023) se za nadpis
    považuje i samostatný řádek nebo položka číslovaného seznamu s textem nadpisu."""
    if volne is None:
        prvni = nadpisy(telo, volne=False)
        return prvni if any(l.strip() == '## Úvod' for l in prvni) else nadpisy(telo, volne=True)
    novy, kod = [], False
    for i, l in enumerate(telo):
        if l.strip().startswith('```'):
            kod = not kod; novy.append(l); continue
        if kod:
            novy.append(l); continue
        if volne:
            s = l.strip()
            m = re.fullmatch(r'\d+\.\s+(.+)', s)
            kandidat = m.group(1).strip() if m else s
            prazdne_okoli = (i == 0 or not telo[i - 1].strip()) and (i + 1 >= len(telo) or not telo[i + 1].strip())
            k = kat(kandidat) if kandidat and len(kandidat) < 90 and not kandidat.endswith(('.', ':')) else None
            if prazdne_okoli and not s.startswith(('|', '*', '#', '!', '<', '-')) and k and k != 'PODKAP' \
                    and (k != 'KAP' or re.match(r'^\d+ [A-ZÁ-Ž]', kandidat)):
                novy.append('## ' + kandidat); continue
        s = l.strip()
        h = re.fullmatch(r'(#{1,4})\s+\*\*(.+?)\*\*\s*', s)        # „## **Úvod**“ → „## Úvod“
        if h: s = f'{h.group(1)} {h.group(2)}'
        m = re.fullmatch(r'\*\*(.+?)\*\*', s) or re.fullmatch(r'#{1,4}\s+(.+)', s)
        if m and '**' not in m.group(1):
            t = m.group(1).strip(); k = kat(t)
            if k and k != 'PODKAP': novy.append('## ' + t); continue
            if k == 'PODKAP' and len(t) < 120: novy.append('### ' + t); continue
            if s.startswith('#'): novy.append('## ' + t); continue
        novy.append(l)
    return novy


def normalizuj(radky):
    """Sjednocení zápisu po převodu z Wordu:
    popisky „Tabulka A.3 – …“ / „**Obrázek B1. …**“ → „**Tab. A.3** …“ / „**Obr. B1** …“;
    obrázek a jeho popisek vždy jako samostatné odstavce; nadpisy bez zpětných lomítek
    („## 6\\. Požadavky“ → „## 6. Požadavky“); prázdné nadpisy „##“ pryč;
    pipe tabulky s prázdným záhlavím → první řádek jako záhlaví."""
    out, kod = [], False
    for l in radky:
        s = l.strip()
        if s.startswith('```'):
            kod = not kod; out.append(l); continue
        if kod:
            out.append(l); continue
        if re.fullmatch(r'#{1,6}', s):
            continue
        if s.startswith('#'):
            l = s.replace('\\.', '.').replace('\\)', ')')
        m = (re.match(r'^(Obrázek|Tabulka)\s+([A-Z]?\.?\d+(?:\.\d+)?)\s*[–-]\s*(.+)$', s)
             or re.fullmatch(r'\*\*(Obrázek|Tabulka)\s+([A-Z]?\.?\d+(?:\.\d+)?)\.?\s*[–-]?\s*(.+?)\*\*', s))
        if m:
            l = f"**{'Obr.' if m.group(1) == 'Obrázek' else 'Tab.'} {m.group(2)}** {m.group(3)}"
        v = re.match(r'^(?:\*\*)?Výpis\s+(\d+)\.?\s*[–-]\s*(.+?)(?:\*\*)?$', s)
        if v and not s.startswith('**Výpis '):
            l = f"**Výpis {v.group(1)}** {v.group(2)}"
        im = re.fullmatch(r'(!\[[^\]]*\]\([^)]*\)(?:\{[^}]*\})?)\s+(\S.*)', l.strip())
        if im:                                   # obrázek a popisek na jednom řádku
            out += [im.group(1), '', im.group(2)]; continue
        if out and l.strip() and re.fullmatch(r'!\[[^\]]*\]\([^)]*\)(?:\{[^}]*\})?', out[-1].strip()):
            out.append('')                       # za obrázkem vždy prázdný řádek
        out.append(l)
    out = _odstavce(out)
    for k, l in enumerate(out):                  # oddělovač pipe tabulky: prázdná buňka → ---
        if re.fullmatch(r'\|[-:| ]+\|', l.strip()) and '-' in l and re.search(r'\|\s+(?=\|)', l):
            out[k] = re.sub(r'\|\s+(?=\|)', '| --- ', l)
    i = 0
    while i < len(out) - 2:
        a, b, c = out[i], out[i + 1], out[i + 2]
        if (a.startswith('|') and not a.replace('|', '').strip() and re.fullmatch(r'\|[-:| ]+\|', b.strip())
                and c.startswith('|')):
            out[i:i + 3] = [c, b]
        i += 1
    return out


def _odstavce(radky):
    """Popisek „**Obr./Tab. …**“ vždy začíná nový odstavec; v odstavci s lichým počtem „**“
    (tučné přes konec řádku z Wordu) se odstraní osamocené „**“ na konci nebo na samostatném řádku."""
    out, kod = [], False
    for l in radky:
        if l.strip().startswith('```'):
            kod = not kod
        if not kod and re.match(r'\*\*(Obr\.|Tab\.|Výpis) ', l.strip()) and out and out[-1].strip():
            out.append('')
        out.append(l)
    vysl, blok, kod = [], [], False

    def uzavri():
        if blok and not blok[0].lstrip().startswith(('|', '<', '```', '    ')):
            if sum(x.count('**') for x in blok) % 2:
                if blok[-1].rstrip().endswith('**') and not blok[-1].rstrip().endswith('***'):
                    blok[-1] = blok[-1].rstrip()[:-2].rstrip()
                elif any(x.strip() == '**' for x in blok):
                    k = max(i for i, x in enumerate(blok) if x.strip() == '**')
                    del blok[k]
        vysl.extend(blok); blok.clear()

    for l in out:
        if l.strip().startswith('```'):
            kod = not kod
        if kod or l.strip().startswith('```') or not l.strip():
            uzavri(); vysl.append(l)
        else:
            blok.append(l)
    uzavri()
    return [x for x in vysl]


def rozdel(text):
    """Vrátí (záhlaví, tělo od nadpisu Úvod) jako seznamy řádků."""
    radky = text.split('\n')
    i = next(i for i, l in enumerate(radky)
             if re.match(r'^(#+\s*|\d+\.\s+)?(\*\*)?Úvod(\*\*)?\s*$', l.strip()))
    return radky[:i], radky[i:]

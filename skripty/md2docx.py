"""Markdown extraktu (zdroj pravdy) → docx a pdf v build/.
Text převede pandoc se šablonou a filtrem, hlavičku (titul, upozornění, tabulka
s názvem a označením, řádek vydání) složí z metadat podle šablony TNK 136."""
import sys, re, copy, subprocess, tempfile
from pathlib import Path
import yaml
from docx import Document
from docx.oxml.ns import qn
KOREN = Path(__file__).resolve().parents[1]
SABLONA = KOREN / 'sablona' / 'reference.docx'
FILTR = KOREN / 'sablona' / 'extrakt.lua'
BUILD = KOREN / 'build'
try:                                   # pandoc ≥ 3 (sloučené buňky tabulek); starší pandoc je umí jen zčásti
    import pypandoc; PANDOC = pypandoc.get_pandoc_path()
except Exception:
    PANDOC = 'pandoc'
TITUL = {'evropská norma': 'EXTRAKT z evropské normy', 'mezinárodní norma ISO': 'EXTRAKT z mezinárodní normy ISO',
         'technická specifikace ISO': 'EXTRAKT z technické specifikace ISO', 'technická specifikace CEN': 'EXTRAKT z technické specifikace CEN',
         'technická zpráva ISO': 'EXTRAKT z technické zprávy ISO', 'technická zpráva CEN': 'EXTRAKT z technické zprávy CEN'}

def T(e): return ''.join(t.text or '' for t in e.iter(qn('w:t')))
def prepis(p, novy):
    ts = list(p.iter(qn('w:t')))
    ts[0].text = novy; ts[0].set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    for t in ts[1:]: t.text = ''

def hlavicka(meta):
    """Prvky záhlaví zkopírované ze šablony a vyplněné z metadat."""
    s = Document(str(SABLONA)); b = list(s.element.body.iterchildren())
    titul, upoz, tab, vyd = [copy.deepcopy(e) for e in b[:4]]
    prepis(titul, TITUL[meta['typ']].replace('EXTRAKT z ', 'EXTRAKT z '))
    bunky = list(tab.iter(qn('w:tc')))
    prepis(next(p for p in bunky[0].iter(qn('w:p')) if T(p).strip()), meta['nazev'])
    ps = [p for p in bunky[-1].iter(qn('w:p')) if T(p).strip()]
    prepis(ps[0], meta['oznaceni'])
    for p in ps[1:]: prepis(p, '')
    prepis(vyd, f"Vydána {meta['vydani']}" + (f", {meta['stran']} stran" if meta.get('stran') else ''))
    extr = copy.deepcopy(vyd)                    # řádek s rokem zpracování a úpravy extraktu
    from docx.oxml import OxmlElement
    ppr = extr.find(qn('w:pPr'))
    if ppr is None: ppr = OxmlElement('w:pPr'); extr.insert(0, ppr)
    for sp in ppr.findall(qn('w:spacing')): ppr.remove(sp)
    sp = OxmlElement('w:spacing'); sp.set(qn('w:before'), '0'); sp.set(qn('w:after'), '120')
    st = ppr.find(qn('w:pStyle')); (st.addnext(sp) if st is not None else ppr.insert(0, sp))
    prepis(extr, f"Extrakt zpracován {meta['zpracovano']}" + (f", aktualizován {meta['upraveno']}" if meta.get('upraveno') else ''))
    for e in (titul, upoz, tab, vyd, extr):    # šablona má zástupné údaje zvýrazněné
        for h in list(e.iter(qn('w:highlight'))): h.getparent().remove(h)
    vysl = [titul, upoz]
    if meta.get('ics'):
        ics = copy.deepcopy(upoz); prepis(ics, meta['ics']); vysl.append(ics)
    return vysl + [tab, vyd, extr]

def upravy_tabulek(body):
    """Tabulky z pandocu: ohraničení, šířka přes celou sazbu (šablona nemá styl Table)."""
    from docx.oxml import OxmlElement
    for tbl in body.iter(qn('w:tbl')):
        pr = tbl.find(qn('w:tblPr'))
        if pr is None or pr.find(qn('w:tblBorders')) is not None: continue
        st = pr.find(qn('w:tblStyle'))
        if st is None or st.get(qn('w:val')) != 'Table': continue
        w = pr.find(qn('w:tblW')); w.set(qn('w:type'), 'pct'); w.set(qn('w:w'), '5000')
        b = OxmlElement('w:tblBorders')
        for strana in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            e = OxmlElement(f'w:{strana}'); e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '4'); e.set(qn('w:color'), '808080')
            b.append(e)
        w.addnext(b)
        sirky_sloupcu(tbl, body)

def sirky_sloupcu(tbl, body):
    """Šířky sloupců podle obsahu: každý sloupec aspoň na nejdelší slovo, zbytek sazby
    poměrně podle délky textu (pandoc je bere z délky pomlček v md, což dává úzké sloupce)."""
    from docx.oxml import OxmlElement
    grid = tbl.find(qn('w:tblGrid'))
    if grid is None: return
    cols = grid.findall(qn('w:gridCol'))
    n = len(cols)
    if n < 2: return
    sect = body.find(qn('w:sectPr'))
    pg, mar = sect.find(qn('w:pgSz')), sect.find(qn('w:pgMar'))
    celkem = int(pg.get(qn('w:w'))) - int(mar.get(qn('w:left'))) - int(mar.get(qn('w:right')))
    nejdelsi, slovo = [1] * n, [1] * n
    for tr in tbl.findall(qn('w:tr')):
        j = 0
        for tc in tr.findall(qn('w:tc')):
            span = tc.find(qn('w:tcPr') + '/' + qn('w:gridSpan'))
            k = int(span.get(qn('w:val'))) if span is not None else 1
            t = T(tc)
            if k == 1 and j < n:
                nejdelsi[j] = max(nejdelsi[j], len(t))
                slovo[j] = max([slovo[j]] + [len(x) for x in t.split()])
            j += k
    ZNAK = 125                                    # přibližná šířka znaku v twipech (Arial 10 pt)
    minimum = [min(s, 25) * ZNAK + 330 for s in slovo]
    if sum(minimum) >= celkem:
        sirky = [celkem * m // sum(minimum) for m in minimum]
    else:
        navic = [max(0, d * ZNAK + 330 - m) for d, m in zip(nejdelsi, minimum)]
        zbyva = celkem - sum(minimum)
        if sum(navic) <= zbyva:                   # vejde se vše na řádek: rozdělit zbytek poměrně k délce
            sirky = [m + v for m, v in zip(minimum, navic)]
            sirky = [w * celkem // sum(sirky) for w in sirky]
        else:
            sirky = [m + zbyva * v // sum(navic) for m, v in zip(minimum, navic)]
    for c, w in zip(cols, sirky): c.set(qn('w:w'), str(w))
    for tr in tbl.findall(qn('w:tr')):
        j = 0
        for tc in tr.findall(qn('w:tc')):
            pr = tc.find(qn('w:tcPr'))
            if pr is None: pr = OxmlElement('w:tcPr'); tc.insert(0, pr)
            span = pr.find(qn('w:gridSpan'))
            k = int(span.get(qn('w:val'))) if span is not None else 1
            tw = pr.find(qn('w:tcW'))
            if tw is None: tw = OxmlElement('w:tcW'); pr.insert(0, tw)
            tw.set(qn('w:type'), 'dxa'); tw.set(qn('w:w'), str(sum(sirky[j:j + k])))
            j += k

def mezery(d):
    """Mezery kolem tabulek a obrázků:
    - popisek tabulky (nad tabulkou) odsazený od tabulky,
    - za tabulkou volné místo před dalším textem,
    - popisek obrázku těsně pod obrázkem a s mezerou před dalším textem."""
    from docx.text.paragraph import Paragraph
    from docx.shared import Pt
    body = d.element.body
    styl = lambda e: (e.find(qn('w:pPr') + '/' + qn('w:pStyle')).get(qn('w:val'))
                      if e is not None and e.tag == qn('w:p') and e.find(qn('w:pPr') + '/' + qn('w:pStyle')) is not None else '')
    obrazek = lambda e: e is not None and e.tag == qn('w:p') and next(e.iter(qn('w:drawing')), None) is not None
    for e in list(body.iterchildren()):
        dalsi, predchozi = e.getnext(), e.getprevious()
        if e.tag == qn('w:tbl') and dalsi is not None and dalsi.tag == qn('w:p'):
            Paragraph(dalsi, d).paragraph_format.space_before = Pt(10)
        elif styl(e) == 'NadpisTabObr':
            pf = Paragraph(e, d).paragraph_format
            if dalsi is not None and dalsi.tag == qn('w:tbl'):        # popisek tabulky
                pf.space_before = Pt(10); pf.space_after = Pt(6); pf.keep_with_next = True
            elif obrazek(predchozi):                                   # popisek obrázku
                pf.space_before = Pt(2); pf.space_after = Pt(12)
                Paragraph(predchozi, d).paragraph_format.space_after = Pt(0)

def horni_dolni_indexy(telo):
    """<sup>/<sub> v běžném textu → ^…^ / ~…~ (pandoc by surové HTML do Wordu vynechal);
    v blocích kódu a HTML tabulkách se nemění."""
    casti = re.split(r'(?ms)(^```.*?^```\s*$)', telo)
    for i in range(0, len(casti), 2):
        c = re.sub(r'<sup>(.*?)</sup>', lambda m: '^' + m.group(1).replace(' ', '\\ ') + '^', casti[i])
        casti[i] = re.sub(r'<sub>(.*?)</sub>', lambda m: '~' + m.group(1).replace(' ', '\\ ') + '~', c)
    return ''.join(casti)


def preved(md: Path, pdf: bool = True):
    text = md.read_text(encoding='utf-8')
    _, fm, telo = text.split('---', 2)
    meta = yaml.safe_load(fm)
    # HTML tabulky (sloučené buňky) jako jeden surový blok, filtr je převede na tabulku Wordu
    telo = re.sub(r'(?ms)^<table.*?</table>\s*$', lambda m: '\n```{=html}\n' + m.group(0).strip() + '\n```\n', telo)
    telo = horni_dolni_indexy(telo)
    cil = BUILD / md.parent.name if md.parent.name.startswith('TC') else BUILD
    cil.mkdir(parents=True, exist_ok=True)
    docx = cil / (md.stem + '.docx')
    with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(telo); tmp = f.name
    subprocess.run([PANDOC, tmp, '-f', 'markdown+raw_html+raw_attribute-implicit_figures-smart', '-t', 'docx',
                    '--reference-doc', str(SABLONA), '--lua-filter', str(FILTR),
                    '--shift-heading-level-by=-1', '--syntax-highlighting=none', '--resource-path', str(md.parent), '-o', str(docx)], check=True)
    d = Document(str(docx)); body = d.element.body
    upravy_tabulek(body)
    prvni = next(body.iterchildren())
    for e in hlavicka(meta): prvni.addprevious(e)
    mezery(d)
    d.save(str(docx))
    if pdf:
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', str(docx.parent), str(docx)],
                       check=True, capture_output=True, timeout=300)
    print('vytvořeno', docx.relative_to(KOREN) if docx.is_relative_to(KOREN) else docx)
    return docx

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='Markdown extraktu → build/<WG>/*.docx a *.pdf')
    ap.add_argument('soubory', nargs='*', help='.md soubory nebo složky; bez nich všechny extrakty')
    ap.add_argument('--bez-pdf', action='store_true', help='vytvořit jen docx')
    a = ap.parse_args()
    cesty = [Path(x).resolve() for x in a.soubory] or [KOREN / 'extrakty']
    md = sorted({m for c in cesty for m in ([c] if c.is_file() else c.rglob('*.md'))})
    for m in md: preved(m, pdf=not a.bez_pdf)

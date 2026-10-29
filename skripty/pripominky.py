"""Jednorázový dozorovaný převod připomínek z Wordu do Markdownu.

Použití: python pripominky.py VRACENY.docx [ZDROJ.md]
- vedle Wordu zapíše výpis komentářů (VRACENY.md) k odškrtávání,
- sledované změny přijme a výsledný text zapíše do zdrojového .md (necommituje);
  kontrola je `git diff`, nechtěné úpravy se vrátí.
"""
import sys, re, shutil, tempfile, zipfile
from pathlib import Path
from lxml import etree
KOREN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from md_upravy import nadpisy, normalizuj, rozdel
import prijmi_revize, docx2md

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
q = lambda t: '{%s}%s' % (W, t)
def T(e): return ''.join(x.text or '' for x in e.iter(q('t'), q('delText')))

def komentare(docx: Path):
    z = zipfile.ZipFile(docx)
    if 'word/comments.xml' not in z.namelist(): return []
    kom = {c.get(q('id')): c for c in etree.fromstring(z.read('word/comments.xml')).iter(q('comment'))}
    doc = etree.fromstring(z.read('word/document.xml'))
    vysl, kapitola, otevrene, citace = [], '', {}, {}
    for el in doc.iter():
        if el.tag == q('p'):
            st = el.find(q('pPr') + '/' + q('pStyle'))
            if st is not None and re.match(r'(Heading|Nadpis)\s*1', st.get(q('val')) or ''):
                kapitola = T(el).strip()
        elif el.tag == q('commentRangeStart'):
            otevrene[el.get(q('id'))] = kapitola; citace[el.get(q('id'))] = []
        elif el.tag in (q('t'), q('delText')):
            for i in otevrene: citace[i].append(el.text or '')
        elif el.tag == q('commentRangeEnd'):
            i = el.get(q('id'))
            if i in otevrene:
                c = kom.get(i)
                if c is not None:
                    vysl.append({'kapitola': otevrene.pop(i), 'citace': ''.join(citace.pop(i)).strip(),
                                 'autor': c.get(q('author')), 'datum': (c.get(q('date')) or '')[:10],
                                 'text': ' '.join(T(p).strip() for p in c.iter(q('p'))).strip()})
    return vysl

def jazyky_kodu(md: str):
    """Jazyky bloků kódu ve zdrojovém .md v pořadí výskytu (Word je nenese)."""
    jaz, kod = [], False
    for l in md.split('\n'):
        if l.strip().startswith('```'):
            if not kod: jaz.append(l.strip()[3:].strip())
            kod = not kod
    return jaz

def prevezmi_text(docx: Path, zdroj: Path):
    """Přijme sledované změny ve Wordu a jeho text zapíše do těla zdrojového .md (metadata ponechá)."""
    with tempfile.TemporaryDirectory() as tmp:
        kopie = Path(tmp) / 'prijato.docx'; shutil.copy2(docx, kopie)
        prijmi_revize.main([str(kopie)])
        novy = docx2md.prevod(kopie, Path(tmp) / 'img', zdroj.stem, jazyky_kodu(zdroj.read_text(encoding='utf-8')))
    _, novy_telo = rozdel(novy)
    novy_telo = normalizuj(nadpisy(novy_telo))
    puvodni = zdroj.read_text(encoding='utf-8')
    _, fm, puv_telo = puvodni.split('---', 2)
    # odkazy na obrázky ponechat podle zdroje (převod je pojmenuje jinak)
    puv_obr = re.findall(r'\]\((\./img/[^)]+)\)', puv_telo)
    nove_obr = re.findall(r'\]\((\./img/[^)]+)\)', '\n'.join(novy_telo))
    text = '\n'.join(novy_telo).strip() + '\n'
    if len(puv_obr) == len(nove_obr):
        for i, a in enumerate(nove_obr): text = text.replace('](' + a + ')', f'](\x00{i}\x00)', 1)   # bez řetězení náhrad
        for i, b in enumerate(puv_obr): text = text.replace(f'](\x00{i}\x00)', '](' + b + ')', 1)
    else:
        print(f'POZOR: počet obrázků se liší ({len(puv_obr)} → {len(nove_obr)}), odkazy zkontrolujte ručně.')
    zdroj.write_text('---' + fm + '---\n\n' + text, encoding='utf-8')

def najdi_zdroj(docx: Path):
    kandidati = list((KOREN / 'extrakty').rglob(docx.stem.split('__')[0] + '.md'))
    if len(kandidati) != 1: raise SystemExit(f'Nenašel jsem jednoznačně zdrojový .md pro {docx.name}, zadejte ho.')
    return kandidati[0]

def main(docx: Path, zdroj: Path = None):
    zdroj = zdroj or najdi_zdroj(docx)
    # 1) výpis komentářů
    kom = komentare(docx)
    vypis = docx.with_suffix('.md')
    radky = [f'# Připomínky k {zdroj.stem} ({docx.name})', '', '| # | Kapitola | Citace | Připomínka | Autor | Vyřízení |', '|---|---|---|---|---|---|']
    for n, k in enumerate(kom, 1):
        cit = k['citace'][:120].replace('|', '\\|'); txt = k['text'].replace('|', '\\|')
        radky.append(f"| {n} | {k['kapitola']} | {cit} | {txt} | {k['autor']} {k['datum']} | |")
    vypis.write_text('\n'.join(radky) + '\n', encoding='utf-8')
    # 2) sledované změny → text do zdrojového .md
    prevezmi_text(docx, zdroj)
    print(f'Komentářů: {len(kom)} → {vypis}')
    print(f'Text zapsán do {zdroj} – zkontrolujte `git diff`.')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None)

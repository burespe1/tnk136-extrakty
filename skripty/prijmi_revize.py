#!/usr/bin/env python3
"""Přijme všechny sledované změny (revize) ve Wordu .docx. Komentáře nechá.

Použití: python prijmi-revize.py SOUBOR.docx [...]
"""
import re, sys, zipfile
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
q = lambda t: "{%s}%s" % (W, t)
CASTI = re.compile(r"word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$")
ZMENY_VLASTNOSTI = ["rPrChange", "pPrChange", "sectPrChange", "tblPrChange", "tblGridChange",
                    "trPrChange", "tcPrChange", "numberingChange", "tblPrExChange"]
ZNACKY_ROZSAHU = ["moveFromRangeStart", "moveFromRangeEnd", "moveToRangeStart", "moveToRangeEnd",
                  "customXmlInsRangeStart", "customXmlInsRangeEnd", "customXmlDelRangeStart", "customXmlDelRangeEnd"]


def prijmi(koren):
    pocty = {}
    def pocet(k, n=1): pocty[k] = pocty.get(k, 0) + n

    # 1) smazané značky odstavce → spojit odstavec s následujícím
    for p in reversed(list(koren.iter(q("p")))):
        rpr = p.find(q("pPr") + "/" + q("rPr"))
        if rpr is None:
            continue
        smaz = rpr.find(q("del")) if rpr.find(q("del")) is not None else rpr.find(q("moveFrom"))
        if smaz is None:
            continue
        rpr.remove(smaz)
        dalsi = p.getnext()
        if dalsi is not None and dalsi.tag == q("p"):
            obsah = [ch for ch in p if ch.tag != q("pPr")]
            kotva = dalsi.find(q("pPr"))
            for ch in reversed(obsah):
                if kotva is not None:
                    kotva.addnext(ch)
                else:
                    dalsi.insert(0, ch)
            p.getparent().remove(p)
            pocet("spojené odstavce")
    # 2) vložené značky odstavce – jen odstranit značku
    for rpr in koren.iter(q("rPr")):
        for t in ("ins", "moveTo"):
            for el in rpr.findall(q(t)):
                rpr.remove(el); pocet("značky vložení")
    # 3) smazané a vložené řádky tabulky
    for tr in list(koren.iter(q("tr"))):
        trpr = tr.find(q("trPr"))
        if trpr is None:
            continue
        if trpr.find(q("del")) is not None:
            tr.getparent().remove(tr); pocet("smazané řádky"); continue
        for el in trpr.findall(q("ins")):
            trpr.remove(el); pocet("vložené řádky")
    for tcpr in koren.iter(q("tcPr")):
        for t in ("cellIns", "cellDel", "cellMerge"):
            for el in tcpr.findall(q(t)):
                tcpr.remove(el); pocet("značky buněk")
    # 4) smazaný a přesunutý-pryč obsah pryč
    for t in ("del", "moveFrom"):
        for el in list(koren.iter(q(t))):
            if el.getparent() is not None and el.getparent().tag not in (q("rPr"), q("trPr"), q("tcPr")):
                el.getparent().remove(el); pocet("smazáno")
    # 5) vložený a přesunutý-sem obsah rozbalit
    for t in ("ins", "moveTo"):
        for el in list(koren.iter(q(t))):
            rodic = el.getparent()
            if rodic is None or rodic.tag in (q("rPr"), q("trPr"), q("tcPr")):
                continue
            for ch in list(el):
                el.addprevious(ch)
            rodic.remove(el); pocet("vloženo")
    # 6) změny formátu (ponechat nový stav) a značky rozsahů
    for t in ZMENY_VLASTNOSTI + ZNACKY_ROZSAHU:
        for el in list(koren.iter(q(t))):
            el.getparent().remove(el); pocet("změny formátu" if t in ZMENY_VLASTNOSTI else "značky rozsahu")
    # 7) běhy se smazaným textem (w:delText) mimo w:del – pro jistotu
    for el in list(koren.iter(q("delText"))):
        r = el.getparent(); r.remove(el); pocet("delText")
    return pocty


def main(soubory):
    for f in soubory:
        z = zipfile.ZipFile(f); info = z.infolist(); data = {i.filename: z.read(i.filename) for i in info}; z.close()
        celkem = {}
        for jm in data:
            if CASTI.match(jm):
                koren = etree.fromstring(data[jm])
                pocty = prijmi(koren)
                if pocty:
                    data[jm] = etree.tostring(koren, xml_declaration=True, encoding="UTF-8", standalone=True)
                    for k, v in pocty.items(): celkem[k] = celkem.get(k, 0) + v
        # vypnout sledování změn, pokud je zapnuté
        if "word/settings.xml" in data:
            s = etree.fromstring(data["word/settings.xml"])
            for el in s.findall(q("trackRevisions")):
                s.remove(el); celkem["vypnuto sledování změn"] = 1
            data["word/settings.xml"] = etree.tostring(s, xml_declaration=True, encoding="UTF-8", standalone=True)
        with zipfile.ZipFile(f, "w", zipfile.ZIP_DEFLATED) as zo:
            for i in info: zo.writestr(i, data[i.filename])
        print(f, celkem)


if __name__ == "__main__":
    main(sys.argv[1:])

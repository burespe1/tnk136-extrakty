"""Smaže všechny komentáře z Wordu .docx (kotvy, odkazy i části comments*.xml)."""
import re, sys, zipfile
from lxml import etree
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
q = lambda t: "{%s}%s" % (W, t)
for f in sys.argv[1:]:
    z = zipfile.ZipFile(f); info = z.infolist(); data = {i.filename: z.read(i.filename) for i in info}; z.close()
    smazano = 0
    for jm in list(data):
        if re.match(r"word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$", jm):
            k = etree.fromstring(data[jm])
            for t in ("commentRangeStart", "commentRangeEnd"):
                for el in list(k.iter(q(t))):
                    el.getparent().remove(el); smazano += 1
            for el in list(k.iter(q("commentReference"))):
                r = el.getparent()
                if r.tag == q("r") and all(ch.tag in (q("rPr"), q("commentReference")) for ch in r):
                    r.getparent().remove(r)
                else:
                    r.remove(el)
                smazano += 1
            data[jm] = etree.tostring(k, xml_declaration=True, encoding="UTF-8", standalone=True)
    casti = [jm for jm in data if re.match(r"word/comments(Extended|Ids|Extensible)?\.xml$", jm) or jm == "word/people.xml"]
    for jm in casti:
        del data[jm]
    rels = data["word/_rels/document.xml.rels"].decode("utf8")
    rels = re.sub(r'<Relationship [^>]*Target="(?:comments(?:Extended|Ids|Extensible)?|people)\.xml"[^>]*/>', "", rels)
    data["word/_rels/document.xml.rels"] = rels.encode("utf8")
    ct = data["[Content_Types].xml"].decode("utf8")
    ct = re.sub(r'<Override PartName="/word/(?:comments(?:Extended|Ids|Extensible)?|people)\.xml"[^>]*/>', "", ct)
    data["[Content_Types].xml"] = ct.encode("utf8")
    info = [i for i in info if i.filename in data]
    with zipfile.ZipFile(f, "w", zipfile.ZIP_DEFLATED) as zo:
        for i in info: zo.writestr(i, data[i.filename])
    print(f.split("/")[-1], "odstraněno značek", smazano, "| části:", casti)

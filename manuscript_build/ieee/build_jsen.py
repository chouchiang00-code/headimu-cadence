"""Build the manuscript (and the supplementary file) in the IEEE Sensors Journal colorized Word format
(Colorized_Format_JSEN template): Letter page, 0.65-in side and 0.7-in top/bottom margins, two 3.5-in columns with a 0.2-in
gap, Helvetica title in IEEE blue, teal (#007367) rules and labels, shaded abstract box with the graphical abstract,
Sensors Council running head, first-page copyright footer, Times body text.
usage: python3 build_jsen.py main OUT.docx | python3 build_jsen.py supp OUT.docx"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.packuri import PackURI
from docx.opc.part import Part
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls
from docx.shared import Pt, Inches, Twips, RGBColor, Emu

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
MODE, OUTP = sys.argv[1], sys.argv[2]
if MODE == "main":
    import content_en as C
else:
    import content_supp as C

SERIF, SANS = "Times New Roman", "Helvetica"
BLUE, TEAL, BOXFILL = "004393", "007367", "E5F1D4"
PAGE_W, MARG_LR, MARG_TB, GAP = 12240, 936, 1008, 288
TEXTW = PAGE_W - 2 * MARG_LR                    # 10368 twips = 7.2 in
COLW = (TEXTW - GAP) // 2                        # 5040 twips = 3.5 in
JOURNAL = "IEEE SENSORS JOURNAL, VOL. XX, NO. XX, MONTH X, XXXX"
LOGO = HERE / "jsen_assets" / "sensors_council_logo.png"

doc = Document()


# ================================================================== styles (names and values as in the template)
def _fonts(rpr_el, font):
    rf = rpr_el.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr_el.insert(0, rf)
    for a in list(rf.attrib):
        del rf.attrib[a]
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), font)


def pstyle(name, base="Normal", font=SERIF, size=10, bold=False, italic=False, color=None, smallcaps=False,
           align=None, before=0, after=0, first=None, left=None, hanging=None, keep=False, line=240):
    styles = doc.styles
    st = styles[name] if name in [s.name for s in styles] else styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    if name != "Normal":
        st.base_style = styles[base]
    f = st.font
    f.size, f.bold, f.italic, f.small_caps = Pt(size), bold, italic, smallcaps
    f.color.rgb = RGBColor.from_string(color) if color else RGBColor(0, 0, 0)
    _fonts(st.element.get_or_add_rPr(), font)
    pf = st.paragraph_format
    pf.space_before, pf.space_after = Twips(before * 20), Twips(after * 20)
    pf.line_spacing = Twips(line) if line != 240 else 1.0
    if align is not None:
        pf.alignment = align
    pf.first_line_indent = Twips(first) if first is not None else None
    if left is not None:
        pf.left_indent = Twips(left)
    if hanging is not None:
        pf.first_line_indent = Twips(-hanging)
    pf.keep_with_next = keep
    pf.widow_control = True
    return st


J, Cn, L = WD_ALIGN_PARAGRAPH.JUSTIFY, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT
pstyle("Normal", font=SERIF, size=10)
pstyle("Title", font=SANS, size=24, color=BLUE, align=Cn, after=4)
pstyle("Authors", font=SANS, size=11, align=Cn, after=12)
pstyle("Abstract", font=SANS, size=9, bold=True, align=J, before=1, first=202)
pstyle("IndexTerms", font=SANS, size=9, bold=True, align=J, before=6, first=202)
pstyle("Text", font=SERIF, size=10, align=J, first=202)
pstyle("Heading 1", font=SANS, size=10, color=BLUE, smallcaps=True, align=Cn, before=12, after=4, keep=True)
pstyle("Heading 2", font=SANS, size=10, italic=True, color=TEAL, align=L, before=6, after=3, keep=True)
pstyle("Reference Head", base="Heading 1", font=SANS, size=10, color=BLUE, smallcaps=True, align=Cn, before=14, after=4,
       keep=True)
pstyle("Equation", font=SERIF, size=10, align=L, before=4, after=4)
pstyle("Table Title", font=SANS, size=8, smallcaps=True, align=Cn, keep=True)
pstyle("Table Text", font=SERIF, size=8, align=Cn)
pstyle("Table Note", font=SANS, size=8, align=J, before=2, after=6)
pstyle("Figure Caption", font=SANS, size=8, align=J, before=2, after=8)
pstyle("Footnote Text", font=SANS, size=8, align=J, first=202)
pstyle("References", font=SERIF, size=8, align=J, left=360, hanging=360)
pstyle("Biography", font=SANS, size=8, align=J)
pstyle("RH", font=SANS, size=7, align=L)
for s in ("Title", "Heading 1", "Heading 2", "Reference Head"):
    el = doc.styles[s].element
    for x in el.iter():
        for a in [a for a in x.attrib if "Theme" in a or a.endswith("themeShade") or a.endswith("themeTint")]:
            del x.attrib[a]
    ppr = el.find(qn("w:pPr"))
    if ppr is not None:
        for b in ppr.findall(qn("w:pBdr")) + ppr.findall(qn("w:contextualSpacing")):
            ppr.remove(b)
for s in ("Title", "Heading 1", "Heading 2", "Reference Head"):
    st = doc.styles[s]
    st.font.bold = False
    rpr = st.element.get_or_add_rPr()
    for el in rpr.findall(qn("w:rFonts")):
        _fonts(rpr, SANS)
doc.styles["Heading 1"].paragraph_format.keep_with_next = True
# RH: teal rule under the running head
rh_ppr = doc.styles["RH"].element.get_or_add_pPr()
rh_ppr.append(parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="12" w:space="2" w:color="{TEAL}"/></w:pBdr>'))

sec = doc.sections[0]
sec.page_width, sec.page_height = Twips(PAGE_W), Twips(15840)
sec.left_margin = sec.right_margin = Twips(MARG_LR)
sec.top_margin = sec.bottom_margin = Twips(MARG_TB)
sec.header_distance = sec.footer_distance = Twips(432)


def set_cols(section, n, space=GAP):
    sp = section._sectPr
    for c in sp.findall(qn("w:cols")):
        sp.remove(c)
    cols = OxmlElement("w:cols"); cols.set(qn("w:num"), str(n)); cols.set(qn("w:space"), str(space))
    pgmar = sp.find(qn("w:pgMar"))
    (pgmar.addnext(cols) if pgmar is not None else sp.append(cols))


# ================================================================== citations and inline markup
ORDER = []


def cite_repl(m):
    nums = []
    for k in [k.strip() for k in m.group(1).split(",")]:
        assert k in C.R, k
        if k not in ORDER:
            ORDER.append(k)
        nums.append(ORDER.index(k) + 1)
    nums = sorted(set(nums)); out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(f"[{nums[i]}]–[{nums[j]}]" if j - i >= 2 else ", ".join(f"[{n}]" for n in nums[i:j + 1]))
        i = j + 1
    return ", ".join(out)


def cites(t):
    return re.sub(r"⟦([^⟧]+)⟧", cite_repl, t)


TOK = re.compile(r"(\*\*|\*|_\{[^}]*\}|\^\{[^}]*\}|\[\[|\]\]|\n)")


def add_runs(par, text, size=None, bold=None, italic=False, smallcaps=False, color=None, font=None):
    text = cites(text)
    b, it, hl = bold, italic, False
    for tok in TOK.split(text):
        if tok == "":
            continue
        if tok == "**":
            b = not b; continue
        if tok == "*":
            it = not it; continue
        if tok == "[[":
            hl = True; continue
        if tok == "]]":
            hl = False; continue
        if tok == "\n":
            par.add_run().add_break(); continue
        sub = sup = False
        if tok.startswith("_{"):
            tok, sub = tok[2:-1], True
        elif tok.startswith("^{"):
            tok, sup = tok[2:-1], True
        r = par.add_run(tok)
        f = r.font
        if b is not None:
            f.bold = b
        if it and not sub and not sup:
            f.italic = True
        if sub:
            f.subscript = True
        if sup:
            f.superscript = True
        if size:
            f.size = Pt(size)
        if smallcaps:
            f.small_caps = True
        if hl:
            f.highlight_color = WD_COLOR_INDEX.YELLOW
        if color:
            f.color.rgb = RGBColor.from_string(color)
        if font:
            r.font.name = font
            r._r.get_or_add_rPr().find(qn("w:rFonts")).set(qn("w:cs"), font)
    return par


def para(text="", style="Text", container=None, **kw):
    p = (container or doc).add_paragraph(style=style)
    if text:
        add_runs(p, text, **kw)
    return p


# ================================================================== floating pictures (graphical abstract, logo, photos)
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
DOCPR = [100]


def anchor_picture(run, path, width_in, align="right", rel="column", wrap="square", dist=(0, 0, 114300, 114300),
                   pos_v=0, behind=False):
    """Insert a picture as a floating (anchored) drawing in `run`, aligned left/right in its column or cell."""
    inline = run.add_picture(str(path), width=Inches(width_in))._inline
    ext = inline.find(qn("wp:extent"))
    graphic = inline.find(qn("a:graphic"))
    DOCPR[0] += 1
    t, b, l, r = dist
    wrap_xml = '<wp:wrapSquare wrapText="bothSides"/>' if wrap == "square" else "<wp:wrapNone/>"
    anc = parse_xml(
        f'<wp:anchor {nsdecls("wp", "a", "pic", "r")} distT="{t}" distB="{b}" distL="{l}" distR="{r}" simplePos="0" '
        f'relativeHeight="{251658240 + DOCPR[0]}" behindDoc="{1 if behind else 0}" locked="0" layoutInCell="1" '
        f'allowOverlap="1"><wp:simplePos x="0" y="0"/><wp:positionH relativeFrom="{rel}"><wp:align>{align}</wp:align>'
        f'</wp:positionH><wp:positionV relativeFrom="paragraph"><wp:posOffset>{pos_v}</wp:posOffset></wp:positionV>'
        f'<wp:extent cx="{ext.get("cx")}" cy="{ext.get("cy")}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>{wrap_xml}'
        f'<wp:docPr id="{DOCPR[0]}" name="Picture {DOCPR[0]}"/><wp:cNvGraphicFramePr>'
        f'<a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr></wp:anchor>')
    anc.append(graphic)
    drawing = inline.getparent()
    drawing.remove(inline)
    drawing.append(anc)
    return anc


# ================================================================== OMML equations (unchanged from the V16 build)
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def mr(t, sty=None):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    rpr = f'<m:rPr><m:sty m:val="{sty}"/></m:rPr>' if sty else ""
    return f'<m:r>{rpr}<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr><m:t xml:space="preserve">{t}</m:t></m:r>'


def sub(b, s): return f"<m:sSub><m:e>{b}</m:e><m:sub>{s}</m:sub></m:sSub>"
def subsup(b, s, u): return f"<m:sSubSup><m:e>{b}</m:e><m:sub>{s}</m:sub><m:sup>{u}</m:sup></m:sSubSup>"
def frac(n, d): return f"<m:f><m:num>{n}</m:num><m:den>{d}</m:den></m:f>"
def dl(c, b="(", e=")"): return f'<m:d><m:dPr><m:begChr m:val="{b}"/><m:endChr m:val="{e}"/></m:dPr><m:e>{c}</m:e></m:d>'
def acc(c, ch): return f'<m:acc><m:accPr><m:chr m:val="{ch}"/></m:accPr><m:e>{c}</m:e></m:acc>'


HAT, TIL = "̂", "̃"
V = lambda s: mr(s, "b")
P = lambda s: mr(s, "p")
I = lambda s: mr(s)
T = P("(") + I("t") + P(")")
a_s = sub(V("a"), I("s")); w_s = sub(V("ω"), I("s")); al_s = sub(V("α"), I("s"))
g_s = sub(acc(V("g"), HAT), I("s"))
LPa = P("LP") + dl(a_s + T, "{", "}")
Ti = lambda lab: sub(acc(I("T"), TIL), P(lab))
EQ = {
    "eq1": sub(I("s"), I("a")) + T + P("=") + dl(a_s + T, "‖", "‖"),
    "eq2": g_s + T + P("=") + frac(LPa, dl(LPa, "‖", "‖")) + P(", ") + I("q") + T + P("=")
           + dl(w_s + T + P("·") + g_s + T, "|", "|"),
    "eq3": I("v") + T + P("=") + a_s + T + P("·") + g_s + T,
    "eq4": subsup(V("a"), I("s"), P("′")) + T + P("=") + V("R") + dl(I("θ") + P(",") + V("u")) + a_s + T + P(", ")
           + subsup(V("ω"), I("s"), P("′")) + T + P("=") + V("R") + dl(I("θ") + P(",") + V("u")) + w_s + T,
    "eq5": subsup(V("a"), I("s"), P("″")) + T + P("=") + a_s + T + P("+") + al_s + T + P("×") + V("r")
           + P("+") + w_s + T + P("×") + dl(w_s + T + P("×") + V("r")),
    "eq6": sub(I("e"), P("T")) + P("=") + Ti("IMU") + P("−") + Ti("ref") + P(", ") + sub(I("e"), P("C")) + P("=")
           + frac(P("60"), Ti("IMU")) + P("−") + frac(P("60"), Ti("ref")),
}
EQN = [0]


def equation(name, width=COLW):
    EQN[0] += 1
    p = para(style="Equation")
    p._p.get_or_add_pPr().append(parse_xml(
        f'<w:tabs {nsdecls("w")}><w:tab w:val="center" w:pos="{width // 2}"/><w:tab w:val="right" w:pos="{width}"/></w:tabs>'))
    p.add_run("\t")
    p._p.append(parse_xml(f'<m:oMath xmlns:m="{M}" {nsdecls("w")}>{EQ[name]}</m:oMath>'))
    p.add_run(f"\t({EQN[0]})")
    return p


# ================================================================== figures and tables
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
FIGN = [0]; TABN = [0]


def figure(path, caption, width=3.45, label_prefix=""):
    FIGN[0] += 1
    p = para(style="Text"); p.paragraph_format.first_line_indent = Twips(0)
    p.paragraph_format.alignment = Cn; p.paragraph_format.space_before = Pt(6); p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(ROOT / path), width=Inches(width))
    c = para(style="Figure Caption")
    add_runs(c, f"Fig. {label_prefix}{FIGN[0]}.", color=TEAL)
    add_runs(c, "  " + caption)


def cell_border(cell, **sides):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn("w:tcBorders"))
    if b is None:
        b = OxmlElement("w:tcBorders"); tcPr.append(b)
    for side, (sz, color) in sides.items():
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:space"), "0"); e.set(qn("w:color"), color)
        b.append(e)


def table(caption, head, rows, widths, note=None, prefix=""):
    TABN[0] += 1
    num = f"{prefix}{TABN[0]}" if prefix else ROMAN[TABN[0] - 1]
    c1 = para(style="Table Title"); c1.paragraph_format.space_before = Pt(6)
    add_runs(c1, f"TABLE {num}", color=TEAL)
    c2 = para(style="Table Title"); c2.paragraph_format.space_after = Pt(3)
    add_runs(c2, caption)
    t = doc.add_table(rows=len(rows) + 1, cols=len(head))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblPr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    tblPr.append(parse_xml(f'<w:tblCellMar {nsdecls("w")}><w:left w:w="45" w:type="dxa"/>'
                           f'<w:right w:w="45" w:type="dxa"/></w:tblCellMar>'))
    for gc, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(w))
    for i, row in enumerate([head] + rows):
        tr = t.rows[i]
        trPr = tr._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
        if i == 0:
            trPr.append(OxmlElement("w:tblHeader"))
        for j, (txt, w) in enumerate(zip(row, widths)):
            cell = tr.cells[j]
            cell.width = Twips(w)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cp = cell.paragraphs[0]
            cp.style = doc.styles["Table Text"]
            cp.paragraph_format.alignment = Cn if j else L
            cp.paragraph_format.keep_with_next = True
            add_runs(cp, txt)
            sides = {}
            if i == 0:
                sides.update(top=(8, TEAL), bottom=(4, TEAL))
            if i == len(rows):
                sides["bottom"] = (8, TEAL)
            if sides:
                cell_border(cell, **sides)
    if note:
        add_runs(para(style="Table Note"), note)
    else:
        para(style="Table Note")
    return t


# ================================================================== first-page footnote (unnumbered), Helvetica 8 pt
def add_footnote_part(text):
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

    def runs_xml(t):
        out, hl = [], False
        for seg in re.split(r"(\[\[|\]\])", t):
            if seg == "[[":
                hl = True; continue
            if seg == "]]":
                hl = False; continue
            if not seg:
                continue
            seg = seg.replace("&", "&amp;").replace("<", "&lt;")
            h = '<w:highlight w:val="yellow"/>' if hl else ""
            out.append(f'<w:r><w:rPr><w:rFonts w:ascii="{SANS}" w:hAnsi="{SANS}" w:cs="{SANS}"/><w:sz w:val="16"/>'
                       f'<w:szCs w:val="16"/>{h}</w:rPr><w:t xml:space="preserve">{seg}</w:t></w:r>')
        return "".join(out)
    paras = "".join(f'<w:p><w:pPr><w:ind w:firstLine="202"/><w:jc w:val="both"/></w:pPr>{runs_xml(t)}</w:p>'
                    for t in text.split("\n\n"))
    xml = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:footnotes xmlns:w="{W}">'
           f'<w:footnote w:type="separator" w:id="-1"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/>'
           f'</w:pPr><w:r><w:separator/></w:r></w:p></w:footnote>'
           f'<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:pPr><w:spacing w:after="0" w:line="240" '
           f'w:lineRule="auto"/></w:pPr><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>'
           f'<w:footnote w:id="1">{paras}</w:footnote></w:footnotes>')
    part = Part(PackURI("/word/footnotes.xml"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml", xml.encode("utf-8"),
                doc.part.package)
    doc.part.relate_to(part, RT.FOOTNOTES)


def footnote_ref(par):
    """Unnumbered first-page footnote as in the template: custom (empty) mark in the same run as the reference."""
    r = parse_xml(f'<w:r {nsdecls("w")}><w:rPr><w:vertAlign w:val="superscript"/></w:rPr>'
                  f'<w:footnoteReference w:customMarkFollows="1" w:id="1"/><w:t>\u200b</w:t></w:r>')
    ppr = par._p.find(qn("w:pPr"))
    (ppr.addnext(r) if ppr is not None else par._p.insert(0, r))


# ================================================================== running heads and footer
def page_field(par):
    r = par.add_run()
    for tag, txt in (("begin", None), (None, " PAGE "), ("end", None)):
        if tag:
            fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), tag); r._r.append(fc)
        else:
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; r._r.append(it)


def rh_par(hdr):
    p = hdr.paragraphs[0]
    p.style = doc.styles["RH"]
    return p


def set_tabs(p, *tabs):
    p._p.get_or_add_pPr().append(parse_xml(
        f'<w:tabs {nsdecls("w")}>' + "".join(f'<w:tab w:val="{k}" w:pos="{v}"/>' for k, v in tabs) + "</w:tabs>"))


def running_heads(odd_text, first_logo=True, copyright_footer=True, even_text=JOURNAL):
    s0 = doc.sections[0]
    s0.different_first_page_header_footer = True
    doc.settings.odd_and_even_pages_header_footer = True
    # first page: Sensors Council logo, journal line, page number
    fp = rh_par(s0.first_page_header)
    if first_logo:
        fp.paragraph_format.left_indent = Twips(1800)
        anchor_picture(fp.add_run(), LOGO, 1.19, align="left", rel="column", wrap="none", dist=(0, 0, 0, 0), pos_v=-20000)
    set_tabs(fp, ("right", TEXTW))
    add_runs(fp, JOURNAL if first_logo else odd_text); fp.add_run("\t"); page_field(fp)
    # even pages: number left, journal right
    ep = rh_par(s0.even_page_header)
    set_tabs(ep, ("right", TEXTW)); page_field(ep); ep.add_run("\t"); add_runs(ep, even_text)
    # odd pages: running title left, number right
    op = rh_par(s0.header)
    set_tabs(op, ("right", TEXTW)); add_runs(op, odd_text); op.add_run("\t"); page_field(op)
    if copyright_footer:
        f = s0.first_page_footer.paragraphs[0]
        f.style = doc.styles["Normal"]; f.paragraph_format.alignment = Cn
        add_runs(f, "XXXX-XXXX © XXXX IEEE. Personal use is permitted, but republication/redistribution requires IEEE "
                    "permission.", size=8, font=SANS)
        f2 = s0.first_page_footer.add_paragraph(); f2.paragraph_format.alignment = Cn
        add_runs(f2, "See http://www.ieee.org/publications_standards/publications/rights/index.html for more information.",
                 size=8, font=SANS)


def heading1(t, numbered=True, style="Heading 1", _n=[0], _h2=[0]):
    p = para(style=style)
    if numbered:
        _n[0] += 1
        H2N[0] = 0
        add_runs(p, f"{ROMAN[_n[0] - 1]}. ")
    add_runs(p, t)
    return p


H2N = [0]


def heading2(t):
    H2N[0] += 1
    return add_runs(para(style="Heading 2"), f"{chr(64 + H2N[0])}. {t}")


def drop_cap_paragraph(text):
    """IEEE first paragraph: two-line drop cap, rest of the first word in capitals."""
    m = re.match(r"(\W*)(\w)(\w*)(.*)", text, re.S)
    lead, first, rest_word, rest = m.groups()
    dc = para(style="Text")
    dc.paragraph_format.first_line_indent = Twips(0)
    ppr = dc._p.get_or_add_pPr()
    ppr.append(parse_xml(f'<w:framePr {nsdecls("w")} w:dropCap="drop" w:lines="2" w:wrap="around" w:vAnchor="text" '
                         f'w:hAnchor="text"/>'))
    ppr.append(parse_xml(f'<w:spacing {nsdecls("w")} w:before="0" w:after="0" w:line="460" w:lineRule="exact"/>'))
    ppr.append(parse_xml(f'<w:textAlignment {nsdecls("w")} w:val="baseline"/>'))
    r = dc.add_run(first)
    r.font.size = Pt(28)
    r._r.get_or_add_rPr().append(parse_xml(f'<w:position {nsdecls("w")} w:val="-5"/>'))
    p = para(style="Text"); p.paragraph_format.first_line_indent = Twips(0)
    add_runs(p, rest_word.upper())
    add_runs(p, rest)
    return p


def biographies():
    """Author biographies as in the template (photo 1 in x 1.25 in at the left, name in bold IEEE blue); placeholders.
    A borderless two-cell table keeps photo and text together in both Word and LibreOffice."""
    para(style="Text")
    for name in ("Qiu Qiang", "Chen Shiqi", "Jin Zhenkun"):
        t = doc.add_table(rows=1, cols=2)
        t.autofit = False
        tblPr = t._tbl.tblPr
        lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
        tblPr.append(parse_xml(f'<w:tblCellMar {nsdecls("w")}><w:left w:w="0" w:type="dxa"/>'
                               f'<w:right w:w="100" w:type="dxa"/></w:tblCellMar>'))
        widths = (1540, COLW - 1540)
        for gc, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths):
            gc.set(qn("w:w"), str(w))
        c0, c1 = t.rows[0].cells
        c0.width, c1.width = Twips(widths[0]), Twips(widths[1])
        c0.vertical_alignment = c1.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        p0 = c0.paragraphs[0]; p0.style = doc.styles["Biography"]
        p0.add_run().add_picture(str(HERE / "jsen_assets" / "photo_placeholder.png"), width=Inches(1.0))
        p1 = c1.paragraphs[0]; p1.style = doc.styles["Biography"]
        add_runs(p1, name, bold=True, color=BLUE)
        add_runs(p1, " [[(membership grades) biography: place and year of birth, degrees (field, institution, year), "
                     "positions, research interests, memberships, and awards. Photograph 1 in × 1.25 in.]]")
        para(style="Biography").paragraph_format.space_after = Pt(6)


# ================================================================== build MAIN
if MODE == "main":
    s0 = doc.sections[0]
    add_runs(para(style="Title"), C.TITLE)
    add_runs(para(style="Authors"), C.AUTHORS)
    # abstract box: teal rule / shaded abstract with floating graphical abstract / teal rule (as in the template)
    box = doc.add_table(rows=3, cols=1)
    box.alignment = WD_TABLE_ALIGNMENT.CENTER; box.autofit = False
    tp = box._tbl.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tp.append(lay)
    tp.append(parse_xml(f'<w:tblCellMar {nsdecls("w")}><w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/>'
                        f'<w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar>'))
    BOXW = TEXTW - 12
    box._tbl.tblGrid.findall(qn("w:gridCol"))[0].set(qn("w:w"), str(BOXW))
    for i, row in enumerate(box.rows):
        c = row.cells[0]; c.width = Twips(BOXW)
        if i == 0:
            cell_border(c, top=(12, TEAL))
        if i == 2:
            cell_border(c, bottom=(12, TEAL))
        if i in (0, 2):
            sp = c.paragraphs[0]; sp.style = doc.styles["Abstract"]
            sp.paragraph_format.first_line_indent = Twips(0)
            sp.paragraph_format.space_before = Pt(1)
    mid = box.rows[1].cells[0]
    tcPr = mid._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{BOXFILL}"/>'))
    tcPr.append(parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="40" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/></w:tcMar>'))
    ap = mid.paragraphs[0]; ap.style = doc.styles["Abstract"]
    anchor_picture(ap.add_run(), ROOT / getattr(C, "GRAPHICAL_ABSTRACT", "fig_ieee/graphical_abstract.png"), 2.75,
                   align="right", rel="column", wrap="square", dist=(0, 50800, 114300, 0), pos_v=50800)
    add_runs(ap, "*Abstract*", color=TEAL); add_runs(ap, "—", color=TEAL)
    add_runs(ap, C.ABSTRACT)
    ip = mid.add_paragraph(style="IndexTerms")
    add_runs(ip, "*Index Terms*", color=TEAL); add_runs(ip, "—", color=TEAL)
    add_runs(ip, C.INDEX)
    para(style="Text").paragraph_format.space_after = Pt(2)
    # two-column body
    s2 = doc.add_section(WD_SECTION.CONTINUOUS)
    set_cols(s0, 1); set_cols(s2, 2)
    first_h1, first_par = True, True
    for kind, payload in C.B:
        if kind == "h1":
            h = heading1(payload)
            if first_h1:
                add_footnote_part(C.FOOTNOTE); footnote_ref(h); first_h1 = False
        elif kind == "h2":
            heading2(payload)
        elif kind == "p":
            if first_par:
                drop_cap_paragraph(payload); first_par = False
            else:
                para(payload)
        elif kind == "eq":
            equation(payload)
        elif kind == "fig":
            figure(*payload)
        elif kind == "table":
            table(*payload)
    for kind, payload in C.TAIL:
        if kind == "h1u":
            heading1(payload, numbered=False, style="Reference Head")
        else:
            para(payload)
    heading1("References", numbered=False, style="Reference Head")
    for i, k in enumerate(ORDER):
        rp = para(style="References")
        rp.paragraph_format.tab_stops.add_tab_stop(Twips(360))
        add_runs(rp, f"[{i + 1}]\t")
        add_runs(rp, C.R[k])
    unused = [k for k in C.R if k not in ORDER]
    print("refs", len(ORDER), "unused", unused)
    if "--bios" in sys.argv:
        biographies()
    doc.add_section(WD_SECTION.CONTINUOUS); set_cols(doc.sections[-1], 2)
    running_heads("Qiu Qiang *et al.*: Cadence From a Single Head-Worn IMU Across Clinical Cohorts")
else:
    # supplementary material: single column, same typography, teal labels and running head
    add_runs(para(style="Title"), "Supplementary Material")
    doc.paragraphs[-1].runs[0].font.size = Pt(20)
    t2 = para(style="Authors")
    add_runs(t2, C.TITLE, italic=True)
    for kind, payload in C.B:
        if kind == "h1":
            heading1(payload, numbered=False, style="Reference Head")
        elif kind == "p":
            p = para(payload); p.paragraph_format.first_line_indent = Twips(0); p.paragraph_format.space_after = Pt(4)
        elif kind == "fig":
            path, cap, w = payload
            figure(path, cap, w, label_prefix="S")
        elif kind == "table":
            cap, head, rows, widths, note = payload
            table(cap, head, rows, widths, note, prefix="S")
    running_heads("Supplementary Material — Cadence From a Single Head-Worn IMU", first_logo=False,
                  copyright_footer=False, even_text="Supplementary Material — Cadence From a Single Head-Worn IMU")

# ================================================================== schema order of property children
ORD = {"tblPr": ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize", "tblW", "jc",
                 "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption",
                 "tblDescription"],
       "tcPr": ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap", "tcMar", "textDirection",
                "tcFitText", "vAlign", "hideMark"],
       "pPr": ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr", "suppressLineNumbers",
               "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap", "overflowPunct", "topLinePunct",
               "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind", "contextualSpacing",
               "mirrorIndents", "suppressOverlap", "jc", "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl",
               "divId", "cnfStyle", "rPr", "sectPr", "pPrChange"],
       "rPr": ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike", "outline", "shadow",
               "emboss", "imprint", "noProof", "snapToGrid", "vanish", "webHidden", "color", "spacing", "w", "kern",
               "position", "sz", "szCs", "highlight", "u", "effect", "bdr", "shd", "fitText", "vertAlign", "rtl", "cs", "em",
               "lang", "eastAsianLayout", "specVanish", "oMath"],
       "trPr": ["cnfStyle", "divId", "gridBefore", "gridAfter", "wBefore", "wAfter", "cantSplit", "trHeight", "tblHeader",
                "tblCellSpacing", "jc", "hidden"]}


def reorder(root):
    for tag, order in ORD.items():
        for el in root.iter(qn("w:" + tag)):
            if tag == "rPr" and el.getparent().tag == qn("w:pPr") and False:
                continue
            kids, seen = [], set()
            for k in list(el):
                nm = k.tag.split("}")[1]
                if tag in ("tblPr", "pPr") and nm in seen and nm not in ("rPr",):
                    el.remove(k); continue
                seen.add(nm); kids.append(k)
            kids.sort(key=lambda k: order.index(k.tag.split("}")[1]) if k.tag.split("}")[1] in order else 99)
            for k in kids:
                el.remove(k)
            for k in kids:
                el.append(k)


reorder(doc.element.body)
reorder(doc.styles.element)
for s in doc.sections:
    for h in (s.header, s.first_page_header, s.even_page_header, s.first_page_footer):
        if not h.is_linked_to_previous:
            reorder(h._element)
for z in doc.settings.element.findall(qn("w:zoom")):
    z.set(qn("w:percent"), "100")
doc.save(OUTP)
print("saved", OUTP, "figs", FIGN[0], "tables", TABN[0], "eqs", EQN[0])

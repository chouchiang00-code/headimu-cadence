"""Build the IEEE-style two-column manuscript (and the supplementary file) with python-docx.
usage: python3 build_ieee.py main OUT.docx | python3 build_ieee.py supp OUT.docx"""
import copy, re, sys
from pathlib import Path
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.part import Part
from docx.opc.packuri import PackURI
from docx.shared import Pt, Inches, Twips, RGBColor

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
MODE, OUTP = sys.argv[1], sys.argv[2]
if MODE == "main":
    import content_en as C
else:
    import content_supp as C

FONT = "Times New Roman"
COLW = 5040  # one column, twips

doc = Document()
st = doc.styles["Normal"]
st.font.name = FONT; st.font.size = Pt(10)
st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
st.paragraph_format.space_after = Pt(0); st.paragraph_format.space_before = Pt(0)
st.paragraph_format.line_spacing = 1.0

sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.top_margin, sec.bottom_margin = Inches(0.75), Inches(1.0)
sec.left_margin = sec.right_margin = Inches(0.625)
sec.header_distance, sec.footer_distance = Inches(0.4), Inches(0.5)


def set_cols(section, n, space=360):
    sp = section._sectPr
    for c in sp.findall(qn("w:cols")):
        sp.remove(c)
    cols = OxmlElement("w:cols"); cols.set(qn("w:num"), str(n)); cols.set(qn("w:space"), str(space))
    # w:cols must precede w:docGrid etc.; insert after pgMar if present
    pgmar = sp.find(qn("w:pgMar"))
    if pgmar is not None:
        pgmar.addnext(cols)
    else:
        sp.append(cols)


# ------------------------------------------------------------------ citations
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


# ------------------------------------------------------------------ inline markup -> runs
TOK = re.compile(r"(\*\*|\*|_\{[^}]*\}|\^\{[^}]*\}|\[\[|\]\]|\n)")
def add_runs(par, text, size=None, bold=False, italic=False, smallcaps=False, color=None):
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
        f.bold, f.italic = b, (it and not sub and not sup) or (it and False)
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
    return par


def para(text="", size=10, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=0.17, before=0, after=0, **kw):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = align; pf.first_line_indent = Inches(indent) if indent else None
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    if text:
        add_runs(p, text, size=size, **kw)
    return p


ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
H1N = [0]; H2N = [0]
def h1(t, numbered=True):
    p = para(align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, before=10, after=5)
    p.paragraph_format.keep_with_next = True
    if numbered:
        H1N[0] += 1; H2N[0] = 0
        add_runs(p, f"{ROMAN[H1N[0] - 1]}. ", size=10)
    add_runs(p, t, size=10, smallcaps=True)
    return p


def h2(t):
    H2N[0] += 1
    p = para(align=WD_ALIGN_PARAGRAPH.LEFT, indent=0, before=6, after=3)
    p.paragraph_format.keep_with_next = True
    add_runs(p, f"{chr(64 + H2N[0])}. {t}", size=10, italic=True)
    return p


# ------------------------------------------------------------------ OMML equations
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
def mr(t, sty=None):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    rpr = f'<m:rPr><m:sty m:val="{sty}"/></m:rPr>' if sty else ""
    return f'<m:r>{rpr}<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr><m:t xml:space="preserve">{t}</m:t></m:r>'
def sub(b, s): return f"<m:sSub><m:e>{b}</m:e><m:sub>{s}</m:sub></m:sSub>"
def sup(b, s): return f"<m:sSup><m:e>{b}</m:e><m:sup>{s}</m:sup></m:sSup>"
def subsup(b, s, u): return f"<m:sSubSup><m:e>{b}</m:e><m:sub>{s}</m:sub><m:sup>{u}</m:sup></m:sSubSup>"
def frac(n, d): return f"<m:f><m:num>{n}</m:num><m:den>{d}</m:den></m:f>"
def dl(c, b="(", e=")"): return f'<m:d><m:dPr><m:begChr m:val="{b}"/><m:endChr m:val="{e}"/></m:dPr><m:e>{c}</m:e></m:d>'
def acc(c, ch): return f'<m:acc><m:accPr><m:chr m:val="{ch}"/></m:accPr><m:e>{c}</m:e></m:acc>'
HAT, TIL = "̂", "̃"
V = lambda s: mr(s, "b")          # bold vector
P = lambda s: mr(s, "p")          # plain
I = lambda s: mr(s)               # italic (default)
T = P("(") + I("t") + P(")")
a_s = sub(V("a"), I("s")); w_s = sub(V("ω"), I("s")); al_s = sub(V("α"), I("s"))
g_s = sub(acc(V("g"), HAT), I("s"))
LPa = P("LP") + dl(a_s + T, "{", "}")
Ti = lambda lab: sub(acc(I("T"), TIL), P(lab))
EQ = {
 "eq1": sub(I("s"), I("a")) + T + P("=") + dl(a_s + T, "‖", "‖"),
 "eq2": g_s + T + P("=") + frac(LPa, dl(LPa, "‖", "‖")) + P(",\u2003") + I("q") + T + P("=") + dl(w_s + T + P("·") + g_s + T, "|", "|"),
 "eq3": I("v") + T + P("=") + a_s + T + P("·") + g_s + T,
 "eq4": subsup(V("a"), I("s"), P("′")) + T + P("=") + V("R") + dl(I("θ") + P(",") + V("u")) + a_s + T + P(",\u2003")
        + subsup(V("ω"), I("s"), P("′")) + T + P("=") + V("R") + dl(I("θ") + P(",") + V("u")) + w_s + T,
 "eq5": subsup(V("a"), I("s"), P("″")) + T + P("=") + a_s + T + P("+") + al_s + T + P("×") + V("r")
        + P("+") + w_s + T + P("×") + dl(w_s + T + P("×") + V("r")),
 "eq6": sub(I("e"), P("T")) + P("=") + Ti("IMU") + P("−") + Ti("ref") + P(",\u2003") + sub(I("e"), P("C")) + P("=")
        + frac(P("60"), Ti("IMU")) + P("−") + frac(P("60"), Ti("ref")),
}
EQN = [0]
def equation(name, width=COLW):
    EQN[0] += 1
    p = para(align=WD_ALIGN_PARAGRAPH.LEFT, indent=0, before=4, after=4)
    ppr = p._p.get_or_add_pPr()
    tabs = parse_xml(f'<w:tabs {nsdecls("w")}><w:tab w:val="center" w:pos="{width // 2}"/><w:tab w:val="right" w:pos="{width}"/></w:tabs>')
    ppr.append(tabs)
    p.add_run("\t")
    om = parse_xml(f'<m:oMath xmlns:m="{M}" {nsdecls("w")}>{EQ[name]}</m:oMath>')
    p._p.append(om)
    r = p.add_run(f"\t({EQN[0]})")
    return p


# ------------------------------------------------------------------ figures, tables
FIGN = [0]; TABN = [0]
def figure(path, caption, width=3.45, label="Fig."):
    FIGN[0] += 1
    p = para(align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, before=6, after=2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(ROOT / path), width=Inches(width))
    c = para(align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=0, after=6)
    add_runs(c, f"{label} {C.FIGPREFIX if hasattr(C, 'FIGPREFIX') else ''}{FIGN[0]}. ", size=8)
    add_runs(c, caption, size=8)


def cell_border(cell, **sides):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn("w:tcBorders"))
    if b is None:
        b = OxmlElement("w:tcBorders"); tcPr.append(b)
    for side, sz in sides.items():
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:space"), "0"); e.set(qn("w:color"), "000000")
        b.append(e)


def table(caption, head, rows, widths, note=None, prefix=""):
    TABN[0] += 1
    num = f"{prefix}{TABN[0]}" if prefix else ROMAN[TABN[0] - 1]
    c1 = para(align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, before=6)
    c1.paragraph_format.keep_with_next = True
    add_runs(c1, f"TABLE {num}", size=8)
    c2 = para(align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, after=3)
    c2.paragraph_format.keep_with_next = True
    add_runs(c2, caption, size=8, smallcaps=True)
    t = doc.add_table(rows=len(rows) + 1, cols=len(head))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblPr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    mar = parse_xml(f'<w:tblCellMar {nsdecls("w")}><w:left w:w="45" w:type="dxa"/><w:right w:w="45" w:type="dxa"/></w:tblCellMar>')
    tblPr.append(mar)
    grid = t._tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
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
            cp.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER if j else WD_ALIGN_PARAGRAPH.LEFT
            add_runs(cp, txt, size=8)
            cp.paragraph_format.keep_with_next = True
            sides = {}
            if i == 0:
                sides.update(top=8, bottom=4)
            if i == len(rows):
                sides["bottom"] = 8
            if sides:
                cell_border(cell, **sides)
    if note:
        n = para(align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=0, before=2, after=6)
        add_runs(n, note, size=7)
    else:
        para(after=4)
    return t


# ------------------------------------------------------------------ footnote part (unnumbered, IEEE first-page note)
def add_footnote_part(text):
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    def runs_xml(t):
        out = []
        for seg in re.split(r"(\[\[|\]\])", t):
            pass
        hl = False
        for seg in re.split(r"(\[\[|\]\])", t):
            if seg == "[[":
                hl = True; continue
            if seg == "]]":
                hl = False; continue
            if not seg:
                continue
            seg = seg.replace("&", "&amp;").replace("<", "&lt;")
            h = '<w:highlight w:val="yellow"/>' if hl else ""
            out.append(f'<w:r><w:rPr><w:sz w:val="16"/>{h}</w:rPr><w:t xml:space="preserve">{seg}</w:t></w:r>')
        return "".join(out)
    xml = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           f'<w:footnotes xmlns:w="{W}">'
           f'<w:footnote w:type="separator" w:id="-1"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:separator/></w:r></w:p></w:footnote>'
           f'<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>'
           f'<w:footnote w:id="1"><w:p><w:pPr><w:ind w:firstLine="170"/><w:jc w:val="both"/></w:pPr>{runs_xml(text)}</w:p></w:footnote>'
           f'</w:footnotes>')
    part = Part(PackURI("/word/footnotes.xml"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml",
                xml.encode("utf-8"), doc.part.package)
    doc.part.relate_to(part, RT.FOOTNOTES)


def footnote_ref(par):
    r = OxmlElement("w:r")
    fr = OxmlElement("w:footnoteReference"); fr.set(qn("w:customMarkFollows"), "1"); fr.set(qn("w:id"), "1")
    r.append(fr)
    ppr = par._p.find(qn("w:pPr"))
    if ppr is not None:
        ppr.addnext(r)
    else:
        par._p.insert(0, r)
    r2 = OxmlElement("w:r"); t = OxmlElement("w:t"); t.text = ""; r2.append(t)
    r.addnext(r2)


# ------------------------------------------------------------------ header
def header(text):
    for s in doc.sections:
        h = s.header
        hp = h.paragraphs[0]
        hp._p.get_or_add_pPr().append(parse_xml(f'<w:tabs {nsdecls("w")}><w:tab w:val="clear" w:pos="4680"/><w:tab w:val="clear" w:pos="9360"/><w:tab w:val="right" w:pos="10440"/></w:tabs>'))
        add_runs(hp, text, size=8)
        hp.add_run("\t")
        r = hp.add_run()
        for tag, txt in (("begin", None), (None, " PAGE "), ("end", None)):
            if tag:
                fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), tag); r._r.append(fc)
            else:
                it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; r._r.append(it)
        r.font.size = Pt(8)
        break


# ================================================================== build MAIN
if MODE == "main":
    t = para(align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, after=8)
    add_runs(t, C.TITLE, size=22)
    a = para(align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, after=8)
    add_runs(a, C.AUTHORS, size=11)
    # abstract box with graphical abstract
    box = doc.add_table(rows=1, cols=2)
    box.alignment = WD_TABLE_ALIGNMENT.CENTER; box.autofit = False
    tp = box._tbl.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tp.append(lay)
    tp.append(parse_xml(f'<w:tblBorders {nsdecls("w")}><w:top w:val="single" w:sz="6" w:space="0" w:color="7F7F7F"/>'
                        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="7F7F7F"/></w:tblBorders>'))
    tp.append(parse_xml(f'<w:tblCellMar {nsdecls("w")}><w:top w:w="80" w:type="dxa"/><w:left w:w="80" w:type="dxa"/>'
                        f'<w:bottom w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar>'))
    wl, wr = 6470, 3970
    for gc, w in zip(box._tbl.tblGrid.findall(qn("w:gridCol")), (wl, wr)):
        gc.set(qn("w:w"), str(w))
    cl, cr = box.rows[0].cells
    cl.width, cr.width = Twips(wl), Twips(wr)
    cr.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    ap = cl.paragraphs[0]; ap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_runs(ap, "*Abstract*—", size=9, bold=True)
    add_runs(ap, C.ABSTRACT, size=9)
    ip = cl.add_paragraph(); ip.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; ip.paragraph_format.space_before = Pt(5)
    add_runs(ip, "*Index Terms*—", size=9, bold=True)
    add_runs(ip, C.INDEX, size=9)
    gp = cr.paragraphs[0]; gp.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    gp.add_run().add_picture(str(ROOT / getattr(C, "GRAPHICAL_ABSTRACT", "fig_ieee/graphical_abstract.png")), width=Inches(2.62))
    para(after=6)
    # two-column body
    s2 = doc.add_section(WD_SECTION.CONTINUOUS)
    set_cols(doc.sections[0], 1); set_cols(s2, 2)
    first_body = True
    for kind, payload in C.B:
        if kind == "h1":
            h1(payload)
        elif kind == "h2":
            h2(payload)
        elif kind == "p":
            p = para(payload)
            if first_body:
                add_footnote_part(C.FOOTNOTE); footnote_ref(p); first_body = False
        elif kind == "eq":
            equation(payload)
        elif kind == "fig":
            figure(*payload)
        elif kind == "table":
            table(*payload)
    for kind, payload in C.TAIL:
        if kind == "h1u":
            h1(payload, numbered=False)
        else:
            para(payload)
    h1("References", numbered=False)
    for i, k in enumerate(ORDER):
        rp = para(align=WD_ALIGN_PARAGRAPH.LEFT, indent=0)
        rp.paragraph_format.left_indent = Inches(0.3); rp.paragraph_format.first_line_indent = Inches(-0.3)
        rp.paragraph_format.tab_stops.add_tab_stop(Inches(0.3))
        add_runs(rp, f"[{i + 1}]\t", size=8)
        add_runs(rp, C.R[k], size=8)
    unused = [k for k in C.R if k not in ORDER]
    print("refs", len(ORDER), "unused", unused)
    # balance the last page
    doc.add_section(WD_SECTION.CONTINUOUS); set_cols(doc.sections[-1], 2)
    header("IEEE SENSORS JOURNAL, VOL. XX, NO. XX, XXXX 2026")
else:
    # supplementary: single column, simple
    t = para(align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, after=4)
    add_runs(t, "Supplementary Material", size=16, bold=True)
    t2 = para(align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, after=10)
    add_runs(t2, C.TITLE, size=11, italic=True)
    for kind, payload in C.B:
        if kind == "h1":
            h1(payload, numbered=False)
        elif kind == "p":
            para(payload, indent=0, after=4)
        elif kind == "fig":
            path, cap, w = payload
            FIGN[0] += 1
            p = para(align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, before=6, after=2)
            p.add_run().add_picture(str(ROOT / path), width=Inches(w))
            c = para(indent=0, after=8); add_runs(c, f"Fig. S{FIGN[0]}. ", size=9, bold=True); add_runs(c, cap, size=9)
        elif kind == "table":
            cap, head, rows, widths, note = payload
            table(cap, head, rows, widths, note, prefix="S")
    if ORDER:
        h1("References", numbered=False)
        for i, k in enumerate(ORDER):
            rp = para(indent=0); add_runs(rp, f"[S{i + 1}] " + C.R[k], size=8)
    header("Supplementary Material — Forehead IMU Cadence")

ORD = {"tblPr": ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize", "tblW", "jc",
                 "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption", "tblDescription"],
       "tcPr": ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap", "tcMar", "textDirection",
                "tcFitText", "vAlign", "hideMark"],
       "pPr": ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr", "suppressLineNumbers",
               "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE",
               "autoSpaceDN", "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents",
               "suppressOverlap", "jc", "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle",
               "rPr", "sectPr", "pPrChange"],
       "trPr": ["cnfStyle", "divId", "gridBefore", "gridAfter", "wBefore", "wAfter", "cantSplit", "trHeight", "tblHeader",
                "tblCellSpacing", "jc", "hidden"]}
for tag, order in ORD.items():
    for el in doc.element.body.iter(qn("w:" + tag)):
        kids, seen = [], set()
        for k in list(el):
            nm = k.tag.split("}")[1]
            if tag == "tblPr" and nm in seen:
                el.remove(k); continue
            seen.add(nm); kids.append(k)
        kids.sort(key=lambda k: order.index(k.tag.split("}")[1]) if k.tag.split("}")[1] in order else 99)
        for k in kids:
            el.remove(k)
        for k in kids:
            el.append(k)
for z in doc.settings.element.findall(qn("w:zoom")):
    z.set(qn("w:percent"), "100")
doc.save(OUTP)
print("saved", OUTP, "figs", FIGN[0], "tables", TABN[0], "eqs", EQN[0])

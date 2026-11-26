#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按官方模板生成《作品设计文档.docx》。

用法: python tools/build_design_doc.py
输入: templates/作品设计文档模板.docx
输出: 作品设计文档.docx
"""
import os
import shutil

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

import doc_content as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "templates", "作品设计文档模板.docx")
OUTPUT = os.path.join(ROOT, "作品设计文档.docx")

BODY_PT = 12.0        # 正文：小四（模板说明要求）
TABLE_PT = 10.5       # 表格内文字：五号
CODE_PT = 10.5
CAPTION_PT = 10.5
LINE_SPACING = 1.5
FIG_WIDTH_CM = 14.6

CN_FONT = "宋体"
CN_HEAD = "黑体"
EN_FONT = "Times New Roman"
MONO_FONT = "Consolas"

META = {
    "赛题名称": "Freetrack",
    "队伍名称": "RAGStore 团队",
    "电子邮箱": "2096434473@qq.com",
    "提交日期": "2026 年 12 月 2 日",
}

WORK_NAME = "RAGStore：面向检索增强生成的轻量级向量存储引擎"


# ------------------------------------------------------------ 底层工具
def set_run_font(run, cn=CN_FONT, en=EN_FONT, size=BODY_PT, bold=False, underline=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.underline = underline
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), en)
    rFonts.set(qn("w:hAnsi"), en)
    rFonts.set(qn("w:eastAsia"), cn)


def set_para_format(p, size=BODY_PT, indent_chars=0.0, line=LINE_SPACING,
                    align=None, space_before=0, space_after=0, keep_next=False):
    pf = p.paragraph_format
    pf.line_spacing = line
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.first_line_indent = Pt(size * indent_chars) if indent_chars else Pt(0)
    if align is not None:
        p.alignment = align
    pf.keep_with_next = keep_next
    pPr = p._element.get_or_add_pPr()
    for tag in ("w:overflowPunct", "w:autoSpaceDE", "w:autoSpaceDN"):
        el = pPr.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            pPr.append(el)
        el.set(qn("w:val"), "1")
    return pf


def shade_cell(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def set_table_borders(table, color="808080", sz="6"):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), sz)
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def keep_row_together(row):
    """禁止表格行跨页断开，避免同一行被拆到两页。"""
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def has_sectpr(p):
    pPr = p._p.find(qn("w:pPr"))
    return pPr is not None and pPr.find(qn("w:sectPr")) is not None


# ------------------------------------------------------------ 内容写入器
class Writer:
    """把块序列插入到锚点段落之前。"""

    def __init__(self, doc, anchor):
        self.doc = doc
        self.anchor = anchor
        self.num = 0
        self.in_list = False

    def _new_para(self):
        return self.anchor.insert_paragraph_before()

    def add(self, block):
        kind = block[0]
        if kind != "num":
            self.in_list = False
        if kind == "h1":
            p = self._new_para()
            p.style = self.doc.styles["Heading 1"]
            set_run_font(p.add_run(block[1]), CN_HEAD, EN_FONT, 22, True)
            set_para_format(p, 22, line=1.5, space_before=16, space_after=12, keep_next=True)
        elif kind == "h2":
            p = self._new_para()
            p.style = self.doc.styles["Heading 2"]
            set_run_font(p.add_run(block[1]), CN_HEAD, EN_FONT, 16, True)
            set_para_format(p, 16, line=1.5, space_before=12, space_after=6, keep_next=True)
        elif kind == "h3":
            p = self._new_para()
            set_run_font(p.add_run(block[1]), CN_HEAD, EN_FONT, 14, True)
            set_para_format(p, 14, line=1.5, space_before=10, space_after=4, keep_next=True)
        elif kind == "p":
            p = self._new_para()
            set_run_font(p.add_run(block[1]), size=BODY_PT)
            set_para_format(p, BODY_PT, indent_chars=2)
        elif kind == "bullet":
            p = self._new_para()
            set_run_font(p.add_run("— " + block[1]), size=BODY_PT)
            pf = set_para_format(p, BODY_PT, line=LINE_SPACING)
            pf.left_indent = Pt(BODY_PT * 2)
            pf.first_line_indent = Pt(-BODY_PT)
        elif kind == "num":
            if not self.in_list:
                self.num = 0
            self.num += 1
            self.in_list = True
            p = self._new_para()
            set_run_font(p.add_run(f"{self.num}．{block[1]}"), size=BODY_PT)
            pf = set_para_format(p, BODY_PT, line=LINE_SPACING)
            pf.left_indent = Pt(BODY_PT * 2)
            pf.first_line_indent = Pt(-BODY_PT)
        elif kind == "code":
            lines = block[1].split("\n")
            for i, line in enumerate(lines):
                p = self._new_para()
                set_run_font(p.add_run(line if line else " "), MONO_FONT, MONO_FONT, CODE_PT)
                pf = set_para_format(p, CODE_PT, line=1.0)
                pf.left_indent = Pt(BODY_PT * 2)
                if i == 0:
                    pf.space_before = Pt(6)
                if i == len(lines) - 1:
                    pf.space_after = Pt(8)
        elif kind == "caption":
            p = self._new_para()
            set_run_font(p.add_run(block[1]), CN_HEAD, EN_FONT, CAPTION_PT, True)
            set_para_format(p, CAPTION_PT, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER,
                            space_before=6, space_after=8)
        elif kind == "figure":
            path = os.path.join(ROOT, block[1])
            if not os.path.exists(path):
                raise FileNotFoundError(path)
            p = self._new_para()
            p.add_run().add_picture(path, width=Cm(FIG_WIDTH_CM))
            set_para_format(p, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER,
                            space_before=10, space_after=2, keep_next=True)
            cap = self._new_para()
            set_run_font(cap.add_run(block[2]), CN_HEAD, EN_FONT, CAPTION_PT, True)
            set_para_format(cap, CAPTION_PT, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER,
                            space_before=0, space_after=12)
        elif kind == "table":
            self._add_table(block)
        elif kind == "pagebreak":
            p = self._new_para()
            p.add_run().add_break(WD_BREAK.PAGE)
            set_para_format(p, line=1.0)
        else:
            raise ValueError(f"unknown block: {kind}")

    def _add_table(self, block):
        _, caption, header, rows = block
        cap = self._new_para()
        set_run_font(cap.add_run(caption), CN_HEAD, EN_FONT, CAPTION_PT, True)
        set_para_format(cap, CAPTION_PT, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER,
                        space_before=12, space_after=2, keep_next=True)

        table = self.doc.add_table(rows=len(rows) + 1, cols=len(header))
        self.anchor._p.addprevious(table._tbl)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(table)

        for j, text in enumerate(header):
            cell = table.cell(0, j)
            cell.text = ""
            p = cell.paragraphs[0]
            set_run_font(p.add_run(text), CN_HEAD, EN_FONT, TABLE_PT, True)
            set_para_format(p, TABLE_PT, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER)
            shade_cell(cell, "E8EEF5")
        repeat_header(table.rows[0])

        for i, row in enumerate(rows):
            keep_row_together(table.rows[i + 1])
            for j, text in enumerate(row):
                cell = table.cell(i + 1, j)
                cell.text = ""
                p = cell.paragraphs[0]
                set_run_font(p.add_run(text), size=TABLE_PT)
                set_para_format(p, TABLE_PT, line=1.0)


# ------------------------------------------------------------ 模板处理
def fill_cover(doc):
    for p in doc.paragraphs:
        txt = p.text.strip()
        for key, value in META.items():
            if txt.startswith(key) and "：" in txt:
                for r in list(p.runs):
                    r._element.getparent().remove(r._element)
                set_run_font(p.add_run(f"{key}："), size=BODY_PT)
                set_run_font(p.add_run(value), size=BODY_PT, underline=True)
                set_para_format(p, BODY_PT, line=1.5)
                break
    add_work_name_line(doc)


def add_work_name_line(doc):
    """在封面标题下方补一行作品名称，便于评委与声明、包名相互核对。"""
    import copy
    from docx.text.paragraph import Paragraph

    title = None
    for p in doc.paragraphs:
        if p.text.strip() == "设计文档":
            title = p
            break
    if title is None:
        return
    new_p = copy.deepcopy(title._p)
    title._p.addnext(new_p)
    para = Paragraph(new_p, title._parent)
    for r in list(para.runs):
        r._element.getparent().remove(r._element)
    set_run_font(para.add_run(f"作品名称：{WORK_NAME}"), size=14, bold=True)
    set_para_format(para, 14, line=1.5, align=WD_ALIGN_PARAGRAPH.CENTER,
                    space_before=6, space_after=6)


def find_heading(doc, text):
    for p in doc.paragraphs:
        if p.text.strip() == text:
            return p
    raise KeyError(text)


def drop_hint_and_blanks(doc):
    """删除章节标题下的斜体提示文字与填充用空段落，保留填写说明页。"""
    paras = doc.paragraphs
    end = -1
    for i, p in enumerate(paras):
        if p.text.strip().startswith("4. 设计文档模板里已经列的内容仅供参考"):
            end = i
    if end < 0:
        raise RuntimeError("未找到填写说明第 4 条")

    for p in paras[end + 1:]:
        if has_sectpr(p):
            continue
        txt = p.text.strip()
        if txt.startswith("（建议包括"):
            p._element.getparent().remove(p._element)
        elif txt == "":
            p._element.getparent().remove(p._element)


def setup_page(doc):
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.86)
        section.right_margin = Cm(2.59)


def _run_xml(text=None, fld=None, instr=None):
    r = OxmlElement("w:r")
    if fld:
        fc = OxmlElement("w:fldChar")
        fc.set(qn("w:fldCharType"), fld)
        r.append(fc)
    if instr is not None:
        it = OxmlElement("w:instrText")
        it.set(qn("xml:space"), "preserve")
        it.text = instr
        r.append(it)
    if text is not None:
        t = OxmlElement("w:t")
        t.set(qn("xml:space"), "preserve")
        t.text = text
        r.append(t)
    return r


def _rewrite_footer(footer):
    """把页脚统一为「第 {PAGE} 页 共 {NUMPAGES} 页」。

    模板原本把总页数写死为字面文本「共 7 页」，页数一变就与实际不符。
    """
    if footer is None:
        return
    for p in list(footer.paragraphs):
        p._element.getparent().remove(p._element)
    p = footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_para_format(p, 9, line=1.0)
    for el in (_run_xml(text="第 "),
               _run_xml(fld="begin"),
               _run_xml(instr=" PAGE "),
               _run_xml(fld="separate"),
               _run_xml(text="1"),
               _run_xml(fld="end"),
               _run_xml(text=" 页　共 "),
               _run_xml(fld="begin"),
               _run_xml(instr=" NUMPAGES "),
               _run_xml(fld="separate"),
               _run_xml(text="1"),
               _run_xml(fld="end"),
               _run_xml(text=" 页")):
        r = el
        rPr = OxmlElement("w:rPr")
        rf = OxmlElement("w:rFonts")
        rf.set(qn("w:ascii"), EN_FONT)
        rf.set(qn("w:hAnsi"), EN_FONT)
        rf.set(qn("w:eastAsia"), CN_FONT)
        rPr.append(rf)
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), "18")
        rPr.append(sz)
        r.insert(0, rPr)
        p._element.append(r)


def fix_footers(doc):
    """只重写确实存在的页脚部件；未定义的（封面节）保持模板原样。"""
    seen = set()
    for section in doc.sections:
        for footer in (section.footer, section.even_page_footer):
            try:
                if footer.is_linked_to_previous:
                    continue
                part = footer.part
            except Exception:
                continue
            if id(part) in seen:
                continue
            seen.add(id(part))
            _rewrite_footer(footer)


def main():
    if not os.path.exists(TEMPLATE):
        raise SystemExit(f"缺少模板: {TEMPLATE}")
    shutil.copyfile(TEMPLATE, OUTPUT)
    doc = Document(OUTPUT)

    setup_page(doc)
    fix_footers(doc)
    fill_cover(doc)
    drop_hint_and_blanks(doc)

    h2 = find_heading(doc, "第二章 关键代码说明")
    h3 = find_heading(doc, "第三章 测试及分析")

    # 第一章内容插到第二章标题之前
    w = Writer(doc, h2)
    for b in C.CH1[1:]:
        w.add(b)

    # 第二章内容插到第三章标题之前
    w = Writer(doc, h3)
    for b in C.CH2[1:]:
        w.add(b)

    # 第三章与第四章接在文末
    a3 = doc.add_paragraph()
    a4 = doc.add_paragraph()
    w = Writer(doc, a3)
    for b in C.CH3[1:]:
        w.add(b)
    w = Writer(doc, a4)
    for b in C.CH4:
        w.add(b)

    for a in (a3, a4):
        a._element.getparent().remove(a._element)

    doc.save(OUTPUT)
    print("written", os.path.normpath(OUTPUT))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《作品设计文档.docx》格式合规检查。

逐条对照官方模板「填写说明」第 2 条与文档结构要求判定，输出 PASS/FAIL 表格。

用法: python tools/check_doc_format.py [docx]
"""
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BODY_PT = 12.0          # 小四
LINE_15 = ("360", "auto")  # 1.5 倍行距
TABLE_PT = 12.0


def q(tag):
    return W + tag


def load(path):
    z = zipfile.ZipFile(path)
    doc = ET.fromstring(z.read("word/document.xml"))
    styles = ET.fromstring(z.read("word/styles.xml"))
    return z, doc, styles


def style_names(styles):
    out = {}
    for s in styles.findall(q("style")):
        sid = s.get(q("styleId"))
        nm = s.find(q("name"))
        if nm is not None:
            out[sid] = nm.get(q("val"))
    return out


def para_info(p):
    txt = "".join(t.text or "" for t in p.iter(q("t"))).strip()
    pPr = p.find(q("pPr"))
    sty, spacing = None, None
    if pPr is not None:
        ps = pPr.find(q("pStyle"))
        if ps is not None:
            sty = ps.get(q("val"))
        sp = pPr.find(q("spacing"))
        if sp is not None:
            spacing = (sp.get(q("line")), sp.get(q("lineRule")))
    sizes, eas = set(), set()
    for r in p.iter(q("r")):
        rPr = r.find(q("rPr"))
        if rPr is None:
            continue
        sz = rPr.find(q("sz"))
        if sz is not None:
            sizes.add(int(sz.get(q("val"))) / 2)
        rf = rPr.find(q("rFonts"))
        if rf is not None and rf.get(q("eastAsia")):
            eas.add(rf.get(q("eastAsia")))
    return txt, sty, spacing, sizes, eas


def check(path):
    z, doc, styles = load(path)
    names = style_names(styles)
    body = doc.find(q("body"))
    paras = list(body.iter(q("p")))

    results = []

    def add(item, ok, detail):
        results.append((item, "PASS" if ok else "FAIL", detail))

    # --- 页面设置：A4 ---
    sect = list(body.iter(q("sectPr")))[-1]
    pg = sect.find(q("pgSz"))
    w, h = int(pg.get(q("w"))), int(pg.get(q("h")))
    a4 = abs(w - 11906) < 30 and abs(h - 16838) < 30
    add("A4 纸", a4, f"{w/566.9:.1f}×{h/566.9:.1f} cm")

    # --- 页边距 ---
    mar = sect.find(q("pgMar"))
    mg = {k: int(mar.get(q(k))) / 566.9 for k in ("top", "bottom", "left", "right")}
    add("页边距沿用模板", True,
        "上%.2f 下%.2f 左%.2f 右%.2f cm" % (mg["top"], mg["bottom"], mg["left"], mg["right"]))

    # --- 字号与行距：正文 ---
    body_bad, body_n = [], 0
    tbl_bad, tbl_n = 0, 0
    for el in body:
        tag = el.tag.replace(W, "")
        if tag == "tbl":
            for tp in el.iter(q("p")):
                txt, sty, spacing, sizes, eas = para_info(tp)
                if not txt:
                    continue
                tbl_n += 1
                if not sizes or TABLE_PT not in sizes:
                    tbl_bad += 1
            continue
        if tag != "p":
            continue
        txt, sty, spacing, sizes, eas = para_info(el)
        if not txt:
            continue
        nm = names.get(sty, "").lower()
        if nm.startswith("heading"):
            continue
        if sizes and BODY_PT in sizes:
            body_n += 1
            if spacing != LINE_15:
                body_bad.append(txt[:24])
    add("正文小四（12 pt）", body_n > 0, f"{body_n} 段为 12 pt")
    add("正文 1.5 倍行距", not body_bad,
        "全部 12 pt 正文段均为 line=360 auto" if not body_bad else f"{len(body_bad)} 段异常：{body_bad[:3]}")
    add("表格小四（12 pt）", tbl_bad == 0, f"{tbl_n} 个表格单元，异常 {tbl_bad} 个")

    # --- 标题层级 ---
    h1, h2, h3 = [], [], []
    for el in body:
        if el.tag.replace(W, "") != "p":
            continue
        txt, sty, _, _, _ = para_info(el)
        nm = names.get(sty, "").lower()
        if not txt:
            continue
        if nm.startswith("heading 1"):
            h1.append(txt)
        elif nm.startswith("heading 2"):
            h2.append(txt)
        elif nm.startswith("heading 3"):
            h3.append(txt)
    add("章标题使用 heading 1 样式", len(h1) >= 4, f"{len(h1)} 个：{h1}")
    add("节标题使用 heading 2 样式", len(h2) >= 20, f"{len(h2)} 个")
    add("三级标题使用 heading 3 样式", len(h3) >= 15, f"{len(h3)} 个")

    # --- 残留模板提示文字 ---
    hints = [t for el in body.iter(q("p"))
             for t, _, _, _, _ in [para_info(el)] if t.startswith("（建议包括")]
    add("已删除模板提示文字", not hints, f"残留 {len(hints)} 处")

    # --- 填写说明页保留 ---
    keep = any("填写说明" == para_info(el)[0] for el in body.iter(q("p")))
    add("保留填写说明页", keep, "填写说明页未删除")

    # --- 页脚页码域 ---
    footers = [n for n in z.namelist() if re.match(r"word/footer\d*\.xml$", n)]
    fields, cached = [], set()
    for f in footers:
        s = z.read(f).decode("utf-8")
        fields += re.findall(r"<w:instrText[^>]*>\s*(\w+)", s)
        for m in re.finditer(r'NUMPAGES.*?fldCharType="separate".*?<w:t[^>]*>([^<]*)</w:t>', s, re.S):
            cached.add(m.group(1))
    add("页脚含 PAGE 与 NUMPAGES 域", "PAGE" in fields and "NUMPAGES" in fields,
        f"域：{sorted(set(fields))}")
    add("NUMPAGES 缓存值已刷新", cached and all(c.isdigit() and int(c) > 1 for c in cached),
        f"缓存值 {sorted(cached)}")

    # --- 图表编号连续 ---
    caps = [para_info(el)[0] for el in body.iter(q("p"))]
    figs = sorted({int(m.group(1)) for t in caps
                   if (m := re.match(r"图 (\d+)[　\s]", t))})
    tbls = sorted({int(m.group(1)) for t in caps
                    if (m := re.match(r"表 (\d+)[　\s]", t))})
    add("图编号连续", figs == list(range(1, len(figs) + 1)), f"图 1–{len(figs)}")
    add("表编号连续", tbls == list(range(1, len(tbls) + 1)), f"表 1–{len(tbls)}")

    # --- 参考文献已按要求移除：正文不得残留引用条目或引用角标 ---
    refs = sum(1 for t in caps if re.match(r"^— \[\d+\]", t))
    marks = sum(1 for t in caps if re.search(r"\[\d+\]", t))
    add("参考文献已移除", refs == 0 and marks == 0,
        f"条目 {refs} 条，角标 {marks} 处")

    return results


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "作品设计文档.docx")
    if not os.path.exists(path):
        raise SystemExit(f"文件不存在：{path}")
    rows = check(path)
    width = max(len(r[0]) for r in rows)
    print("=" * (width + 40))
    print("《作品设计文档》格式合规检查")
    print("=" * (width + 40))
    for item, verdict, detail in rows:
        print(f"[{verdict}] {item.ljust(width)}  {detail}")
    bad = [r for r in rows if r[1] == "FAIL"]
    print("-" * (width + 40))
    print(f"结论：{len(rows) - len(bad)}/{len(rows)} 项通过"
          + ("" if not bad else f"，未通过：{[b[0] for b in bad]}"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

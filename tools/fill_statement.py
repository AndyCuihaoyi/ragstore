#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""填写《作品原创性声明.docx》。

仅填写作品名称；组员签名与日期需手写后扫描或拍照替换。

用法: python tools/fill_statement.py
"""
import os
import shutil

from docx import Document

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "templates", "作品原创性声明.docx")
OUTPUT = os.path.join(ROOT, "作品原创性声明.docx")

WORK_NAME = "RAGStore：面向检索增强生成的轻量级向量存储引擎"


def main():
    if not os.path.exists(TEMPLATE):
        raise SystemExit(f"缺少模板: {TEMPLATE}")
    tmp = OUTPUT + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    shutil.copyfile(TEMPLATE, tmp)
    doc = Document(tmp)

    filled = False
    for p in doc.paragraphs:
        if "所提交的作品" not in p.text:
            continue
        # 模板中作品名称的位置是若干段带下划线的空白 run
        blanks = [r for r in p.runs if r.underline and not r.text.strip()]
        if not blanks:
            raise RuntimeError("未找到作品名称的空位")
        blanks[0].text = WORK_NAME
        for r in blanks[1:]:
            r.text = ""
        filled = True
        break

    if not filled:
        raise RuntimeError("未找到声明正文段落")

    doc.save(tmp)
    try:
        os.replace(tmp, OUTPUT)
    except PermissionError:
        print("!! 目标文件被占用（可能正�� Word 中打开），新文件保留在：", os.path.normpath(tmp))
        raise SystemExit(2)
    print("written", os.path.normpath(OUTPUT))
    print("作品名称:", WORK_NAME)


if __name__ == "__main__":
    main()

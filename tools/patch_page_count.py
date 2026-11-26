#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把页脚里 NUMPAGES 域的缓存值改成实测页数。

域代码本身在 Word 中会自动更新，但 WPS、网页预览、PDF 直读等非 Word 场景
会直接显示缓存值。模板里该缓存值是 1，与实际页数不符。

用法: python tools/patch_page_count.py <docx> <页数>
"""
import os
import re
import shutil
import sys
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def patch_footer(xml_bytes, pages):
    s = xml_bytes.decode("utf-8")
    # 定位 NUMPAGES 域的 separate..end 之间的缓存文本
    out = []
    idx = 0
    changed = 0
    while True:
        i = s.find("NUMPAGES", idx)
        if i < 0:
            out.append(s[idx:])
            break
        sep = s.find('w:fldCharType="separate"', i)
        end = s.find('w:fldCharType="end"', i)
        if sep < 0 or end < 0:
            out.append(s[idx:])
            break
        # separate 与 end 之间的 w:t 才是缓存值
        seg = s[sep:end]
        new_seg, n = re.subn(r'(<w:t[^>]*>)[^<]*(</w:t>)',
                             lambda m: m.group(1) + str(pages) + m.group(2),
                             seg, count=1)
        out.append(s[idx:sep])
        out.append(new_seg)
        changed += n
        idx = end
    return "".join(out).encode("utf-8"), changed


def main():
    if len(sys.argv) < 3:
        raise SystemExit("用法: python tools/patch_page_count.py <docx> <页数>")
    path = os.path.abspath(sys.argv[1])
    pages = int(sys.argv[2])

    tmp = path + ".tmp"
    total = 0
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if re.match(r"word/footer\d*\.xml$", item.filename):
                data, n = patch_footer(data, pages)
                total += n
            zout.writestr(item, data)
    os.replace(tmp, path)
    print(f"patched {os.path.basename(path)}: {total} 处 NUMPAGES 缓存值 -> {pages}")


if __name__ == "__main__":
    main()

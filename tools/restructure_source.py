#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 OceanBase 加赛的交付物重组为华为存储竞赛的作品仓库。

做三件事：
  1. 重命名：minivectordb → ragstore，MiniVectorDB → RAGStore，MINIVECDB → RAGSTORE
  2. 剔除上游 seekdb 骨架（CI、devcontainer、bazel 等），这些不属于本作品
  3. 把开发过程存档（原样保留）单独归入 development-record/

开发过程存档与其生成脚本保持原样：它们记录的是参赛赛题阶段的工作，
其中的项目命名是当时的事实，改写会破坏记录的可信度。

用法: python tools/restructure_source.py <源目录> <目标目录>
"""
import json
import os
import shutil
import sys

# 开发过程存档：保持原样，不重命名、不改写
#
# 目录项按前缀匹配：agent/ 下的每一个文件都属于存档，
# 只按文件名匹配会漏掉 agent/conversation.json，
# 造成根副本被保留而 agent 副本被改写，两份材料就此分叉。
KEEP_VERBATIM_DIRS = ("agent",)
KEEP_VERBATIM_FILES = {
    "conversation.json",
    "tools/build_conversation_json.py",
    "tools/check_conversation_against_record.py",
    "tools/check_conversation_json.py",
    "tools/check_prompt_authorship.py",
    "tools/record_current_turns.py",
    "tools/recover_record_turns.py",
    "tools/record_snapshot.json",
}

# 上游 seekdb 骨架，与本作品无关，剔除
DROP = {
    ".github", ".devcontainer", ".agents", ".gitlab-ci.yml", ".akfarm",
    ".akperformancetest", ".bazelrc", ".bazelversion", ".secignore",
    ".secignore.opensource", ".cursor", ".vscode",
}

REPLACEMENTS = [
    ("MINIVECDB", "RAGSTORE"),
    ("MiniVectorDB", "RAGStore"),
    ("minivectordb", "ragstore"),
]

TEXT_EXT = {".rs", ".toml", ".md", ".py", ".sh", ".json", ".txt", ".yml", ".yaml", ".cfg", ".in", ""}


def is_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in TEXT_EXT:
        return True
    try:
        with open(path, "rb") as fh:
            head = fh.read(4096)
        if b"\x00" in head:
            return False
        head.decode("utf-8")
        return True
    except (UnicodeDecodeError, OSError):
        return False


def rewrite(path):
    if not is_text(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except (UnicodeDecodeError, OSError):
        return 0
    original = text
    for a, b in REPLACEMENTS:
        text = text.replace(a, b)
    if text != original:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        return 1
    return 0


def main():
    if len(sys.argv) < 3:
        raise SystemExit("用法: python tools/restructure_source.py <源目录> <目标目录>")
    src, dst = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)

    kept_verbatim = []
    changed = 0

    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        rel = os.path.relpath(dirpath, src)
        rel = "" if rel == "." else rel.replace("\\", "/")

        if rel.split("/")[0] in DROP:
            continue

        target_dir = os.path.join(dst, rel) if rel else dst
        os.makedirs(target_dir, exist_ok=True)

        for f in filenames:
            if rel == "" and f in DROP:
                continue
            full = os.path.join(dirpath, f)

            if rel == "" and f in (".gitignore", ".gitattributes"):
                dstp = os.path.join(target_dir, f)
                shutil.copy2(full, dstp)
                changed += rewrite(dstp)
                continue

            rel_file = f"{rel}/{f}" if rel else f

            keep = rel_file in KEEP_VERBATIM_FILES or \
                rel_file.split("/")[0] in KEEP_VERBATIM_DIRS
            if keep:
                shutil.copy2(full, os.path.join(target_dir, f))
                kept_verbatim.append(rel_file)
                continue

            shutil.copy2(full, os.path.join(target_dir, f))
            changed += rewrite(os.path.join(target_dir, f))

    # crate 目录改名
    crate_old = os.path.join(dst, "minivectordb")
    crate_new = os.path.join(dst, "ragstore")
    if os.path.isdir(crate_old):
        os.rename(crate_old, crate_new)

    # 开发过程存档单独归位
    rec = os.path.join(dst, "development-record")
    os.makedirs(rec, exist_ok=True)
    for name in ("conversation.json", "agent"):
        p = os.path.join(dst, name)
        if os.path.exists(p):
            shutil.move(p, os.path.join(rec, name))
    tool_src = os.path.join(dst, "tools")
    tool_rec = os.path.join(rec, "tools")
    os.makedirs(tool_rec, exist_ok=True)
    for name in sorted(KEEP_VERBATIM_FILES):
        if not name.startswith("tools/"):
            continue
        base = name.split("/", 1)[1]
        p = os.path.join(tool_src, base)
        if os.path.exists(p):
            shutil.move(p, os.path.join(tool_rec, base))

    print(f"重命名文件数 : {changed}")
    print(f"原样保留     : {len(kept_verbatim)} 项 -> development-record/")
    for k in kept_verbatim:
        print("   ", k)


if __name__ == "__main__":
    main()

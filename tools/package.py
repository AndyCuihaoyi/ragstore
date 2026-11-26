#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""组装参赛作品压缩包。

用法: python tools/package.py <华为云账号>
输出: Freetrack-<华为云账号>.zip
"""
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGE = os.path.join(ROOT, ".package")


README = """# RAGStore：面向检索增强生成的轻量级向量存储引擎

> 参赛作品 · 第四届大学生信息存储技术竞赛 · 自由赛道（Free track）
> 作品名称：RAGStore：面向检索增强生成的轻量级向量存储引擎

## 一、作品简介

RAGStore 是一个从零实现的轻量级向量存储引擎，面向企业知识库 RAG 检索场景。
存储引擎、查询执行器、向量索引、事务与崩溃恢复全部自行实现，编译期依赖图为空
（`Cargo.lock` 仅含自身一个 package），`cargo build --offline --locked` 必然成功。

作品承担 RAG 链路中的向量写入与向量召回两步。
其核心主张是：检索环节的漏召回无法被下游的重排与生成补救，
因此召回率应当被构造保证，而不是依赖调优得到的经验值。
本作品通过 IVF 倒排检索的精确剪枝，使 Recall@10 在有过滤与无过滤两种情形下均为 1.000。

| 指标 | 数值 |
| --- | --- |
| 源代码 | 13 771 行 / 32 个源文件（Rust 2021，零外部依赖） |
| 单元 + 协议测试 | 143 + 15 项全部通过 |
| 召回率 Recall@10 | 1.000（有过滤与无过滤，与暴力检索答案逐字节一致） |
| 查询耗时 | 900.6 ms / 1000 次 TopK（10 000 行 x 128 维，三轮中位数） |
| 查询 I/O | 1.611 MB（相对基线版本降低 4.58 倍） |
| 崩溃恢复 | 12 轮 SIGKILL 全部通过且幂等（宿主与容器内各 12 轮） |

## 二、压缩包内容

```
├── README.md                 本文件
├── 作品设计文档.docx          方案设计 / 关键代码说明 / 测试及分析 / 创新性说明 / 参考文献
├── 作品原创性声明.docx        需组员手写签名后替换
├── figures/                  设计文档中全部框图的源文件（PNG）
└── source/                   源码、构建脚本、测试工具、性能数据与开发记录
    ├── ragstore/             Rust 源码（主 crate，零外部依赖）
    ├── Dockerfile            容器构建定义，镜像内仅含二进制
    ├── docs/design.md        存储、索引与恢复的完整设计说明
    ├── docs/perf/            性能台账、剖析报告与原始测量数据（JSON）
    ├── tools/                测试与性能测量脚本
    ├── development-record/   开发过程记录（保留参赛赛题阶段的项目命名原样）
    └── README.md             源码级说明：协议、SQL 子集、运行参数、测试方法
```

## 三、快速复现

```bash
cd source/ragstore

# 构建（离线，零外部依赖）
cargo build --release --offline --locked

# 单元测试与协议集成测试
cargo test --release --offline --locked

# 差分自测（与参考执行器逐字节比对）
python3 ../tools/selftest.py

# 公开题包，精确与近似两种模式
python3 ../tools/run_public_cases.py
python3 ../tools/run_public_cases.py --mode ann

# 崩溃恢复幂等验证
bash ../tools/killtest.sh

# 召回率校验
python3 ../tools/check_ann_recall.py

# 性能测量（绑核单核，三轮取中位数）
python3 ../tools/bench_median.py --mode exact --rounds 3 --cpu 3 --cpus 3
```

容器方式：

```bash
cd source
docker build -t ragstore .
docker run --rm -i -v "$PWD/data:/data" ragstore --data-dir /data
```

## 四、源码目录说明

`source/ragstore/`、`source/Dockerfile`、`source/docs/` 与 `source/tools/` 为参赛团队的原创工作。

`source/development-record/` 是开发过程存档，记录的是本作品在另一项赛题（OceanBase 数据库大赛加赛）
阶段的工作过程，其中的项目命名沿用当时的赛题名称，未作改写，以保持记录的可信度。
该目录仅用于佐证开发过程的真实性，不参与构建与评测。

## 五、创新点摘要

1. **IVF 倒排检索的精确剪枝** —— 依据三角不等式构造单元距离下界，剪枝不改变答案，
   召回率由构造保证而非调参获得。
2. **过滤先于 TopK 选择** —— 返回的是「满足过滤条件中的最近 k 条」，
   而非「全表最近 k 条里恰好满足过滤的」，这是语义正确性问题而非性能问题。
3. **流式投影** —— 查询峰值内存与表大小解耦，只随 k 与单行宽度增长。
4. **行镜像的向量占位标记** —— 向量列在落盘镜像中只留 1 字节占位，
   128 维下写放大降低约 30 倍。
5. **索引不持有向量副本** —— 索引仅保存行身份信息，开销降至每行 8 字节。
6. **以量化论证替代直觉的工程决策** —— 例如块内行主序的选择以 20 倍的成本比较为依据。
7. **测量方法论的自纠错** —— 推翻自身「性能瓶颈在驱动开销」的错误归因，
   并由此建立可复现的测量规程。

详见《作品设计文档》第四章。

## 六、说明

- 评测平台的正式参考基线数值未公开，因此文中所有性能倍数均对应一个明确标注
  commit 号的团队自研版本，并区分了算法级改进与常数级改进。
- 《作品原创性声明》需全部组员手写签名并填写日期后，再作为独立文件随包提交。
"""



def stage():
    if os.path.exists(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)

    shutil.copyfile(os.path.join(ROOT, "作品设计文档.docx"),
                    os.path.join(STAGE, "作品设计文档.docx"))
    shutil.copyfile(os.path.join(ROOT, "作品原创性声明.docx"),
                    os.path.join(STAGE, "作品原创性声明.docx"))

    figs = os.path.join(STAGE, "figures")
    os.makedirs(figs)
    figdir = os.path.join(ROOT, "docs", "figures")
    for f in sorted(os.listdir(figdir)):
        if f.endswith(".png"):
            shutil.copyfile(os.path.join(figdir, f), os.path.join(figs, f))

    src = os.path.join(STAGE, "source")
    shutil.copytree(os.path.join(ROOT, "source"), src,
                    ignore=shutil.ignore_patterns(".git", "target"))

    with open(os.path.join(STAGE, "README.md"), "w", encoding="utf-8") as fh:
        fh.write(README)


def main():
    if len(sys.argv) < 2:
        raise SystemExit("用法: python tools/package.py <华为云账号>")
    account = sys.argv[1].strip()
    if not account:
        raise SystemExit("华为云账号不能为空")

    stage()
    name = f"Freetrack-{account}.zip"
    out = os.path.join(ROOT, name)
    if os.path.exists(out):
        os.remove(out)

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for dirpath, _, files in os.walk(STAGE):
            for f in files:
                full = os.path.join(dirpath, f)
                z.write(full, os.path.relpath(full, STAGE).replace("\\", "/"))

    size = os.path.getsize(out) / 1024 / 1024
    print(f"written {os.path.normpath(out)}  ({size:.2f} MB)")
    shutil.rmtree(STAGE)


if __name__ == "__main__":
    main()

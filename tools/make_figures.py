#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成作品设计文档所需的全部框图。

用法: python tools/make_figures.py
输出: docs/figures/fig-1..fig-7.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "figures")
os.makedirs(OUT, exist_ok=True)

C_LINE = "#1f2a37"
C_FILL = "#eef2f7"
C_ACC = "#d6e4f2"
C_HOT = "#fbe4e0"
C_DIM = "#6b7280"

# 图在 Word 中按 15 cm 栏宽插入；画布 8 in ⇒ 缩放系数 0.738，
# 因此把画布内字号放大 1.15 倍，最终落在纸面上约 7.6 pt，可读。
FONT_SCALE = 1.15


def F(x):
    return round(x * FONT_SCALE, 1)


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fill=C_FILL, fs=F(9), bold=False, ls="-", ec=C_LINE):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.3,rounding_size=1.0",
        linewidth=1.1, edgecolor=ec, facecolor=fill, linestyle=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight="bold" if bold else "normal", color=C_LINE,
            linespacing=1.6)


def group(ax, x, y, w, h, label):
    ax.add_patch(Rectangle((x, y), w, h, linewidth=0.9, edgecolor=C_DIM,
                           facecolor="#ffffff", linestyle=(0, (5, 3)), zorder=-1))
    ax.text(x + 1.0, y + h - 1.2, label, ha="left", va="top",
            fontsize=F(8.5), color=C_DIM, fontweight="bold")


def arrow(ax, p1, p2, label=None, lx=None, ly=None, fs=F(8), color=C_LINE,
          rad=0.0, ha="center"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=10,
                                 linewidth=1.0, color=color,
                                 connectionstyle=f"arc3,rad={rad}",
                                 shrinkA=0, shrinkB=0))
    if label:
        if lx is None:
            lx = (p1[0] + p2[0]) / 2
        if ly is None:
            ly = (p1[1] + p2[1]) / 2
        ax.text(lx, ly, label, ha=ha, va="center", fontsize=fs, color=C_LINE)


def caption(fig, text):
    """图题改由 Word 正文段落承载，避免与文档中的图号重复。"""
    pass


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("written", os.path.normpath(p))


# ---------------------------------------------------------------- 图 1 系统总体架构
def fig1():
    fig, ax = canvas(8.00, 5.67)
    group(ax, 3, 82, 94, 16, "应用层")
    box(ax, 7, 85.5, 26, 9, "企业知识库 RAG 检索\n（文档入库 / 召回 / 重排）", C_ACC, 9)
    box(ax, 37, 85.5, 26, 9, "AI Agent 长期记忆\n（会话语义检索）", C_ACC, 9)
    box(ax, 67, 85.5, 26, 9, "判题驱动 / 压测客户端\n（JSON Lines）", C_ACC, 9)

    group(ax, 3, 63, 94, 15, "接口层")
    box(ax, 8, 65.5, 34, 9.5, "SQL 词法与语法分析\nsql/lexer.rs　sql/parser.rs", C_FILL, 8.5)
    box(ax, 56, 65.5, 36, 9.5, "协议层：JSON Lines\nproto/json.rs　proto/session.rs", C_FILL, 8.5)

    group(ax, 3, 38, 94, 21, "引擎层")
    box(ax, 6, 46, 28, 9.5, "通用执行器（流式投影）\nexec/query.rs", C_FILL, 8.5)
    box(ax, 36, 46, 28, 9.5, "向量检索\nexact.rs　ann.rs", C_ACC, 9, bold=True)
    box(ax, 66, 46, 28, 9.5, "事务缓冲与语句级撤销\nengine.rs", C_FILL, 8.5)
    box(ax, 18, 39.5, 64, 5.5, "TopK 堆　过滤下推　距离内核（AVX2）", "#f7f9fb", 8.5)

    group(ax, 3, 13, 94, 21, "存储层")
    box(ax, 6, 21, 28, 9.5, "块缓存缓冲池\nbufferpool.rs\n三类缓存共享预算", C_FILL, 8)
    box(ax, 36, 21, 28, 9.5, "列式存储\ntable.rs　format.rs\nmeta.dat　col.dat　vec.dat", C_ACC, 8, bold=True)
    box(ax, 66, 21, 28, 9.5, "预写日志 WAL\nwal.rs\n完整行镜像 · 提交标记分组重放", C_FILL, 8)
    box(ax, 18, 14.5, 64, 5.0, "IVF 倒排索引（驻留内存，启动时重建）", "#f7f9fb", 8.5)

    group(ax, 3, 2, 94, 8, "持久层")
    box(ax, 20, 3.2, 60, 5.4, "文件系统　/data　（单进程单客户端，容器化部署）", "#f3f4f6", 9)

    arrow(ax, (20, 85.5), (20, 75), "SQL", lx=16.5, ly=80.2)
    arrow(ax, (50, 85.5), (50, 75), "SQL", lx=46.5, ly=80.2)
    arrow(ax, (80, 85.5), (74, 75), "JSONL", lx=84, ly=80.2)
    arrow(ax, (25, 65.5), (20, 55.5), "DML", lx=17.5, ly=60.4)
    arrow(ax, (74, 65.5), (50, 55.5), "请求", lx=69, ly=60.4)
    arrow(ax, (20, 46), (30, 45.2), "", rad=0.25)
    arrow(ax, (50, 46), (50, 45.2), "")
    arrow(ax, (80, 46), (72, 45.2), "", rad=-0.25)
    arrow(ax, (30, 45.2), (20, 30.5), "读块", lx=15.5, ly=37.5)
    arrow(ax, (50, 45.2), (50, 30.5), "")
    arrow(ax, (70, 45.2), (80, 30.5), "WAL 追加", lx=86.5, ly=37.5)
    arrow(ax, (20, 30.5), (35, 17), "", rad=-0.2)
    arrow(ax, (50, 30.5), (50, 19.5), "")
    arrow(ax, (80, 30.5), (65, 17), "", rad=0.2)
    arrow(ax, (50, 14.5), (50, 8.6), "刷盘", lx=56, ly=11.6)

    caption(fig, "图 1  RAGStore 系统总体架构")
    save(fig, "fig-1-architecture.png")


# ---------------------------------------------------------------- 图 2 部署拓扑
def fig2():
    fig, ax = canvas(8.00, 5.00)
    group(ax, 3, 54, 94, 43, "宿主机（Linux / Ubuntu 24.04）")
    box(ax, 6, 59, 27, 31, "客户端\n───────────\n· 判题驱动（JSONL）\n· RAG 检索服务\n· 压测脚本 bench.py", C_FILL, 8.5)

    box(ax, 38, 58, 57, 35, "", "#ffffff", 9.5, ls="-")
    ax.text(66.5, 90, "Docker 容器　ragstore（--cpus=2，2 GiB）",
            ha="center", va="center", fontsize=F(9.5), fontweight="bold", color=C_LINE)
    box(ax, 42, 73, 49, 12, "单进程服务 main.rs\nstdin / stdout ←→ JSON Lines 协议", C_ACC, 8.5)
    box(ax, 42, 61, 24, 9.5, "引擎\nexec / vector", C_FILL, 8.5)
    box(ax, 69, 61, 24, 9.5, "存储\ntable / wal", C_FILL, 8.5)
    arrow(ax, (60, 73), (54, 70.5), "")
    arrow(ax, (74, 73), (81, 70.5), "")

    group(ax, 3, 15, 94, 32, "容器可写层　/data　（持久化目录）")
    box(ax, 6, 21, 20, 21, "wal.dat\n预写日志\n（完整行镜像）", C_FILL, 8.5)
    box(ax, 28, 21, 17, 21, "catalog.dat\n表定义目录", C_FILL, 8.5)
    box(ax, 47, 21, 25, 21, "<table>/meta.dat\n行目录（48 B 定长）\n<table>/col.dat\n标量行镜像", C_FILL, 8)
    box(ax, 74, 21, 20, 21, "<table>/vec.dat\n向量列（行主序）\n<table>/index.dat", C_FILL, 8)

    box(ax, 3, 2, 94, 12, "宿主机块设备 / 操作系统页缓存\n（平台以 cgroup v2 的 io.stat 统计字节数；查询阶段实际无物理 I/O）", "#f3f4f6", 8.5)

    arrow(ax, (33, 79), (42, 79), "")
    arrow(ax, (52, 58), (40, 42), "落盘", lx=53, ly=50)
    arrow(ax, (56, 21), (56, 14), "")

    caption(fig, "图 2  部署拓扑与持久化路径")
    save(fig, "fig-2-deployment.png")


# ---------------------------------------------------------------- 图 3 存储格式
def fig3():
    fig, ax = canvas(8.00, 4.95)
    group(ax, 2, 55, 47, 43, "行目录 meta.dat（每行 48 字节定长记录）")
    fields = [("pk", "i64"), ("col_off", "u64"), ("col_len", "u32"), ("vec_blk", "u32"),
              ("vec_slot", "u32"), ("version", "u32"), ("alive", "u8")]
    x = 4.5
    for name, ty in fields:
        box(ax, x, 74, 5.6, 7.0, f"{name}\n{ty}", C_FILL, 7.0)
        x += 5.95
    ax.text(25.5, 70.5, "+ 11 字节填充　（示意图，宽度不按字节比例）",
            ha="center", fontsize=F(7.6), color=C_DIM)
    ax.text(25.5, 65.8, "定长记录 → 同一数据块的条目在文件中连续\n一次系统调用即可读完整个块的行目录",
            ha="center", va="center", fontsize=F(8.2), color=C_LINE, linespacing=1.6)

    group(ax, 52, 55, 46, 43, "标量行镜像 col.dat（带标签的变长序列）")
    box(ax, 55, 78, 12, 6.2, "BIGINT\n0x01 + 8 B", C_FILL, 7.6)
    box(ax, 68.5, 78, 13, 6.2, "VARCHAR\n0x02 + 4 B + UTF8", C_FILL, 7.6)
    box(ax, 83, 78, 12, 6.2, "VECTOR\n0x03 + 4 B + dim×4 B", C_FILL, 7.6)
    box(ax, 55, 70.5, 40, 6.0, "VABOVE　0x04　← 向量列在此只留 1 字节占位标记", C_HOT, 8.4, bold=True)
    ax.text(75, 65.0, "128 维下：含向量 533 B → 去向量 17 B\n写放大降低 30 倍",
            ha="center", va="center", fontsize=F(8.4), color=C_LINE, linespacing=1.6)

    group(ax, 2, 4, 96, 45, "向量文件 vec.dat 与块内行主序布局")
    box(ax, 5, 12, 15, 9, "16 B 文件头\nmagic / ver\ndim / block_rows", C_FILL, 7.8)
    box(ax, 22, 12, 20, 9, "块 0\nslot0：dim 个 f32 连续\nslot1：dim 个 f32 连续", C_ACC, 8)
    box(ax, 44, 12, 20, 9, "块 1\nslot0 …\n……", C_ACC, 8)
    box(ax, 66, 12, 14, 9, "块 b\n……", C_ACC, 8)
    ax.text(5, 8.5, "offset = 16 + ((b × block_rows) + s) × dim × 4",
            ha="left", fontsize=F(8.4), color=C_LINE)

    box(ax, 62, 26, 34, 15,
        "行主序 vs 列主序的量化论证\n"
        "转置 2 MB 块 ≈ 200 μs\n"
        "而它能并行化的 8 行仅省 ≈ 11 μs\n"
        "→ 20 倍反对，布局保持行主序",
        "#f7f9fb", 8.4, ec=C_DIM)

    caption(fig, "图 3  存储格式：行目录、标量行镜像与向量文件")
    save(fig, "fig-3-storage-format.png")


# ---------------------------------------------------------------- 图 4 缓冲池
def fig4():
    fig, ax = canvas(8.00, 4.07)
    group(ax, 3, 54, 94, 42, "缓冲池（--buffer-pool-mb 是三个缓存的合计预算）")
    box(ax, 7, 63, 26, 26, "向量缓存\n（块内解码为 f32 矩阵）\n预算 50%\n\n512 KB / 块\n（1024 行 × 128 维）", C_ACC, 8.5)
    box(ax, 37, 63, 26, 26, "行目录缓存\n（48 B 定长记录数组）\n预算 25%\n\n按块整体换入换出", C_FILL, 8.5)
    box(ax, 67, 63, 26, 26, "标量列缓存\n（解码后的标量列）\n预算 25%\n\n向量子列单独存放", C_FILL, 8.5)

    group(ax, 3, 4, 94, 45, "读路径与换出策略")
    box(ax, 7, 27, 22, 15, "扫描器\n按块读取", C_FILL, 9)
    box(ax, 33, 24, 27, 21, "LRU 双向链表\ntouch / evict 均为常数步\n\n（线性扫描会退化为 O(n^2)）", C_ACC, 8.5)
    box(ax, 64, 27, 28, 15, "写入 → 立即失效对应块\n缓存中永不持有比文件更旧的值", C_FILL, 8.5)
    box(ax, 33, 8, 58, 12, "容量核算：块分配、行列分配、每个值的字节数\n全部向编译器问 size_of，不做估算\n（估算偏小 → 缓存实际持有量翻倍）", "#f7f9fb", 8.4)

    arrow(ax, (18, 42), (16, 63), "取块", lx=11.5, ly=52)
    arrow(ax, (46, 45), (46, 63), "")
    arrow(ax, (78, 42), (78, 63), "")

    caption(fig, "图 4  块缓存缓冲池：共享预算与 LRU 换出")
    save(fig, "fig-4-bufferpool.png")


# ---------------------------------------------------------------- 图 5 向量检索流程
def fig5():
    fig, ax = canvas(8.00, 4.80)
    box(ax, 5, 84, 30, 11, "SQL 语句\nORDER BY L2_DISTANCE(...) ASC\nLIMIT k", C_FILL, 8.5)
    box(ax, 42, 84, 32, 11, "识别：单升序 L2_DISTANCE + LIMIT\n→ 走向量检索路径", C_ACC, 8.5)
    box(ax, 80, 84, 15, 11, "否则走\n通用执行器", C_FILL, 8)

    box(ax, 26, 67, 48, 13,
        "过滤下推：先筛后选\n"
        "过滤在 TopK 选择之前施加\n"
        "→ 返回「满足过滤条件中的最近 k 条」\n"
        "而不是「全表最近 k 条里恰好满足过滤的」",
        C_HOT, 8.6, bold=True)
    arrow(ax, (58, 84), (52, 80), "")

    box(ax, 5, 43, 42, 19,
        "精确路径　exact.rs\n"
        "① 一次读入块的行目录\n"
        "② 一次读入块的向量（行主序连续）\n"
        "③ 有过滤才解码标量列\n"
        "④ 距离送入容量 ≤ k 的堆　O(rows·log k)",
        C_FILL, 8.2)
    box(ax, 53, 43, 42, 19,
        "近似路径　ann.rs / index.rs\n"
        "IVF 粗聚类倒排表，按质心距离访问单元\n"
        "精确剪枝：d_c - R_c 是该单元的距离下界\n"
        "→ 剪枝后答案与暴力扫描逐字节一致",
        C_ACC, 8.2)

    box(ax, 5, 30, 90, 9,
        "TopK 堆（容量 ≤ k）：最差候选置于堆顶，新候选一次比较即可淘汰\n"
        "距离相同按主键升序破平 —— 与 SQL 的 ORDER BY 语义一致",
        "#f7f9fb", 8.5)
    arrow(ax, (26, 43), (26, 39), "")
    arrow(ax, (74, 43), (74, 39), "")

    box(ax, 5, 16, 42, 11, "事务内未提交行不在存储中\n→ 单独度量后并入答案", C_FILL, 8.2)
    box(ax, 53, 16, 42, 11, "索引不持有向量：仅存行标识与主键（16 B/行）\n需要距离时向存储层索取", C_FILL, 8.2)
    arrow(ax, (40, 30), (26, 27), "并入")
    arrow(ax, (60, 30), (74, 27), "读取")

    box(ax, 5, 4, 90, 8.5, "结果：Recall@10 有过滤 / 无过滤 = 1.0（由精确剪枝保证，非调参所得）", C_ACC, 9, bold=True)

    caption(fig, "图 5  向量检索执行流程")
    save(fig, "fig-5-vector-search.png")


# ---------------------------------------------------------------- 图 6 事务与恢复
def fig6():
    fig, ax = canvas(8.00, 4.07)
    group(ax, 3, 50, 94, 46, "正常运行")
    box(ax, 7, 60, 18, 28, "BEGIN\n\n事务缓冲区\n（有序日志）", C_FILL, 8.5)
    box(ax, 29, 60, 21, 28, "语句执行\n\n日志记录暂存\n失败只撤销本语句", C_FILL, 8.5)
    box(ax, 54, 60, 21, 28, "COMMIT\n\n先写数据记录\n再写提交标记", C_ACC, 8.5, bold=True)
    box(ax, 79, 60, 18, 28, "刷盘\n\n数据文件 + WAL", C_FILL, 8.5)
    arrow(ax, (25, 74), (29, 74), "")
    arrow(ax, (50, 74), (54, 74), "")
    arrow(ax, (75, 74), (79, 74), "")

    group(ax, 3, 4, 94, 41, "崩溃与恢复")
    box(ax, 7, 12, 18, 24, "进程被\n强制终止\nSIGKILL", C_HOT, 9)
    box(ax, 29, 12, 23, 24, "按事务分组重放 WAL\n仅重放含提交标记的组\n（未确认事务必须丢弃）", C_FILL, 8.4)
    box(ax, 56, 12, 21, 24, "幂等：目录项 version\n判断记录是否已应用\n→ 重复恢复结果一致", C_ACC, 8.4)
    box(ax, 81, 12, 15, 24, "截断 WAL\n状态收敛", C_FILL, 8.4)
    arrow(ax, (25, 24), (29, 24), "")
    arrow(ax, (52, 24), (56, 24), "")
    arrow(ax, (77, 24), (81, 24), "")
    arrow(ax, (88, 60), (16, 36), "崩溃", lx=42, ly=49, ha="center")

    caption(fig, "图 6  事务、日志与崩溃恢复流程")
    save(fig, "fig-6-transaction-recovery.png")


# ---------------------------------------------------------------- 图 7 性能对比
def fig7():
    panels = [
        ("查询耗时（ms）", 1360.1, 900.6, "1.51×", "{:,.1f}"),
        ("查询 I/O（MB）", 7.379, 1.611, "4.58×", "{:,.3f}"),
        ("查询峰值 RSS（KB）", 14732, 14988, "1.02×", "{:,.0f}"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(8.0, 3.06))
    for ax, (title, before, after, ratio, fmt) in zip(axes, panels):
        bars = ax.bar([0, 1], [before, after], 0.52,
                      color=["#c9d6e5", "#4a7fb5"])
        for r, v in zip(bars, (before, after)):
            ax.text(r.get_x() + r.get_width() / 2, v * 1.04, fmt.format(v),
                    ha="center", va="bottom", fontsize=F(9))
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["基线\nb88e0209", "优化后\n当前 HEAD"], fontsize=F(8.5))
        ax.set_title(title, fontsize=F(10))
        ax.set_ylim(0, max(before, after) * 1.30)
        ax.grid(axis="y", linestyle=":", alpha=0.55)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.text(0.5, 0.93, ratio, transform=ax.transAxes, ha="center",
                fontsize=F(12), color="#b45309", fontweight="bold")
    fig.subplots_adjust(wspace=0.32, top=0.86, bottom=0.20)
    caption(fig, "图 7  优化前后性能对比（10 000 行 × 128 维 × 1000 次 TopK 查询，取三轮中位数）")
    save(fig, "fig-7-perf-compare.png")


if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6(); fig7()
    print("all figures written to", os.path.normpath(OUT))

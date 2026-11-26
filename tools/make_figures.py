#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成作品设计文档所需的全部框图。

用法: python tools/make_figures.py
输出: docs/figures/fig-1..fig-8.png

图在 Word 中按 15 cm 栏宽插入；画布宽 8 in，故把画布内字号统一放大 1.15 倍，
最终落在纸面上约 7.6 pt，可读。
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

FONT_SCALE = 1.15


def F(x):
    return round(x * FONT_SCALE, 1)


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.canvas.draw()          # 先渲染一次，取得可用于文字测量的 renderer
    return fig, ax


BOXES = []
MIN_PT = 6.5          # 画布内字号的可用下限（对应纸面约 4.8 pt）


def _fit_text(ax, t, x, y, w, h, fs, renderer, pad=0.12):
    """按渲染后的文字包围盒自动缩字号，直到文字完全落在框内。

    缩到 MIN_PT 仍放不下的，交给版式调整处理，并在溢出报告里点名。
    """
    inv = ax.transData.inverted()
    size = F(fs)
    t.set_fontsize(size)
    for _ in range(24):
        bb = t.get_window_extent(renderer=renderer)
        (x0, y0) = inv.transform((bb.x0, bb.y0))
        (x1, y1) = inv.transform((bb.x1, bb.y1))
        if x0 >= x - pad and x1 <= x + w + pad and y0 >= y - pad and y1 <= y + h + pad:
            return size, True
        cw, ch = max(x1 - x0, 1e-6), max(y1 - y0, 1e-6)
        scale = min((w + 2 * pad) / cw, (h + 2 * pad) / ch) * 0.98
        nxt = size * scale
        if nxt <= MIN_PT:
            t.set_fontsize(max(MIN_PT, nxt))
            return max(MIN_PT, nxt), False
        size = nxt
        t.set_fontsize(size)
    return size, False


def box(ax, x, y, w, h, text, fill=C_FILL, fs=9, bold=False, ls="-", ec=C_LINE):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.3,rounding_size=1.0",
        linewidth=1.1, edgecolor=ec, facecolor=fill, linestyle=ls))
    t = ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=F(fs), fontweight="bold" if bold else "normal",
                color=C_LINE, linespacing=1.6)
    renderer = ax.figure.canvas.get_renderer()
    size, fitted = _fit_text(ax, t, x, y, w, h, fs, renderer)
    BOXES.append((ax, x, y, w, h, text, fs, t, fitted))
    return t


def check_overflow(fig, name, tol=0.15):
    """检测文字是否溢出所在框体：比较渲染后的文字包围盒与框体矩形。"""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bad = []
    for ax, x, y, w, h, text, fs, t, fitted in BOXES:
        bb = t.get_window_extent(renderer=renderer)
        inv = ax.transData.inverted()
        (x0, y0) = inv.transform((bb.x0, bb.y0))
        (x1, y1) = inv.transform((bb.x1, bb.y1))
        over = []
        if x0 < x - tol:
            over.append("左溢 %.2f" % (x - x0))
        if x1 > x + w + tol:
            over.append("右溢 %.2f" % (x1 - x - w))
        if y0 < y - tol:
            over.append("下溢 %.2f" % (y - y0))
        if y1 > y + h + tol:
            over.append("上溢 %.2f" % (y1 - y - h))
        if over:
            label = text.replace(chr(10), " / ")
            bad.append((label[:34], ", ".join(over),
                        "框 %.1f×%.1f  文字 %.1f×%.1f  已缩字" % (w, h, x1 - x0, y1 - y0)
                        if fitted else
                        "框 %.1f×%.1f  文字 %.1f×%.1f  未解决" % (w, h, x1 - x0, y1 - y0)))
    if bad:
        print("  [%s] 文字溢出 %d 处:" % (name, len(bad)))
        for t_, o, d in bad:
            print("     · %-34s %s  (%s)" % (t_, o, d))
    else:
        print("  [%s] 无溢出" % name)
    BOXES.clear()
    return bad


def group(ax, x, y, w, h, label):
    ax.add_patch(Rectangle((x, y), w, h, linewidth=0.9, edgecolor=C_DIM,
                           facecolor="#ffffff", linestyle=(0, (5, 3)), zorder=-1))
    ax.text(x + 1.0, y + h - 1.2, label, ha="left", va="top",
            fontsize=F(8.5), color=C_DIM, fontweight="bold")


ROUTES = {
    "hv": "angle,angleA=90,angleB=0,rad=6",
    "vh": "angle,angleA=0,angleB=90,rad=6",
}


def arrow(ax, p1, p2, label=None, lx=None, ly=None, fs=8, color=C_LINE,
          rad=0.0, ha="center", route=None):
    """连接线。

    route=None 画直线（仅用于两点同轴的情况）；
    route="hv" 先竖后横、"vh" 先横后竖，正交折线带圆角。
    标签一律带不透明遮罩，避免压在线条上。
    """
    cs = ROUTES[route] if route else "arc3,rad=%g" % rad
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=10,
                                 linewidth=1.0, color=color,
                                 connectionstyle=cs,
                                 shrinkA=0, shrinkB=0))
    if label:
        if lx is None:
            lx = (p1[0] + p2[0]) / 2
        if ly is None:
            ly = (p1[1] + p2[1]) / 2
        ax.text(lx, ly, label, ha=ha, va="center", fontsize=F(fs), color=C_LINE,
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none"))


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
    fig, ax = canvas(8.00, 5.90)
    group(ax, 3, 84, 94, 15, "应用层")
    box(ax, 12, 86.5, 24, 8.5, "企业知识库 RAG 检索\n（文档入库 / 召回 / 重排）", C_ACC, 8.5)
    box(ax, 42, 86.5, 24, 8.5, "AI Agent 长期记忆\n（会话语义检索）", C_FILL, 8.5)
    box(ax, 71, 86.5, 24, 8.5, "判题驱动 / 压测客户端\n（JSON Lines）", C_FILL, 8.5)

    group(ax, 3, 66, 94, 14, "接口层")
    box(ax, 12, 68, 39, 9.0, "SQL 词法与语法分析\nsql/lexer.rs　sql/parser.rs", C_FILL, 8.2)
    box(ax, 57, 68, 38, 9.0, "协议层：JSON Lines\nproto/json.rs　proto/session.rs", C_FILL, 8.2)

    group(ax, 3, 42, 94, 20, "引擎层")
    box(ax, 12, 52, 26, 9.0, "通用执行器（流式投影）\nexec/query.rs", C_FILL, 8.2)
    box(ax, 41, 52, 26, 9.0, "向量检索\nexact.rs　ann.rs", C_ACC, 8.6, bold=True)
    box(ax, 70, 52, 25, 9.0, "事务缓冲与语句级撤销\nengine.rs", C_FILL, 8.2)
    box(ax, 20, 44, 68, 6.5, "TopK 堆　过滤下推　距离内核（AVX2）", "#f7f9fb", 8.5)

    group(ax, 3, 15, 94, 21, "存储层")
    box(ax, 12, 18.5, 26, 13.5, "块缓存缓冲池\nbufferpool.rs\n三类缓存共享预算", C_FILL, 8.2)
    box(ax, 41, 18.5, 26, 13.5,
        "列式存储 + IVF 倒排索引\ntable.rs　format.rs\nmeta.dat　col.dat　vec.dat\n索引驻留内存，启动时重建",
        C_ACC, 7.8, bold=True)
    box(ax, 70, 18.5, 25, 13.5, "预写日志 WAL\nwal.rs\n完整行镜像\n提交标记分组重放", C_FILL, 7.8)

    group(ax, 3, 3, 94, 9, "持久层")
    box(ax, 20, 4.2, 60, 5.6, "文件系统　/data　（单进程单客户端，容器化部署）", "#f3f4f6", 8.8)

    arrow(ax, (19, 86.5), (19, 77), "SQL", lx=14.5, ly=82)
    arrow(ax, (54, 86.5), (54, 77), "SQL", lx=49.5, ly=82)
    arrow(ax, (83, 86.5), (83, 77), "JSONL", lx=88, ly=82)
    arrow(ax, (30, 68), (30, 61), "DML", lx=25.5, ly=64)
    arrow(ax, (70, 68), (70, 64), "")
    arrow(ax, (70, 64), (54, 64), "请求", lx=62, ly=64)
    arrow(ax, (54, 64), (54, 61), "")
    arrow(ax, (24, 44), (24, 32), "读块", lx=16.5, ly=38)
    arrow(ax, (54, 44), (54, 32), "")
    arrow(ax, (82, 44), (82, 32), "WAL 追加", lx=89, ly=38)
    arrow(ax, (54, 18.5), (54, 9.8), "刷盘", lx=60, ly=14)

    check_overflow(fig, "fig-1")
    caption(fig, "图 2  RAGStore 系统总体架构")
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
    arrow(ax, (50, 59), (50, 52), "")
    arrow(ax, (50, 52), (38, 52), "落盘", lx=44, ly=52)
    arrow(ax, (38, 52), (38, 42), "")
    arrow(ax, (56, 21), (56, 14), "")

    check_overflow(fig, "fig-2")
    caption(fig, "图 3  部署拓扑与持久化路径")
    save(fig, "fig-2-deployment.png")


# ---------------------------------------------------------------- 图 3 存储格式
def fig3():
    fig, ax = canvas(8.00, 7.60)
    group(ax, 2, 79, 96, 19, "行目录 meta.dat（每行 48 字节定长记录）")
    fields = [("pk", "i64"), ("col_off", "u64"), ("col_len", "u32"), ("vec_blk", "u32"),
              ("vec_slot", "u32"), ("version", "u32"), ("alive", "u8")]
    x = 2.6
    for name, ty in fields:
        box(ax, x, 88.0, 11.5, 6.4, "%s\n%s" % (name, ty), C_FILL, 8.2)
        x += 13.4
    ax.text(50, 85.0, "+ 11 字节填充　（示意图，宽度不按字节比例）",
            ha="center", fontsize=F(7.6), color=C_DIM)
    ax.text(50, 82.0, "定长记录 → 同一数据块的条目在文件中连续；一次系统调用即可读完整个块的行目录",
            ha="center", va="center", fontsize=F(8.2), color=C_LINE)

    group(ax, 2, 43, 96, 34, "标量行镜像 col.dat（带标签的变长序列）")
    box(ax, 3.4, 61.0, 12.5, 9.5, "BIGINT\n0x01\n+ 8 B", C_FILL, 7.6)
    box(ax, 17.4, 61.0, 13.0, 9.5, "VARCHAR\n0x02 + 4 B\n+ UTF-8", C_FILL, 7.6)
    box(ax, 32.0, 61.0, 14.0, 9.5, "VECTOR\n0x03 + 4 B\n+ dim×4 B", C_FILL, 7.6)
    box(ax, 3.4, 51.5, 42.5, 6.8,
        "VABOVE　0x04\n向量列在此只留 1 字节占位标记，不存向量负载", C_HOT, 8.4, bold=True)
    box(ax, 51.0, 51.5, 42.5, 6.8,
        "128 维下：含向量 533 B → 去向量 17 B\n行镜像内向量占比降约 30 倍", C_ACC, 8.4, bold=True)
    ax.text(25, 46.5, "行镜像只存标量列，向量负载只存在 vec.dat 里",
            ha="center", va="center", fontsize=F(8.4), color=C_LINE)

    group(ax, 2, 4, 96, 36, "向量文件 vec.dat 与块内行主序布局")
    box(ax, 5, 22, 15, 9, "16 B 文件头\nmagic / ver\ndim / block_rows", C_FILL, 7.8)
    box(ax, 21.5, 22, 20, 9, "块 0\nslot0：dim 个 f32 连续\nslot1：dim 个 f32 连续", C_ACC, 8)
    box(ax, 43, 22, 20, 9, "块 1\nslot0 …\n……", C_ACC, 8)
    box(ax, 64.5, 22, 14, 9, "块 b\n……", C_ACC, 8)
    ax.text(5, 18.5, "offset = 16 + ((b × block_rows) + s) × dim × 4",
            ha="left", fontsize=F(8.4), color=C_LINE)
    box(ax, 56, 5.5, 40, 11.5,
        "行主序 vs 列主序的量化论证\n"
        "转置 2 MB 块 ≈ 200 μs\n"
        "而它能并行化的 8 行仅省 ≈ 11 μs\n"
        "→ 18 倍反对，布局保持行主序",
        "#f7f9fb", 8.4, ec=C_DIM)

    check_overflow(fig, "fig-3")
    caption(fig, "图   存储格式：行目录、标量行镜像与向量文件")
    save(fig, "fig-3-storage-format.png")


# ---------------------------------------------------------------- 图 4 缓冲池
def fig4():
    fig, ax = canvas(8.00, 5.60)
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

    check_overflow(fig, "fig-4")
    caption(fig, "图 5  块缓存缓冲池：共享预算与 LRU 换出")
    save(fig, "fig-4-bufferpool.png")


# ---------------------------------------------------------------- 图 5 向量检索流程
def fig5():
    fig, ax = canvas(8.00, 6.60)
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

    box(ax, 5, 28, 90, 9,
        "TopK 堆（容量 ≤ k）：最差候选置于堆顶，新候选一次比较即可淘汰\n"
        "距离相同按主键升序破平 —— 与 SQL 的 ORDER BY 语义一致",
        "#f7f9fb", 8.5)
    arrow(ax, (26, 43), (26, 37), "")
    arrow(ax, (74, 43), (74, 37), "")

    box(ax, 5, 13, 42, 11, "事务内未提交行不在存储中\n→ 单独度量后并入答案", C_FILL, 8.2)
    box(ax, 53, 13, 42, 11, "索引不持有向量：仅存行标识与主键（16 B/行）\n需要距离时向存储层索取", C_FILL, 8.2)
    arrow(ax, (26, 28), (26, 24), "并入", lx=32, ly=26)
    arrow(ax, (74, 28), (74, 24), "读取", lx=80, ly=26)

    box(ax, 5, 4, 90, 8.5, "结果：Recall@10 有过滤 / 无过滤 = 1.0（由精确剪枝保证，非调参所得）", C_ACC, 9, bold=True)

    check_overflow(fig, "fig-5")
    caption(fig, "图   向量检索执行流程")
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
    box(ax, 56, 12, 21, 24, "幂等：按行标识判重跳过\n→ 重复恢复结果一致", C_ACC, 8.4)
    box(ax, 81, 12, 15, 24, "截断 WAL\n状态收敛", C_FILL, 8.4)
    arrow(ax, (25, 24), (29, 24), "")
    arrow(ax, (52, 24), (56, 24), "")
    arrow(ax, (77, 24), (81, 24), "")
    arrow(ax, (88, 60), (88, 48), "")
    arrow(ax, (88, 48), (16, 48), "崩溃", lx=52, ly=48)
    arrow(ax, (16, 48), (16, 36), "")

    check_overflow(fig, "fig-6")
    caption(fig, "图   事务、日志与崩溃恢复流程")
    save(fig, "fig-6-transaction-recovery.png")


# ---------------------------------------------------------------- 图 7 性能对比
def fig7():
    """图 9：优化前后性能对比。左为分组柱状图（查询耗时），右为横向条形图（各维度倍数）。"""
    base_c, cur_c = "#c9d6e5", "#4a7fb5"
    fig = plt.figure(figsize=(8.0, 3.40))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1.0], wspace=0.46)
    ax = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    groups = [("精确检索 exact", 948.9, 428.8, "2.21×"),
              ("近似检索 ann", 2773.5, 428.3, "6.48×")]
    w = 0.28
    for i, (name, b, c, ratio) in enumerate(groups):
        x = float(i)
        ax.bar(x - w / 2, b, w, color=base_c, edgecolor="#8fa8c4", linewidth=0.6)
        ax.bar(x + w / 2, c, w, color=cur_c)
        ax.text(x - w / 2, b * 1.03, "{:,.1f}".format(b), ha="center",
                va="bottom", fontsize=8.8)
        ax.text(x + w / 2, c * 1.03, "{:,.1f}".format(c), ha="center",
                va="bottom", fontsize=8.8)
        ax.text(x + w / 2, c * 1.16, ratio, ha="center", va="bottom",
                fontsize=12, color="#b45309", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none"))
    ax.set_xticks([0, 1])
    ax.set_xticklabels([g[0] for g in groups], fontsize=9)
    ax.set_ylabel("查询耗时（ms）", fontsize=9.5)
    ax.set_title("查询耗时：同协议交错测量，5 轮中位数", fontsize=10)
    ax.set_ylim(0, 3350)
    ax.grid(axis="y", linestyle=":", alpha=0.55)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.bar(0, 0, color=base_c, edgecolor="#8fa8c4", linewidth=0.6, label="对照版本")
    ax.bar(0, 0, color=cur_c, label="本作品版本")
    ax.legend(fontsize=8.2, frameon=False, loc="upper left")
    ax.text(0.5, -0.235, "查询阶段 I/O：两个版本均为 0 B（全部命中页缓存）",
            transform=ax.transAxes, ha="center", va="top", fontsize=8.4, color=C_DIM)

    items = [("查询峰值 RSS", 1.08), ("写入耗时", 1.36), ("精确检索耗时", 2.21),
             ("索引构建耗时", 2.28), ("近似检索耗时", 6.48)]
    ys = list(range(len(items)))
    colors = ["#4a7fb5" if v >= 2 else "#7ba3cc" for _, v in items]
    ax2.barh(ys, [v for _, v in items], 0.56, color=colors)
    for y, (lab, v) in zip(ys, items):
        ax2.text(v + 0.14, y, "%.2f×" % v, va="center", ha="left", fontsize=8.8)
    ax2.set_yticks(ys)
    ax2.set_yticklabels([l for l, _ in items], fontsize=8.8)
    ax2.set_xlim(0, 7.6)
    ax2.set_xlabel("相对对照版本的倍数（>1 表示本作品更优）", fontsize=8.8)
    ax2.set_title("各维度相对对照版本的提升", fontsize=10)
    ax2.axvline(1.0, color="#b45309", linestyle="--", linewidth=0.9, alpha=0.8)
    ax2.set_ylim(-1.0, 4.6)
    ax2.text(1.06, -0.72, "对照版本 1.0×", fontsize=8, color="#b45309",
             ha="left", va="center")
    ax2.grid(axis="x", linestyle=":", alpha=0.5)
    ax2.set_axisbelow(True)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)
    ax2.text(0.5, -0.235, "RSS 越低越好，1.08× 即降为对照版本的 1/1.08",
             transform=ax2.transAxes, ha="center", va="top", fontsize=8.4, color=C_DIM)

    fig.subplots_adjust(left=0.09, right=0.985, top=0.88, bottom=0.24)
    caption(fig, "图 7  优化前后性能对比")
    save(fig, "fig-7-perf-compare.png")


# ---------------------------------------------------------------- 图 8 RAG 两阶段工作流
def fig8():
    fig, ax = canvas(8.00, 4.70)
    group(ax, 3, 58, 94, 39, "离线索引阶段")
    box(ax, 6, 67, 20, 13, "文档加载", C_FILL, 8.5)
    box(ax, 29, 67, 20, 13, "切割\nChunking", C_FILL, 8.5)
    box(ax, 52, 67, 20, 13, "向量化\nEmbedding", C_FILL, 8.5)
    box(ax, 75, 67, 20, 13, "写入向量存储\nRAGStore", C_ACC, 8.5, bold=True)
    arrow(ax, (26, 73.5), (29, 73.5), "")
    arrow(ax, (49, 73.5), (52, 73.5), "")
    arrow(ax, (72, 73.5), (75, 73.5), "")

    group(ax, 3, 4, 94, 45, "在线查询阶段")
    box(ax, 4, 12, 17, 13, "问题向量化", C_FILL, 8.2)
    box(ax, 24, 12, 17, 13, "向量召回\nRAGStore", C_ACC, 8.2, bold=True)
    box(ax, 44, 12, 17, 13, "重排\nCross-Encoder", C_FILL, 8.2)
    box(ax, 64, 12, 15, 13, "提示构造", C_FILL, 8.2)
    box(ax, 82, 12, 15, 13, "生成回答", C_FILL, 8.2)
    arrow(ax, (21, 18.5), (24, 18.5), "")
    arrow(ax, (41, 18.5), (44, 18.5), "")
    arrow(ax, (61, 18.5), (64, 18.5), "")
    arrow(ax, (79, 18.5), (82, 18.5), "")

    arrow(ax, (85, 67), (85, 54), "")
    arrow(ax, (85, 54), (32, 54), "索引建立", lx=58, ly=54)
    arrow(ax, (32, 54), (32, 25), "")

    ax.text(66, 39.5,
            "召回率由构造保证：向量通道不引入漏召回\n重排的输入质量上限因而确定",
            ha="center", va="center", fontsize=F(8.2), color=C_LINE,
            linespacing=1.5,
            bbox=dict(boxstyle="round,pad=0.4", fc="#f7f9fb", ec=C_DIM, linewidth=0.8))

    check_overflow(fig, "fig-8")
    caption(fig, "图   检索增强生成的两阶段工作流与本作品的位置")
    save(fig, "fig-8-rag-workflow.png")


# ---------------------------------------------------------------- 图 9 硬件框图
def fig9():
    fig, ax = canvas(8.00, 5.40)
    group(ax, 2, 62, 96, 34, "宿主机（20 核 / 125 GB 内存 / 本地块设备）")
    box(ax, 6, 66, 40, 24,
        "CPU 核 0\n"
        "─────────────\n"
        "服务进程（1 核）\n"
        "· AVX2 L2 距离内核\n"
        "· 缓冲池 64 MB\n"
        "· TopK 堆与排序", C_ACC, 8)
    box(ax, 52, 66, 42, 24,
        "CPU 核 3\n"
        "─────────────\n"
        "驱动与压测客户端（1 核）\n"
        "· 构造查询并发送\n"
        "· 读取应答", C_FILL, 8)

    group(ax, 2, 30, 96, 27, "宿主机内存")
    box(ax, 6, 34, 40, 18,
        "进程堆\n"
        "─────────────\n"
        "解码后的 f32 向量矩阵\n"
        "解码后的行目录与标量列\n"
        "（缓冲池预算内）", C_FILL, 8)
    box(ax, 52, 34, 42, 18,
        "操作系统页缓存\n"
        "─────────────\n"
        "数据目录 10.86 MiB\n"
        "（计入 cgroup 峰值内存）", C_FILL, 8)

    group(ax, 2, 2, 96, 23, "宿主机块设备")
    box(ax, 6, 6, 88, 13,
        "wal.dat（预写日志）　col.dat（标量行镜像）　vec.dat（向量列）　meta.dat（行目录）\n"
        "数据经容器可写层 /data 映射至此；查询阶段全部命中页缓存，不产生块设备读", C_FILL, 8.2)

    arrow(ax, (26, 66), (26, 54), "读块", lx=20, ly=60)
    arrow(ax, (73, 66), (73, 54), "读块", lx=68, ly=60)
    arrow(ax, (26, 34), (26, 21), "刷盘", lx=33, ly=27.5)
    arrow(ax, (46, 73), (52, 73), "JSONL", lx=49, ly=77)

    caption(fig, "硬件框图与 I/O 通路")
    check_overflow(fig, "fig-9")
    save(fig, "fig-9-hardware.png")

# ---------------------------------------------------------------- 图 11 逐轮交错测量
def fig11():
    base_exact = [940.6, 945.7, 957.8, 948.9, 952.0]
    cur_exact = [426.8, 428.8, 438.3, 429.1, 428.8]
    base_ann = [2773.5, 2816.2, 2764.0, 2828.0, 2760.9]
    cur_ann = [427.6, 428.3, 441.7, 426.4, 429.6]
    rounds = [1, 2, 3, 4, 5]

    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.30))
    panels = [("精确检索 exact", base_exact, cur_exact, "2.21×"),
              ("近似检索 ann", base_ann, cur_ann, "6.48×")]
    for ax, (title, b, c, ratio) in zip(axes, panels):
        ax.plot(rounds, b, "-o", color="#9db3cc", linewidth=1.6, markersize=4.5,
                label="对照版本")
        ax.plot(rounds, c, "-o", color="#3a6ea5", linewidth=1.6, markersize=4.5,
                label="本作品版本")
        for series, color in ((b, "#9db3cc"), (c, "#3a6ea5")):
            m = sum(series) / len(series)
            ax.axhline(m, color=color, linestyle="--", linewidth=0.9, alpha=0.75)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("轮次", fontsize=9)
        ax.set_ylabel("查询耗时（ms）", fontsize=9)
        ax.set_xticks(rounds)
        ax.grid(axis="y", linestyle=":", alpha=0.5)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        mid = (sum(b) / len(b) + sum(c) / len(c)) / 2
        ax.text(3, mid, "中位数之比 " + ratio, ha="center", va="center",
                fontsize=10.5, color="#b45309", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none"))
        ax.legend(fontsize=8, frameon=False, loc="lower left")
    fig.subplots_adjust(wspace=0.28, top=0.86, bottom=0.22)
    caption(fig, "图 11  逐轮交错测量：两版本在同协议下交替测量")
    save(fig, "fig-11-round-by-round.png")


if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6(); fig7(); fig8(); fig9(); fig11()

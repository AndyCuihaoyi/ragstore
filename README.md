# RAGStore · 第四届大学生信息存储技术竞赛（自由赛道）

> 承办：华中科技大学 ｜ 赞助：华为技术有限公司
> 提交截止：**2026-12-02** ｜ 奖金池：**¥290,000**

作品名称：**RAGStore：面向检索增强生成的轻量级向量存储引擎**

本仓库承载参赛作品《RAGStore》的设计文档、测试报告、源码与演示材料。

## 快速信息

| 项目 | 内容 |
| --- | --- |
| 赛事名称 | 第四届大学生信息存储技术竞赛 · 自由赛 |
| 赛道 | 自由赛道（Free track） |
| 承办单位 | 华中科技大学 |
| 赞助单位 | 华为技术有限公司 |
| 报名状态 | 已报名 |
| 当前规模 | 46 支团队 / 147 名参赛人数 |
| 奖金池 | ¥290,000 |
| 提交截止 | 2026-12-02（截至 2026-11-26 剩 6 天） |
| 压缩包命名 | `Freetrack-<华为云账号>.zip` |
| 压缩包大小 | < 500 MB（当前包 2.85 MB） |
| 上传次数 | ≤ 10 次，以最后一次提交为准 |
| 初赛晋级 | 网络评审 → 16 强进入决赛 |
| 源码仓库 | https://github.com/AndyCuihaoyi/ragstore |
| 服务器工作区 | `chyLap` (10.144.0.111) 的 `~/StorageContest` |

## 作品指标

| 指标 | 数值 | 口径 |
| --- | --- | --- |
| 源代码 | 13 771 行 / 32 个源文件 | Rust 2021，编译期外部依赖为 0 |
| 测试 | 143 单测 + 15 协议测试全绿 | `cargo test --release --offline --locked` |
| 召回率 | Recall@10 = 1.000（有过滤与无过滤） | 与暴力检索答案逐字节比对 |
| 查询耗时 | 900.6 ms / 1000 次 TopK | 三轮中位数，绑核单核 |
| 查询 I/O | 1.611 MB（较基线降低 4.58 倍） | cgroup v2 `io.stat` |
| 峰值内存 | 14 988 KB | cgroup v2 `memory.peak` |
| 崩溃恢复 | 12 轮 SIGKILL 幂等全绿 | 宿主与容器内各 12 轮 |
| 官方判题器 | 20 / 20 PASS | `protocol_check/run.py` 对真实镜像 |

## 文档索引

| 文档 | 用途 |
| --- | --- |
| [赛事要求](./docs/赛事要求.md) | 赛题范围、提交物清单、评审规则、提交规范的完整口径 |
| [候选作品评估](./docs/候选作品评估.md) | 远端现有赛题仓库的盘点与三个候选方向的评分对照 |
| [文档模板结构](./docs/文档模板结构.md) | 官方两个 docx 模板的章节结构、排版参数与填写要点 |
| [提交检查清单](./docs/提交检查清单.md) | 打包前逐项勾选的自查表 |

## 仓库目录结构

```
MassiveStorege/
├── README.md                    # 本文件：项目索引与关键信息
├── 作品设计文档.docx              # 按官方模板撰写的四章正文 + 参考文献
├── 作品原创性声明.docx            # 需组员手写签名后替换
├── docs/
│   ├── 赛事要求.md              # 赛题详情 / 评审规则 / 提交要求
│   ├── 候选作品评估.md          # 现有仓库盘点 + 三个候选方向对照
│   ├── 文档模板结构.md          # 模板章节 / 排版参数 / 填写要点
│   ├── 提交检查清单.md          # 提交前自查
│   └── figures/                 # 设计文档用框图（PNG，由 tools/make_figures.py 生成）
├── source/                      # 作品源码（= GitHub 仓库内容）
│   ├── ragstore/                # Rust crate，零外部依赖
│   ├── Dockerfile
│   ├── docs/design.md, docs/perf/
│   ├── tools/                   # 测试与性能测量脚本
│   └── development-record/      # 开发过程存档（保留赛题阶段命名原样）
├── templates/                   # 官方模板原件（复制后填写，原件勿改）
│   ├── 作品设计文档模板.docx
│   └── 作品原创性声明.docx
├── tools/                       # 文档与打包生成脚本
└── scripts/
    └── check_submission.py      # 提交包合规校验（命名/体积/完整性/编码）
```

## 生成与打包

```bash
python tools/make_figures.py       # 生成框图
python tools/build_design_doc.py   # 生成《作品设计文档.docx》
python tools/fill_statement.py     # 生成《作品原创性声明.docx》
python tools/package.py <华为云账号>  # 组装 Freetrack-<账号>.zip

python scripts/check_submission.py Freetrack-<账号>.zip \
  --naming '^Freetrack-.+\.zip$' --max-size-mb 500 \
  --require 作品设计文档.docx --require 作品原创性声明.docx
```

## 待办

- [x] 从赛事页面底部下载官方模板 → `templates/`
- [x] 作品重命名并与存储竞赛叙事对齐（RAGStore）
- [x] 源码重命名与重组，构建通过、158 项测试全绿、工具链验证通过
- [x] 在 `chyLap` 建立 `~/StorageContest` 工作区并推送 GitHub 仓库
- [x] 撰写《作品设计文档》四章正文与参考文献
- [x] 补充 RAG 章节与两阶段工作流图示（图 1）
- [ ] 组员手写签名《作品原创性声明》并填日期
- [ ] 核对官方《参赛指南》原文，确认与 OceanBase 大赛同期参赛是否存在限制
- [ ] 用真实华为云账号重新打包（当前为占位账号）
- [ ] 整包压缩并控制在 500 MB 以内，上传后重新下载校验

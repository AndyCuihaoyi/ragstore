# 开发过程存档

本目录保存本作品在开发阶段的原始记录，用于佐证开发过程的真实性与连续性。
**它不参与构建与评测**：`cargo build`、`cargo test` 与各测试脚本都不会读取本目录。

## 为什么保留原始命名

本作品的核心代码库此前用于另一项赛事——第六届 OceanBase 数据库大赛（2026）——
的加赛题目，在那次赛事中项目名为 `minivectordb`，环境变量前缀为 `MINIVECDB`。
为保证本目录中的记录不被事后修饰造成的歧义，本目录内的一切内容
（对话记录、归档快照、生成脚本）**逐字保留当时的命名**，未作任何重命名或改写。

正文的《作品设计文档》第四章已就这一关系作出说明：本次参赛的改动限于
crate 与二进制改名、设计文档的章节重组，以及删除与彼次赛题绑定的功能与脚本；
核心存储格式、IVF 索引、事务与恢复逻辑未作改动。

## 目录内容

| 路径 | 说明 |
| --- | --- |
| `conversation.json` | 开发过程的完整对话记录（JSON） |
| `agent/archive/conversation-v*.json` | 历次归档快照，用于比对记录是否被截断或篡改 |
| `agent/archive/unscored-instances.json` | 未计分的评测实例快照 |
| `agent/DIAGNOSIS-agent-prompt.md` | 诊断阶段使用的提示词原文 |
| `tools/build_conversation_json.py` | 由归档生成 `conversation.json` 的脚本 |
| `tools/check_conversation_against_record.py` | 校验 `conversation.json` 与归档是否逐条一致 |

## 如何校验

```bash
python3 tools/check_conversation_against_record.py
```

该脚本把 `conversation.json` 与 `agent/archive/` 中的归档逐条比对，
用于确认存档未被改写。生成与校验脚本均按原样保留，以维持记录的可复现性。

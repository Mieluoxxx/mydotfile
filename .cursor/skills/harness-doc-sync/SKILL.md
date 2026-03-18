---
name: harness-doc-sync
description: 用户明确要求更新 Harness 文档，或在完成 AI Coding 改动后，自动同步全局 Harness 文档与根级工程入口（AGENTS.md、ARCHITECTURE.md、TODO.md）。
---

# Harness Doc Sync

在代码改动完成后使用本技能，目标不是“只记流水”，而是同时修正文档系统本身，避免工程约束与代码状态漂移。

## 何时触发

当用户表达以下意图时触发：

- “更新/同步/维护 Harness 文档”
- “AI Coding 结束后自动记录改造”
- “补齐全局规则与任务记录”
- “同步更新 AGENTS/ARCHITECTURE/TODO”

## 输入约定

执行前先确认以下输入（至少 task）：

- `task`：本次改造主题（必填）
- `intent`：目标（可选，默认与 task 相同）
- `constraints`：边界约束（可选）
- `checks`：验证命令（可选）
- `dod`：完成定义（可选）
- `rollback`：回退策略（可选）

## 标准流程

1. 读取并理解当前改动（`git status --short`）。
2. 先用 `date` 获取当前时间戳（必须）：

```bash
date +"%Y%m%d-%H%M%S"
```

3. 运行脚本：

```bash
python3 .agents/skills/harness-doc-sync/scripts/update_harness_log.py \
  --repo-root . \
  --task "<本次改造主题>" \
  --intent "<目标>" \
  --constraints "<约束>" \
  --checks "<验证命令>" \
  --dod "<完成定义>" \
  --rollback "<回退策略>"
```

4. 检查脚本输出文件：
   - `docs/harness/records/<YYYYMMDD-HHMMSS>-<摘要>.md`
   - `docs/README.md`
   - `AGENTS.md`
   - `ARCHITECTURE.md`
   - `TODO.md`
5. 如本次新增了长期规则，再手动补充 `docs/harness/总则.md`。
6. 在交付说明中引用新增记录文件名与更新过的根级文件。

## 规则

- `docs/harness/总则.md` 只放长期规则，不写一次性任务流水。
- `docs/harness/records/` 按“一次任务一个文件”记录 Intent/Constraints/Checks/DoD/Rollback。
- 记录文件命名必须为：`YYYYMMDD-HHMMSS-摘要.md`（示例：`20260306-094809-任务摘要.md`）。
- 每次同步按需更新根级入口：`AGENTS.md`、`ARCHITECTURE.md`、`TODO.md`。
- 若本次任务无需改动某个根级文件，脚本应保持该文件不变（幂等）。

## 快速验证

至少执行以下检查：

```bash
rg "Harness 记录目录" "docs/README.md"
rg "任务收尾提醒（Harness 同步）" "AGENTS.md"
rg "L0-L3" "ARCHITECTURE.md"
rg "Harness 文档对齐" "TODO.md"
```

## References

- OpenAI: https://openai.com/index/harness-engineering/
- Philipp Schmid: https://www.philschmid.de/agent-harness-2026
- 摘要索引：`references/harness-notes.md`
- 新增摘要：`references/agent-harness-2026-summary.md`

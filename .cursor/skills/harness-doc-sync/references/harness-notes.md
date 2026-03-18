# Harness Engineering 摘要（用于本 Skill）

来源：

- OpenAI《Harness engineering: leveraging Codex in an agent-first world》
- Philipp Schmid《The importance of Agent Harness in 2026》

参考链接：

- https://openai.com/index/harness-engineering/
- https://www.philschmid.de/agent-harness-2026

## 核心原则

1. Humans steer, agents execute：人负责目标、约束、验收，Agent 负责实现。
2. Map, not manual：AGENTS.md 应该是导航索引，而非超长手册。
3. Mechanical invariants：关键约束必须可被测试/脚本机械校验。
4. Observability for agents：日志、指标、追踪应可供 Agent 自查与回归验证。
5. Continuous garbage collection：持续清理文档漂移、重复规则、失效约束。

## 对文档更新的启发

- Harness 文档应区分“长期规则”和“任务记录”。
- 任务记录每条都应包含 Intent/Constraints/Checks/DoD/Rollback。
- 文档更新不仅是记录，还要按需对齐根级入口文档。
- 根级架构文档应保持导航属性，实现细节下沉到子项目文档。

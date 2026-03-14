## Why

当前论文自动下载有两条触发路径：
1. skill 调用触发；
2. assistant 文本提及 arXiv ID 的兜底触发。

文本兜底会引入误触发与不可控副作用（模型提及 != 用户确认下载），且难以稳定回归检测。需要切换为“仅 skill 触发自动下载”，并通过 BDD/TDD 固化行为。

## What Changes

- 关闭默认“文本提及论文 ID 即自动 ingest”的兜底逻辑。
- 将自动下载触发收敛为：仅当流事件出现 `knowledge.paper_ingest` 工具调用时触发。
- 保留可选开关：`ENABLE_PAPER_TEXT_MENTION_FALLBACK=true` 时可临时恢复文本兜底（默认关闭）。
- 增加 BDD/TDD 覆盖，确保后续自动检测回归。

## Expected Benefit

- 降低误下载与非预期写入数据库风险。
- 明确“触发边界”：skill 调用是唯一默认入口，行为可观测、可审计。
- 当链路异常时，测试可快速定位是 skill 事件缺失还是 ingest 执行失败。

## Success Metrics

1. `fallback_ingest_default_invocations = 0`（默认配置下）
2. `skill_triggered_ingest_invocation_rate = 100%`（BDD 预置 skill 事件场景）
3. `bdd_tdd_pass_rate = 100%`（新增用例必须持续通过）

## Rollback / Kill Criteria

- 若线上发现 skill 事件丢失导致 ingest 触发率 < 95%，可临时启用 `ENABLE_PAPER_TEXT_MENTION_FALLBACK=true` 回滚行为。
- 若新增 BDD/TDD 用例连续 2 次失败，阻断变更并回退到上一个稳定提交。

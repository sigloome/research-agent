## Context

`/api/chat` 在 SSE 流解析阶段可拿到 `tool-input-available` 事件。该事件包含 `toolName` 与 `input`，可用于判断是否触发 `knowledge.paper_ingest`。

## Design

1. 触发条件
- 仅解析 `type=tool-input-available` 事件。
- `toolName` 包含 `knowledge.paper_ingest` 时，读取 `input.source` 或 `input.arguments.source`。
- 收集到 source 后，在流结束阶段执行 ingest。

2. 兜底策略
- 默认不执行文本兜底 ingest。
- 仅在 `ENABLE_PAPER_TEXT_MENTION_FALLBACK=true` 时，且无 skill 触发 source 时，才执行文本兜底。

3. 执行顺序
- 先持久化 assistant 文本。
- 若有 skill source：执行 skill-triggered ingest。
- 否则在 fallback 开关开启时执行文本兜底 ingest。

4. 可测试性
- 抽离 helper：
  - `_extract_skill_ingest_source(event)`
  - `_is_text_fallback_ingest_enabled()`
- 以 BDD 覆盖端到端行为，以 TDD 覆盖 helper 解析与开关。

## Risks

- 风险：某些 runtime 的 `toolName` 命名不同导致未命中。
- 缓解：保持包含匹配（`knowledge.paper_ingest` 子串）+ BDD 流事件回归测试。

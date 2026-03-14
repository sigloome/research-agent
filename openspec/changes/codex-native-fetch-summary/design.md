## Context

- 活跃对话链路已经是 `codex_sdk` 运行时。
- `paper_ingest` 已实现“下载本地全文 + 调用 summarizer + 入库 + RAG 事件”。
- 问题在于：`fetch_papers` 不会默认触发 ingest；`summarizer` 使用外部 Anthropic token。

## Design

1. Codex-native summarizer
- 新增 `backend/codex_sdk_adapter/run_summary.mjs`，复用 `@openai/codex-sdk`。
- `generate_summary` 通过 Node 子进程调用适配器并解析 JSON。
- 复用 `backend/codex_sdk_runtime.py` 的 runtime env 构建函数，保证与主 agent 相同的配置基线。

2. fetch -> ingest default path
- `fetch_papers` 对于新论文：先入元数据，再调用 `paper_ingest`。
- 对于已存在但不完整论文：继续调用 `paper_ingest` 补齐。
- 对于已完整论文：跳过 ingest。

3. Failure handling
- Codex 摘要失败时返回结构化 fallback，避免 DB 写入破坏契约。
- ingest 失败不抛出中断 fetch 列表，但记录 warning 便于观测。

## Risks

- 风险：fetch 延迟上升。
  - 缓解：维持 `max_results<=5`，并保留后续异步化空间。
- 风险：Codex 输出非 JSON。
  - 缓解：提取 JSON 对象 + fallback summary。

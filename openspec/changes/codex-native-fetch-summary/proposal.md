## Why

当前 `fetch_papers` 仅做元数据入库和摘要截断，缺少稳定的“本地全文下载 + 结构化关键信息提取”闭环；同时 `summarizer` 仍依赖 `ANTHROPIC_AUTH_TOKEN`，与当前统一的 Codex 运行时不一致。

需要将论文总结链路切换到 Codex-native，并在 `fetch_papers` 后自动走 ingest，确保后续检索与 GraphRAG 有完整数据。

## What Changes

- 将 `skills/knowledge/summarizer/summarize.py` 从 Anthropic API 切换为 `@openai/codex-sdk` 适配器调用。
- 新增 Node 适配脚本用于结构化摘要调用（同一 Codex runtime/env）。
- 调整 `fetch_papers`：对新拉取/不完整论文自动触发 `paper_ingest`，默认补齐本地文件与关键字段。
- 新增 BDD/TDD 测试覆盖 fetch->ingest 和 Codex summarizer fallback 行为。

## Expected Benefit

- 统一模型调用栈，减少多供应商差异和密钥依赖问题。
- 提升论文数据完整率（本地路径 + methods/results/limitations）。
- 提升后续检索命中稳定性，降低“已下载但不可检索”的误报。

## Success Metrics

1. `fetch_triggered_ingest_rate >= 95%`（fetch 返回论文中自动触发 ingest 的比例）
2. `paper_key_fields_complete_rate >= 90%`（`summary_*` + `full_text_local_path`）
3. `codex_summarizer_success_rate >= 95%`（摘要调用成功率，按滚动窗口统计）

## Rollback / Kill Criteria

- 若 `codex_summarizer_success_rate < 85%` 连续两个窗口，回滚至“仅摘要截断 + 不自动 ingest”。
- 若 fetch 平均延迟较基线上涨 >50% 且持续两轮回归，禁用 fetch 后自动 ingest。
- 若新增 deterministic 测试连续 2 次失败，阻断发布并回退到上个稳定版本。

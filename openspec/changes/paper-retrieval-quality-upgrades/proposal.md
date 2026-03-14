## Why

当前项目已经完成论文检索的 foundation 能力：活跃 runtime profile、生效的结构化 retrieval context、frozen benchmark、端到端 deterministic scoring 都已经落地。但最新 `paper_core` 结果暴露出质量层面的明确瓶颈：

1. `cluster_coverage` 仍低，说明 related work 检索无法稳定覆盖 classic baseline、same-family work 和 recent follow-up。
2. `support_recall` / `contradict_recall` 仍低，说明 cross-validation 场景下对支持证据与反例的召回仍不完整。
3. `graph_verify` 当前未明显优于 `graph_expand`，说明 critic 仍停留在弱文本过滤，而没有真正作用于结构化 evidence。
4. `hybrid` profile 虽已在 runtime 中定义，但 benchmark manifest 还未纳入，且当前实现并非真实 lexical+dense hybrid recall。

foundation 阶段已经证明 benchmark 能稳定暴露问题，因此下一轮工作应集中在 retrieval quality 本身，而不是继续扩展治理壳层。

## What Changes

- 将 `hybrid` 从占位 profile 升级为真实论文检索层：lexical recall + semantic/dense recall + 合并重排。
- 扩展 `graph_expand` 为 cluster-aware retrieval：显式覆盖 classic baseline、same method family、recent follow-up 三类 related-work cluster。
- 重构 `graph_verify` 为 evidence-item rerank：critic 直接作用于结构化 evidence，而不是自由文本 chunk。
- 为 cross-validation 增加反例优先检索策略，显式提高 `contradict` 证据召回。
- 将 benchmark manifest 与 runner 补齐到 profile parity，至少纳入 `hybrid`，并在 `paper_core` 上对 quality uplift 做可比验证。

## Expected Benefit

- 提升论文 related-work 检索完整性，而不是只提升字段填充率。
- 提升 cross-validation 场景对 support / contradict 两侧证据的平衡召回。
- 让 `graph_verify` 对结果质量有实质增益，而不是仅保留结构占位。
- 让 runtime profile 阶梯真正可比：`baseline -> hybrid -> graph_expand -> graph_verify`。

## Impact

- 受影响目录：
  - `backend/`
  - `evals/metrics/`
  - `evals/runners/`
  - `evals/datasets/`
  - `tests/backend/`
  - `tests/evals/`
- 不扩展 frozen dataset 规模；仍保持当前低成本 benchmark 基线。

## Success Metrics

1. `paper_core` 上 `hybrid.paper_recall > baseline.paper_recall`。
2. `paper_core` 上 `graph_expand.cluster_coverage >= 0.60`。
3. `paper_core` 上 `graph_verify.support_recall >= 0.50`。
4. `paper_core` 上 `graph_verify.contradict_recall >= 0.50`。
5. `paper_core` 上 `graph_verify.balanced_evidence_rate >= 0.50`。
6. `graph_verify` 相比 `graph_expand` 的 `mean_total_tokens` 增长不超过 `25%`。
7. 新增 deterministic tests 与现有 retrieval suites 持续通过。

## Risk Metrics

1. `hybrid.paper_recall <= baseline.paper_recall` on repeated frozen `paper_core` runs.
2. `graph_verify` fails to exceed or match `graph_expand` on support/contradict recall.
3. `graph_verify.mean_total_tokens` grows by more than `25%` over `graph_expand`.
4. deterministic regressions appear in existing retrieval suites.

## Kill Criteria

- 若 `hybrid` 未能稳定优于 `baseline`，暂停默认推广，仅保留实验 profile。
- 若 `graph_verify` 在 `paper_core` 上连续两轮仍不优于 `graph_expand`，回退到 `graph_expand` 作为默认高阶 profile。
- 若质量提升依赖扩大 benchmark 样本数或放松 frozen contract，则停止该方向，保持当前 benchmark 治理不变。

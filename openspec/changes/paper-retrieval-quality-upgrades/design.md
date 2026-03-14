## Context

- foundation change 已完成 runtime profile 接线、结构化 retrieval context、frozen dataset/snapshot、端到端 deterministic scoring。
- 最新 `paper_core` 对比结果表明：
  - `baseline.paper_recall = 0.75`
  - `graph_expand.paper_recall = 0.8333`
  - `graph_expand.cluster_coverage = 0.3333`
  - `graph_verify` 与 `graph_expand` 基本持平
- 当前问题不是 benchmark 缺失，而是 runtime retrieval 质量不足。
- local execution evidence and diagnostics continue to live under `tmp/runs/evolution/` and `tmp/runs/evolution/index.md` when not promoted into tracked artifacts.

## Goals

1. 让 `hybrid` 成为真正的 retrieval layer，而不是 baseline 的轻包装。
2. 让 `graph_expand` 显式补 related-work cluster 覆盖。
3. 让 `graph_verify` 直接对结构化 evidence 做 rerank/verification。
4. 让 cross-validation 检索主动寻找反例，而不是仅被动等待 contradict 命中。
5. 保持 benchmark 冻结规模不变，仅提升同一数据上的质量分数。

## Non-Goals

1. 本 change 不做全量 citation graph 或 claim graph 存储层重构。
2. 不扩增 frozen dataset 样本规模。
3. 不引入 blocking 运行时 LLM judge。
4. 不修改 foundation change 已定下的 benchmark governance 合同。

## Design

### 1. Real hybrid retrieval

`hybrid` 必须由三段组成：

1. lexical recall
   - title
   - abstract
   - summary_main_ideas
   - summary_methods/results/limitations
2. semantic recall
   - 先使用现有摘要字段的轻量语义匹配
   - 第一版允许使用本地可计算 embedding 或 deterministic token-overlap proxy，但接口必须保持 dense-ready
3. fusion + dedup
   - RRF 或固定规则合并
   - 输出统一 `candidate_papers`

要求：`hybrid` 不再只是给 candidate 添加 `semantic_match` 标签，而要显式记录候选来自 lexical、semantic 或 mixed。

### 2. Cluster-aware graph expansion

`graph_expand` 在 `hybrid` 的候选上继续补 3 类 cluster：

- classic baseline
- same method family
- recent follow-up

实现上使用轻量启发式，不引入全量图数据库：

- 通过 query + seed candidates 推断 method family
- 用 snapshot/local paper rows 的 metadata 与 summary 字段做 cluster expansion
- 在 retrieval context 中记录新增候选的 `match_reasons`

### 3. Evidence-item rerank for graph_verify

`graph_verify` 不再把 critic 主要用于自由文本 chunk，而应直接用于结构化 evidence item：

- 输入：`paper_id/method/dataset/metric/value/polarity/limitation/comparability_warning`
- 输出：
  - relevance score
  - polarity confidence
  - comparability judgment
  - rerank order

第一版允许仍复用现有 critic 类，但外部 contract 必须转成 evidence-item 级别。

### 4. Counter-evidence-first retrieval for xval

对于 `cross_validation` intent，新增反例优先检索分支：

- 在原 query 基础上增加 negative probes：
  - `contradict`
  - `failure`
  - `regression`
  - `negative results`
  - `not directly comparable`
- 将这一路召回与正常支持证据召回合并
- coverage audit 必须区分：
  - 未找到反例
  - 没有执行反例检索

### 5. Benchmark parity and validation

需要补齐 profile parity：

- `manifest_v1.json` 加入 `hybrid`
- runner 支持 `paper_core` 对 `hybrid` 执行 end-to-end scoring
- 新增 deterministic tests 验证：
  - `hybrid` 确实不同于 `baseline`
  - `graph_verify` 的 rerank 输入是 evidence items
  - xval 反例检索会影响 `coverage_audit.has_counter_evidence`

## Risks / Trade-offs

- 风险：第一版“semantic recall”如果仍过弱，`hybrid` 可能只比 `baseline` 略好。
  - 缓解：先把 contract 做实，并以 benchmark 指标为推广门槛。
- 风险：cluster-aware expansion 若启发式过强，可能污染 precision。
  - 缓解：保持 top-k 上限，且记录 `match_reasons` 便于 benchmark 诊断。
- 风险：critic 迁移到 evidence-item 后可能产生格式兼容问题。
  - 缓解：先在 runtime 内部转换，保留对旧 critic 的薄适配层。

## Rollback Plan

- 若 `hybrid` 无法稳定优于 `baseline`，保留 manifest parity 但不默认推广 `hybrid`。
- 若 `graph_verify` 不能提升或维持 `graph_expand` 的质量，则将高阶默认 profile 固定在 `graph_expand`。
- 若 quality uplift 依赖不稳定的 benchmark 聚合或放宽 frozen contract，则回退到 foundation change 的聚合与治理基线。

## Ownership

- Retrieval quality ownership:
  - `backend/multi_agent_runtime.py`
- Benchmark parity ownership:
  - `evals/runners/run_suite.py`
  - `evals/datasets/paper_benchmark/manifest_v1.json`
- Quality verification ownership:
  - `tests/backend/test_multi_agent_runtime_structured.py`
  - `tests/evals/test_paper_benchmark_runner.py`
- Reviewer:
  - retrieval/runtime maintainer
  - paper benchmark maintainer
- Oncall:
  - backend oncall for runtime profile regressions
  - evals oncall for paper benchmark parity regressions

## Metrics Instrumentation

- Source:
  - frozen `paper_core` profile comparison from `evals/runners/run_suite.py`
- Runtime quality deltas are measured via frozen `paper_core` profile comparisons.
- Required aggregate metrics:
  - `paper_recall`
  - `cluster_coverage`
  - `support_recall`
  - `contradict_recall`
  - `balanced_evidence_rate`
  - `mean_total_tokens`
- Case-level diagnostics remain available through `case_results[*].scores` and `case_results[*].retrieval_context`.
- Threshold:
  - `hybrid.paper_recall > baseline.paper_recall`
  - `graph_expand.cluster_coverage >= 0.60`
  - `graph_verify.support_recall >= 0.50`
  - `graph_verify.contradict_recall >= 0.50`
  - `graph_verify.balanced_evidence_rate >= 0.50`
- Window:
  - evaluate on each implementation pass against frozen `paper_core`
  - promote only after repeat confirmation on larger slices

## Verification Plan

1. SDD：新增 quality-upgrades change 和 delta specs。
2. BDD：覆盖 related-work cluster、hybrid uplift、xval counter-evidence 三个关键场景。
3. TDD：补 profile parity、hybrid recall contract、evidence-item rerank contract tests。
4. Implementation：先做 `hybrid`，再做 `graph_expand` cluster-aware，最后做 `graph_verify` evidence rerank。
5. Deterministic verification：对 `paper_core` 做 profile 对比，并回归现有 retrieval suites。

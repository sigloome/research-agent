## Context

- 活跃 `/api/chat` 路径当前经过 `backend/agent.py -> _run_codex_sdk -> stream_codex_sdk`，`runtime_profile` 还没有进入活跃检索逻辑。
- `backend/multi_agent_runtime.py` 已定义 `baseline / graph / graph_critic`，但仍是旁路能力，且 `baseline` 依赖本地 SQL `LIKE` 搜索，Graph 返回值也偏自由文本。
- 现有 `paper_ingest` 已保证论文本地路径和关键摘要字段的 durability，为更强检索提供了最小数据底座。
- 仓库已存在 deterministic-first benchmark 治理要求和一个未完成的 `lock-paper-benchmark-dataset-and-tiered-runs` 变更，适合作为本文检索 benchmark 的治理基线。
- 该基线变更中关于 frozen tiers、signature、budget gate、snapshot restore、CI tier scheduling 的设计应吸收进当前 foundation change，避免并行维护两份相近方案。
- local run-log retention follows `tmp/runs/evolution/` and `tmp/runs/evolution/index.md` when execution evidence needs to be persisted outside tracked specs.

## Goals

1. 让论文检索 profile 真正接入活跃运行时，但保持实现分阶段推进。
2. 将 retrieval 输出统一成结构化 `retrieval context`，使 answer synthesis 与 benchmark 解耦。
3. 将 Graph 能力定位为候选扩展、coverage audit、证据补全，而不是直接承担最终自然语言回答。
4. 用 frozen dataset/snapshot/signature/budget gate 规范论文 benchmark，使结果稳定可比且成本受控。

## Non-Goals

1. 本 change 不要求完成完整 claim graph 自动抽取与全量图构建。
2. 不引入新的 blocking 在线数据源作为 benchmark 输入。
3. 不在本 change 中一次性重写所有 paper ingestion 逻辑。

## Design

### 1. Runtime profile contract

活跃 `/api/chat` 路径引入统一的 retrieval context builder。调用顺序为：

1. 解析 `runtime_profile`
2. 根据 query intent 选择 retrieval policy
3. 生成结构化 retrieval context
4. 将 retrieval context 注入 Codex answer synthesis

推荐 profile 语义：

- `baseline`: local lexical + metadata，低成本、可作为基线。
- `hybrid`: baseline + semantic/dense recall。
- `graph_expand`: hybrid + citation / method / dataset / relation graph expansion。
- `graph_verify`: graph_expand + critic-based comparability / polarity / evidence filtering。

第一阶段实现允许保留历史别名（如 `graph`、`graph_critic`），但内部语义以新四层为准。

### 2. Structured retrieval context

运行时不应只把 Graph answer 文本传给下游，而应输出可打分、可审计的结构化对象。建议字段：

- `profile`
- `intent`
- `query`
- `candidate_papers[]`
- `evidence_items[]`
- `coverage_audit`
- `params_signature`

其中 `coverage_audit` 至少包含：

- `has_classic_baseline`
- `has_recent_followup`
- `has_supporting_evidence`
- `has_counter_evidence`
- `has_comparability_warning`

### 3. Graph responsibility boundary

Graph 层不再直接作为最终答案生成器，而承担以下职责：

1. `candidate expansion`
   - 从种子论文扩展 citation / method / dataset / relation 邻居。
2. `coverage audit`
   - 检查是否只覆盖单一簇、是否缺少反例、是否缺少经典 baseline。
3. `structured evidence routing`
   - 将 query 路由为 related work / comparison / cross-validation 三类 evidence gathering 流程。

### 4. Evidence model for paper tasks

为 comparison / cross-validation 预留统一 evidence 结构：

- `paper_id`
- `evidence_type` (`summary`, `result_tuple`, `claim`, `citation_neighbor`)
- `task`
- `dataset`
- `metric`
- `value`
- `polarity` (`support`, `contradict`, `neutral`, `unknown`)
- `source_ref`

第一阶段允许部分字段为空，但 schema 必须稳定，便于 deterministic benchmark 按 slot 打分。

### 5. Benchmark governance integration

在现有 `paper-benchmark-governance` 基础上补充论文检索特有要求：

1. Frozen dataset tier
   - `core`: PR blocking，24 cases。
   - `full`: nightly blocking，72 cases。
   - `audit`: weekly non-blocking，24 high-difficulty cases。
2. Frozen snapshot restore
   - blocking tiers 必须 restore 指定 snapshot 后再跑。
3. Signature contract
   - `dataset_version`
   - `dataset_hash`
   - `snapshot_id`
   - `seed`
   - `params_signature`
   - `git_commit`
4. Budget gate
   - 样本数、token、p95 latency、timeout rate。
5. Repeat-run stability
   - 相同 signature 下至少支持一次重复运行比较关键 retrieval 指标波动。

此外，吸收已有治理变更中的执行要求：

6. Frozen dataset manifest and metadata
   - 为 `core/full/audit` 提供 versioned manifest、hash metadata、sample count 和 snapshot binding。
7. Snapshot manifest and restore instruction
   - 为 blocking tiers 提供显式 restore precondition 和失败即中止的 runner 合同。
8. CI tier scheduling
   - PR: frozen `core`
   - nightly: frozen `full`
   - weekly: frozen `audit`
9. Repo-level policy sync
   - 在 `docs/specs/agent-evaluation-standard.md` 与 `docs/specs/auto-evolving-backend.md` 中写明论文 benchmark 的冻结、预算与非阻塞/阻塞边界。

### 6. Deterministic metrics

第一阶段 benchmark 主要使用 deterministic metrics：

- `paper_recall_at_k`
- `cluster_coverage`
- `comparison_facet_coverage`
- `support_recall_at_k`
- `contradict_recall_at_k`
- `balanced_evidence_rate`
- `unsupported_claim_rate`
- `benchmark_signature_completeness`
- `budget_gate`

PR / nightly 不依赖 runtime LLM judge；weekly audit 可选抽样 judge，但不得成为唯一阻塞条件。

## Risks / Trade-offs

- 风险：profile 语义升级后，历史 `graph` / `graph_critic` 预期与新结构化输出不完全一致。
  - 缓解：保留别名解析，但把 contract 明确写入 specs 和 deterministic tests。
- 风险：benchmark 样本过大导致成本过高。
  - 缓解：固定 `core/full/audit` 样本量并在 manifest 中锁定 budget gate。
- 风险：Graph 扩展引入更多延迟，却未带来稳定 recall 收益。
  - 缓解：以 frozen `core` 指标做 rollout 决策，不满足指标则不推广默认 profile。
- 风险：若保留两套相近 benchmark 设计，后续可能出现 runner 和 spec 脱节。
  - 缓解：以当前 foundation change 作为唯一后续实现入口，吸收旧治理变更中的可取要求。

## Rollback Plan

- 若活跃 runtime profile 接线导致 `/api/chat` 行为异常，则回退到不注入 retrieval context 的默认路径。
- 若 frozen benchmark runner 无法稳定执行，则保留 manifest/snapshot 工件并回退到 planning-only validation。
- 若 graph profiles 不能在 frozen `core` 上稳定优于 baseline，则保留 `baseline` 为默认，仅保留 graph profiles 为实验能力。

## Ownership

- Runtime ownership:
  - `backend/agent.py`
  - `backend/multi_agent_runtime.py`
- Benchmark ownership:
  - `evals/runners/run_suite.py`
  - `evals/metrics/paper_benchmark.py`
  - `evals/datasets/paper_benchmark/`
- Governance ownership:
  - `docs/specs/agent-evaluation-standard.md`
  - `docs/specs/auto-evolving-backend.md`
- Reviewer:
  - backend/runtime maintainer
  - evals/benchmark maintainer
- Oncall:
  - backend oncall for `/api/chat` regressions
  - evals oncall for benchmark runner regressions

## Metrics Instrumentation

- Runtime emits structured `retrieval_context` with:
  - `candidate_papers`
  - `evidence_items`
  - `coverage_audit`
- Runner reports:
  - `paper_recall`
  - `cluster_coverage`
  - `comparison_facet_coverage` / `evidence_facet_coverage`
  - `support_recall`
  - `contradict_recall`
  - `balanced_evidence_rate`
  - `span_grounding_recall`
  - budget and signature metadata
- Threshold:
  - `related_paper_recall_at_10 >= 0.80`
  - `comparison_facet_coverage >= 0.80`
  - `support_evidence_recall_at_10 >= 0.75`
- Window:
  - PR blocking on `paper_core`
  - nightly blocking on `paper_full`
  - weekly non-blocking on `paper_audit`

## Verification Plan

1. SDD：新建 foundation change，新增 retrieval runtime 和 benchmark governance specs。
2. BDD：定义 related work / comparison / cross-validation 三类行为场景。
3. TDD：新增 deterministic metrics、signature gate、snapshot gate、budget gate tests。
4. Implementation：先打通活跃 runtime profile 与 retrieval context，再接 benchmark runner。
5. Deterministic verification：以 frozen `core` tier 作为 blocking gate，`full` nightly，`audit` weekly non-blocking。

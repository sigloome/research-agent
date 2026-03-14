## Why

当前项目已具备论文入库、Graph RAG、RAG critic 和 deterministic-first eval 框架，但论文检索主链路仍存在三个基础缺口：

1. 活跃 `/api/chat` 路径没有把 `runtime_profile` 真正接入主检索链路，Graph RAG 仍停留在可选实验能力。
2. 当前 `baseline` 论文检索实质上仍接近本地 SQL `LIKE` 搜索，无法稳定支撑“相关论文对比、交叉验证、支持/反驳证据补全”等论文场景。
3. benchmark 尚未为论文检索建立“冻结数据集 + 固定快照 + 固定参数 + 成本闸门 + 可比性签名”的完整治理合同，导致结果难以稳定比较，也难控制成本。

需要先建立一个基础变更，把论文检索的运行时接口、结构化检索上下文、Graph 扩展职责和 benchmark 治理合同统一下来。这个变更不追求一次性完成 claim graph，而是为后续 comparison / cross-validation 图层增强提供稳定底座。

## What Changes

- 新增 `paper-retrieval-runtime` 能力，定义论文查询在活跃 `/api/chat` 路径中的 runtime profile 合同、结构化 retrieval context 合同，以及 Graph/critic 的职责边界。
- 扩展 `paper-management` 能力，要求论文检索与 benchmark 使用结构化 evidence 与 coverage audit，而不是仅依赖自由文本回答。
- 复用并补齐 `paper-benchmark-governance` 能力，明确 frozen `core/full/audit` 数据集、固定 snapshot、signature、预算闸门和 repeat-run 可比性要求。
- 为后续实现定义分层检索路线：`baseline -> hybrid -> graph_expand -> graph_verify`，并要求结构化输出便于 deterministic benchmark 打分。
- 同步 benchmark 治理到仓库级规范与执行入口，包括 `docs/specs/agent-evaluation-standard.md`、`docs/specs/auto-evolving-backend.md`、`evals/runners/` 和 CI tier scheduling。

## Expected Benefit

- 提升论文相关工作检索的完整性，减少关键论文、关键 baseline 或关键 follow-up 漏召回问题。
- 为论文对比和交叉验证建立结构化 evidence 底座，避免只靠自由文本回答导致的不可比和不可审计问题。
- 让 benchmark 结果跨多次运行可比较、可追溯，并将成本控制在固定预算内。
- 将 Graph RAG 从“直接生成答案”收敛到“候选扩展、coverage audit、证据补全”的更稳职责。
- 避免仓库中出现“runtime contract 一套、benchmark governance 另一套”的分叉规范，降低后续演化成本。

## Impact

- 受影响目录：
  - `backend/`
  - `evals/metrics/`
  - `evals/runners/`
  - `evals/datasets/`
  - `evals/fixtures/`
  - `.github/workflows/`
  - `docs/specs/agent-evaluation-standard.md`
  - `docs/specs/auto-evolving-backend.md`
- 不引入新的 blocking 在线依赖；blocking benchmark 继续依赖 frozen 数据与固定 snapshot。

## Success Metrics

1. `related_paper_recall_at_10 >= 0.80` on frozen `core` tier.
2. `comparison_facet_coverage >= 0.80` on frozen `core` tier.
3. `support_evidence_recall_at_10 >= 0.75` on frozen `core` tier.
4. `unsupported_claim_rate <= 0.05` on frozen `core` tier.
5. `benchmark_signature_completeness = 1.0` for blocking tiers.
6. `repeat_run_metric_variance <= 0.05` for key retrieval metrics under identical signature.
7. `core_benchmark_p95_latency_ms <= 8000` and `timeout_rate = 0`.

## Risk Metrics

1. `benchmark_signature_completeness < 1.0` on any blocking tier run.
2. `core_benchmark_p95_latency_ms` exceeds baseline by more than `30%`.
3. `repeat_run_metric_variance > 0.05` for key retrieval metrics.
4. `timeout_rate > 0` on `paper_core`.

## Kill Criteria

- 若 `benchmark_signature_completeness < 1.0` 连续两次 blocking run 失败，暂停基于新 benchmark 的回归结论并回退到仅 deterministic retrieval gate。
- 若 `graph_expand` 或 `graph_verify` 在 frozen `core` 上连续两轮未优于 `baseline/hybrid`，暂停默认推广，仅保留实验 profile。
- 若 `core_benchmark_p95_latency_ms` 较 baseline 超过 `30%` 且连续两轮不回落，停止扩大 graph runtime 覆盖范围。
- 若 comparison / cross-validation 相关 deterministic 指标无法稳定复现（repeat-run variance > `0.05`），暂停后续 claim-graph rollout。

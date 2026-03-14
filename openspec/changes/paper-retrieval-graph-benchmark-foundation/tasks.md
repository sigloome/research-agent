## 1. SDD

- [x] 1.1 新建 foundation OpenSpec change，固化 retrieval runtime、benchmark governance、paper-management 增量要求。
- [x] 1.2 将论文检索 profile 语义统一为 `baseline / hybrid / graph_expand / graph_verify`，并定义历史别名兼容策略。
- [x] 1.3 定义 frozen `core/full/audit` benchmark tier、signature、budget、repeat-run 稳定性合同。
- [x] 1.4 将论文 benchmark governance 同步到 `docs/specs/agent-evaluation-standard.md`。
- [x] 1.5 将 rollout / budget / blocking policy 同步到 `docs/specs/auto-evolving-backend.md`。

## 2. BDD

- [x] 2.1 场景：活跃 `/api/chat` 路径在指定 `runtime_profile` 时输出结构化 retrieval context，而不是丢弃 profile。
- [x] 2.2 场景：related work 查询在 `graph_expand` 下补齐 classic baseline 与 recent follow-up coverage。
- [x] 2.3 场景：comparison 查询输出 method / dataset / metric / limitation facets，并在不可直接比较时给出 warning。
- [x] 2.4 场景：cross-validation 查询至少尝试收集 support 与 contradict 两侧 evidence，若未找到反例需显式声明。
- [x] 2.5 场景：blocking benchmark tier 在 snapshot restore 或 signature 缺失时 fail-fast。

## 3. TDD

- [x] 3.1 为 runtime profile 解析与 retrieval context schema 新增 deterministic tests。
- [x] 3.2 为 paper recall、cluster coverage、comparison facet coverage、support/contradict recall 新增 deterministic metrics tests。
- [x] 3.3 为 benchmark signature completeness、hash mismatch、budget gate、snapshot restore precondition 新增 deterministic tests。
- [x] 3.4 为 repeat-run stability calculation 新增 deterministic tests。

## 4. Implementation

- [x] 4.1 打通活跃 `backend/agent.py` 到 retrieval context builder，使 `runtime_profile` 在 `_run_codex_sdk` 路径生效。
- [x] 4.2 重构 `backend/multi_agent_runtime.py` 为结构化 retrieval context 输出，并兼容旧 profile 别名。
- [x] 4.3 扩展 paper retrieval / graph 扩展接口，输出结构化 candidate 与 evidence，而不是仅自由文本。
- [x] 4.4 新增 frozen benchmark dataset manifest、snapshot manifest、tier runner contract 和 report signature。
- [x] 4.5 将论文 benchmark 接入现有 deterministic-first runner 和 CI tier matrix。
- [x] 4.6 为 blocking tiers 增加 snapshot restore precondition enforcement。
- [x] 4.7 新增 nightly / weekly tier scheduling 或等效 workflow contract。

## 5. Verification

- [x] 5.1 运行新增 runtime / metric / benchmark contract tests。
- [x] 5.2 运行现有 retrieval deterministic suite，确保旧 gate 不回归。
- [x] 5.3 对 frozen `core` tier 进行一次 blocking 试跑并记录 signature、budget、stability 输出。
- [x] 5.4 更新 acceptance report 与 handoff/TODO continuity。
- [x] 5.5 确认吸收后的 foundation change 覆盖旧 `lock-paper-benchmark-dataset-and-tiered-runs` 的有效治理点，避免并行实现分叉。

## BDD Evidence

- Given active `/api/chat` receives `runtime_profile`, when `_run_codex_sdk` executes, then retrieval context is built instead of dropping the profile:
  - `tests/backend/test_paper_retrieval_runtime.py`
- Given related-work graph expansion runs, when candidate coverage is expanded, then classic baseline and recent follow-up markers are observable:
  - `tests/backend/test_multi_agent_runtime_structured.py`
- Given frozen benchmark suites execute, when runner preconditions are checked, then missing snapshot/signature state fails fast:
  - `tests/evals/test_paper_benchmark_runner.py`

## TDD Evidence

- Failing test:
  - `tests/evals/test_paper_benchmark_contracts.py`
  - `tests/evals/test_paper_benchmark_evidence.py`
  - `tests/evals/test_paper_benchmark_gold_scoring.py`
  - `tests/scripts/test_build_paper_benchmark_snapshot.py`
- Implemented:
  - runtime profile wiring, frozen manifest/snapshot validation, deterministic scoring, snapshot builder
- Passing:
  - the above tests pass under the final foundation implementation

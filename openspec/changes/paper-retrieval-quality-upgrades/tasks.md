## 1. SDD

- [x] 1.1 新建 `paper-retrieval-quality-upgrades` change，限定范围为 `hybrid`、cluster-aware `graph_expand`、evidence-item `graph_verify`。
- [x] 1.2 为 runtime、paper-management、benchmark-governance 写出增量要求。
- [x] 1.3 将当前 `paper_core` baseline/profile 结果写入 design 作为改造基线。

## 2. BDD

- [x] 2.1 场景：`hybrid` 在同一 query 下比 `baseline` 多召回至少一个 semantic-only candidate。
- [x] 2.2 场景：`graph_expand` 对 related-work 查询补齐 classic baseline、same-family、recent follow-up 中至少两类 cluster。
- [x] 2.3 场景：`graph_verify` 对 comparison/xval 直接基于结构化 evidence rerank，而非仅文本 chunk。
- [x] 2.4 场景：cross-validation 查询会主动执行反例检索，并把“未找到反例”和“未检索反例”区分开。
- [x] 2.5 场景：benchmark manifest 支持 `hybrid` profile parity，且 runner 能执行 `paper_core --params-signature hybrid`。

## 3. TDD

- [x] 3.1 为 `hybrid` lexical+semantic fusion contract 新增 deterministic tests。
- [x] 3.2 为 cluster-aware expansion 和 `match_reasons` 新增 deterministic tests。
- [x] 3.3 为 evidence-item critic/rerank 输入输出 contract 新增 deterministic tests。
- [x] 3.4 为 xval negative probe 与 counter-evidence audit 新增 deterministic tests。
- [x] 3.5 为 manifest `hybrid` parity 与 runner execution 新增 deterministic tests。

## 4. Implementation

- [x] 4.1 将 `hybrid` 从占位 profile 升级为真实 lexical+semantic fusion retrieval。
- [x] 4.2 重构 `graph_expand`，引入 cluster-aware candidate expansion。
- [x] 4.3 重构 `graph_verify`，让 critic 直接作用于结构化 evidence items。
- [x] 4.4 为 xval intent 增加 counter-evidence-first retrieval 分支与 coverage audit 区分。
- [x] 4.5 补齐 benchmark manifest 的 `hybrid` params signature 与 runner parity。

## 5. Verification

- [x] 5.1 运行新增 runtime / benchmark deterministic tests。
- [x] 5.2 回归现有 retrieval deterministic suites。
- [x] 5.3 重新跑 `paper_core` 的 `baseline / hybrid / graph_expand / graph_verify` 对比并记录结果。
- [x] 5.4 若关键指标未达标，更新 acceptance/rollout 建议，不默认提升 profile。

## BDD Evidence

- Given `hybrid` executes, when lexical and semantic recall are fused, then semantic-only candidates become observable beyond `baseline`:
  - `tests/backend/test_multi_agent_runtime_structured.py`
- Given `graph_verify` and benchmark parity execute, when runtime and runner process `hybrid/graph_*` profiles, then evidence-item rerank and profile parity remain observable:
  - `tests/evals/test_paper_benchmark_runner.py`

## TDD Evidence

- Failing test:
  - `tests/backend/test_multi_agent_runtime_structured.py`
  - `tests/evals/test_paper_benchmark_runner.py`
- Implemented:
  - semantic recall prioritization, cluster-aware merge reason preservation, evidence-item rerank, applicable-case benchmark aggregation
- Passing:
  - `tests/backend/test_multi_agent_runtime.py`
  - `tests/evals/test_paper_benchmark_contracts.py`
  - `tests/evals/test_paper_benchmark_gold_scoring.py`
  - the new runtime/runner tests pass after implementation

# Done Log (Local)

## 2026-03-05

- Implemented proposal validator and template.
- Implemented tasks validator and template.
- Implemented design validator and template.
- Implemented retention validator.
- Added `scripts/run_evolution_cycle.sh` with persisted reports.

## 2026-03-06

- Hardened research-agent SDK skill reliability with deterministic Claude auth preflight in `backend/agent.py`.
- Added runtime skill accessibility verifier: `scripts/check_skill_runtime_access.py`.
- Added live `/api/chat` skill-tool probe script: `scripts/probe_research_skill_tool_usage.sh`.
- Extended `scripts/check_claude_skill_config.py` to enforce auth preflight/env-builder presence.

## 2026-03-06 (LiteLLM PoC slice)

- Added LiteLLM bridge env/provider integration in `backend/agent.py`.
- Added deterministic check script: `scripts/check_litellm_bridge_config.py`.
- Added live bridge probe script: `scripts/probe_litellm_bridge.sh`.
- Confirmed live probe failure mode remains: no `tool-input`/`Skill` events in bridge stream.

## 2026-03-06 (Codex bridge skill reliability)

- Implemented codex bridge function-tool orchestration in `backend/agent.py` with native `Skill` tool definition.
- Added runtime `Skill` tool execution path for `list`, `knowledge`, and `preference` without manual SKILL content injection.
- Enforced skill-routed requests to require tool usage via bridge `tool_choice=required`.
- Added deterministic codex checks/probe scripts:
  - `scripts/check_codex_bridge_config.py`
  - `scripts/probe_codex_bridge.sh`
- Validated with real `/api/chat` run: observed `tool-input-*` events and `Skill` invocations (`list`, `knowledge`, `preference`) with `finishReason=stop`.

## 2026-03-06 (Codex bridge docs/setup alignment)

- Updated `docs/specs/core-features.md` to reflect codex bridge dependency (OpenAI-compatible Responses API endpoint).
- Updated `docs/specs/chat-interface.md` streaming contract example to UI-message SSE events (`start`, `text-delta`, `tool-input-*`, `tool-output-available`, `finish`, `[DONE]`).
- Updated `docs/specs/skills-system.md` to remove stale Claude SDK-specific constraint wording and stale `.claude/skills/...` path example.
- Updated `scripts/init_wizard.sh` to bootstrap codex bridge env vars instead of Anthropic/Claude token envs.
- Deterministic validation pass:
  - `python3 scripts/check_codex_bridge_config.py`
  - `python3 scripts/check_skill_runtime_access.py`
  - `pytest -q evals/tests/test_retrieval_prompt_paths.py evals/tests/test_retrieval_prompt_paths_audit.py`

## 2026-03-06 (Legacy helper cleanup for skill paths)

- Updated `scripts/update_specs.py` to remove `.claude/skills` assumptions and prefer runtime skill roots:
  - `skills/` primary
  - `.codex/skills` fallback
- Updated `scripts/sync_todo_skill_adapters.sh` target path from `.claude/skills/...` to `skills/...`.
- Revalidated:
  - `python3 scripts/check_codex_bridge_config.py` (pass)
  - `python3 scripts/check_skill_runtime_access.py` (pass)
  - `pytest -q evals/tests/test_retrieval_prompt_paths.py evals/tests/test_retrieval_prompt_paths_audit.py` (31 passed)

## 2026-03-06 (Runtime stability + smoke + logging + CI)

- Stabilized runtime listener state for validation and verified `scripts/check_dev_listener_sanity.sh` pass in a single-listener state.
- Added fail-fast daily smoke checker:
  - `scripts/smoke_codex_bridge.sh`
  - checks: health -> codex config -> runtime skill access -> live probe.
- Trimmed noisy streaming debug logs while preserving actionable warnings/errors:
  - `backend/agent.py`
  - `backend/app.py`
- Added deterministic CI workflow for non-live agent reliability gates:
  - `.github/workflows/deterministic-agent-checks.yml`
  - runs config check, runtime skill access check, and retrieval eval tests.
- Validated after changes:
  - `python3 scripts/check_codex_bridge_config.py` (pass)
  - `python3 scripts/check_skill_runtime_access.py` (pass)
  - `pytest -q evals/tests/test_retrieval_prompt_paths.py evals/tests/test_retrieval_prompt_paths_audit.py` (31 passed)
  - `./scripts/smoke_codex_bridge.sh` (pass with live server)

## 2026-03-06 (start-dev single-listener hardening)

- Updated `scripts/start-dev.sh` to reduce listener nondeterminism:
  - pre-start cleanup of existing listeners on backend/frontend ports
  - cleanup trap removes listeners on shutdown
  - supports `BACKEND_PORT` and `FRONTEND_PORT` overrides
  - frontend dev command now receives explicit `--port`
- Validation:
  - `bash -n scripts/start-dev.sh` (pass)
  - deterministic checks and eval tests still pass:
    - `python3 scripts/check_codex_bridge_config.py`
    - `python3 scripts/check_skill_runtime_access.py`
    - `pytest -q evals/tests/test_retrieval_prompt_paths.py evals/tests/test_retrieval_prompt_paths_audit.py`

## 2026-03-07 (Interview pack in tmp)

- Added session-scoped interview deliverables under `tmp/interview_pack/` (no tracked docs/scripts modified):
  - `tmp/interview_pack/docs/architecture.md`
  - `tmp/interview_pack/docs/evaluation.md`
  - `tmp/interview_pack/docs/changelog-runtime-migration.md`
  - `tmp/interview_pack/evals/datasets/interview_demo.jsonl`
  - `tmp/interview_pack/scripts/eval_e2e.sh`
- Executed `tmp/interview_pack/scripts/eval_e2e.sh` and generated:
  - `tmp/interview_pack/reports/e2e_report.md`
  - `tmp/interview_pack/reports/e2e_run.log`
- Deterministic gate result captured in report/log:
  - `pytest -q evals/tests/test_retrieval_prompt_paths.py evals/tests/test_retrieval_prompt_paths_audit.py`
  - outcome: 31 passed.
- Updated `tmp/interview_pack/docs/evaluation.md` to strict "implemented vs planned" split aligned with current repo eval reality.
- Normalized temporary interview docs to capability-first generic naming (removed project-specific branding and reduced provider/skill-specific phrasing where possible).

## 2026-03-08 (Multi-agent runtime + live benchmark loop)

- Implemented explicit multi-agent runtime skeleton in tracked backend code:
  - `backend/multi_agent_runtime.py`
  - typed handoff envelope (`ok/payload/error/fallback/latency`)
  - profiles: `baseline`, `graph`, `graph_critic`
- Wired optional `runtime_profile` through `/api/chat` request path:
  - `backend/app.py` (`ChatRequest.runtime_profile`)
  - `backend/agent.py` (runtime context injection path)
- Added deterministic tests for runtime skeleton:
  - `tests/backend/test_multi_agent_runtime.py`
  - pass result: `3 passed`
- Re-validated deterministic eval gate:
  - `pytest -q evals/tests/test_retrieval_prompt_paths.py evals/tests/test_retrieval_prompt_paths_audit.py`
  - pass result: `31 passed`
- Upgraded interview e2e script + added live benchmark parser:
  - `tmp/interview_pack/scripts/eval_e2e.sh`
  - `tmp/interview_pack/scripts/live_benchmark.py`
  - supports live `/api/chat`, SSE parsing (`tool-input-*`, `finish`, `[DONE]`) and metrics:
    - `ttft_ms`, `latency_p95_ms`, `done_marker_rate`, `tool_path_compliance`, `tool_failure_rate`
- Generated latest reports with real run values:
  - `tmp/interview_pack/reports/e2e_report.md`
  - `tmp/interview_pack/reports/live_benchmark_report.json`
  - `tmp/interview_pack/reports/live_benchmark_report.md`
  - `tmp/interview_pack/reports/variant_comparison.md`
- Added interview delivery docs in tmp:
  - `tmp/interview_pack/docs/architecture-v2.md`
  - `tmp/interview_pack/docs/evaluation-v2.md`
  - `tmp/interview_pack/docs/implementation-status.md`
  - `tmp/interview_pack/docs/interview-script-60s.md`
  - `tmp/interview_pack/docs/interview-script-3min.md`
  - `tmp/interview_pack/docs/failure-postmortem-template.md`


## 2026-03-10 (Benchmark diagnostics + rollout gate)

- Completed interview benchmark optimization item #1:
  - split mixed `tool_path_compliance` into:
    - `route_compliance`
    - `content_compliance`
    - keep combined `tool_path_compliance` for backward comparability
  - implementation: `tmp/interview_pack/scripts/live_benchmark.py`
- Completed interview benchmark optimization item #2:
  - added profile-level rollout recommendation thresholds into comparison report
  - implementation: `tmp/interview_pack/scripts/live_benchmark.py` report generation output
- Re-ran full evaluation loop with real data:
  - `BASE_URL=http://127.0.0.1:18000 PROFILES=baseline,graph,graph_critic tmp/interview_pack/scripts/eval_e2e.sh`
  - deterministic suite: `31 passed`
  - reports refreshed:
    - `tmp/interview_pack/reports/live_benchmark_report.json`
    - `tmp/interview_pack/reports/live_benchmark_report.md`
    - `tmp/interview_pack/reports/variant_comparison.md`
- Added metric-to-description mapping artifact:
  - `tmp/interview_pack/docs/metrics-required-and-description-update-plan-v1.md`
- Updated project description with metric upgrade rules:
  - `tmp/interview_pack/docs/project-description-v4.md`


## 2026-03-10 (Final interview benchmark completion)

- Completed remaining interview metrics/tasks in one pass:
  - added contract-level proxy metrics in benchmark output:
    - `handoff_schema_valid_rate`, `agent_boundary_violation_rate`, `verifier_block_rate`
  - added quality/personalization proxy metrics:
    - `evidence_coverage_rate`, `unsupported_claim_rate`, `preference_hit_rate`, `preference_conflict_rate`
  - added repeat-run mode (`REPEATS`) with stability check result in reports
- Converted benchmark dataset prompts/expectations to English for git-ready consistency
- Re-ran deterministic and live benchmark verification:
  - deterministic suite: `31 passed`
  - live benchmark repeated run (`k=2`) generated updated reports
- Finalized docs with metric-backed summary:
  - `tmp/interview_pack/docs/final-experiment-summary-2026-03-10.md`
  - `tmp/interview_pack/docs/project-description-final-metrics.md`

## 2026-03-10 (Evolution automation + executable BDD gate)

- Implemented change bootstrap automation:
  - `scripts/new_evolution_change.sh`
  - scaffolds `proposal.md/design.md/tasks.md/specs/` with mandatory section context and run-log references.
- Implemented auto trigger engine:
  - `scripts/trigger_evolution.sh`
  - supports PASS/FAIL trigger handling, failed-run follow-up change scaffold, and summary sync into:
    - `tmp/runs/evolution/index.md`
    - `todos/handoff.md`
- Integrated trigger flow with deterministic cycle:
  - updated `scripts/run_evolution_cycle.sh` to invoke trigger script after each run.
- Added executable BDD gate and made it merge-blocking:
  - new tests: `tests/backend/test_bdd_chat_flow.py`
  - coverage: stream completion markers, tool trace event visibility, user/assistant history persistence.
  - hooked into local and CI gates:
    - `.githooks/pre-push`
    - `scripts/lint.sh`
    - `.github/workflows/deterministic-agent-checks.yml`
- Added stable benchmark entrypoint in tracked scripts:
  - `scripts/run_live_benchmark.sh` (delegates to existing interview pack benchmark runner).

## 2026-03-12 (Codex SDK single-provider + API/Frontend validation)

- Consolidated runtime to one provider (`codex_sdk`) in `backend/agent.py`.
- Verified Codex SDK package usage path:
  - `backend/codex_sdk_adapter/run_stream.mjs` -> `import { Codex } from "@openai/codex-sdk"`.
- Re-ran deterministic checks:
  - `pytest -q tests/backend/test_codex_exec_runtime.py tests/backend/test_bdd_chat_flow.py` (`5 passed`)
  - `python3 scripts/check_codex_bridge_config.py` (pass)
  - `frontend npm run build` (pass)
- Ran live API and frontend E2E verification:
  - `/api/chat` SSE stream shape valid with `[DONE]`
  - frontend transcript renders assistant response token `FRONTEND_ASSERT_20260312`.

## 2026-03-12 (Naming cleanup: codex_exec -> codex_sdk)

- Completed naming normalization in runtime and tests:
  - `backend/codex_sdk_runtime.py`
  - `tests/backend/test_codex_sdk_runtime.py`
- Updated `backend/agent.py` to use `stream_codex_sdk` and `_run_codex_sdk`.

## 2026-03-14 (Paper retrieval graph benchmark foundation completed)

- Completed `openspec/changes/paper-retrieval-graph-benchmark-foundation/` end to end:
  - active `_run_codex_sdk` path honors `runtime_profile`
  - runtime profiles unified to `baseline / hybrid / graph_expand / graph_verify`
  - structured retrieval context and coverage audit emitted from `backend/multi_agent_runtime.py`
  - `graph_expand` now augments related-work retrieval with classic baseline and recent follow-up coverage
  - paper benchmark runner executes real `MultiAgentRuntime` retrieval against frozen snapshot data and emits aggregate deterministic scores
  - span grounding upgraded from exact-only source ref matching to semantic same-paper span equivalence with structured-field overlap
- Added/updated frozen benchmark artifacts:
  - `evals/datasets/paper_benchmark/`
  - `evals/fixtures/paper_benchmark/snapshots/papers_snapshot_v1.sqlite`
  - `scripts/build_paper_benchmark_snapshot.py`
- Synced tracked artifacts and closure docs:
  - `openspec/.../tasks.md`
  - `openspec/.../acceptance-report.md`
  - `docs/specs/agent-evaluation-standard.md`
  - `docs/specs/auto-evolving-backend.md`
- Verification:
  - `python3 -m pytest -q tests/backend/test_multi_agent_runtime.py tests/backend/test_paper_retrieval_runtime.py tests/backend/test_codex_sdk_runtime.py tests/evals/test_paper_benchmark_contracts.py tests/evals/test_paper_benchmark_evidence.py tests/evals/test_paper_benchmark_gold_scoring.py tests/evals/test_paper_benchmark_runner.py tests/backend/test_multi_agent_runtime_structured.py evals/tests/test_retrieval_prompt_paths.py evals/tests/test_retrieval_prompt_paths_audit.py` -> `58 passed`
  - `python3 -m evals.runners.run_suite --suite paper_core --params-signature graph_expand --git-commit testsha` -> pass

## 2026-03-14 (Paper retrieval quality upgrades first pass)

- Added follow-up OpenSpec change:
  - `openspec/changes/paper-retrieval-quality-upgrades/`
- Implemented first quality-upgrade pass:
  - real `hybrid` parity in benchmark manifest and runner
  - lexical + semantic fusion path in `backend/multi_agent_runtime.py`
  - cluster-aware `graph_expand` merge reason preservation
  - evidence-item rerank path for `graph_verify`
  - xval counter-evidence probe path and audit distinction
- Added deterministic tests for:
  - semantic-only hybrid candidate behavior
  - cluster-aware expansion reasons
  - evidence-item rerank contract
  - benchmark `hybrid` parity
- Verification:
  - `python3 -m pytest -q tests/backend/test_multi_agent_runtime.py tests/backend/test_paper_retrieval_runtime.py tests/backend/test_codex_sdk_runtime.py tests/backend/test_multi_agent_runtime_structured.py tests/evals/test_paper_benchmark_contracts.py tests/evals/test_paper_benchmark_evidence.py tests/evals/test_paper_benchmark_gold_scoring.py tests/evals/test_paper_benchmark_runner.py evals/tests/test_retrieval_prompt_paths.py evals/tests/test_retrieval_prompt_paths_audit.py` -> `63 passed`
  - `paper_core` profile comparison rerun completed for `baseline / hybrid / graph_expand / graph_verify`
- Outcome:
  - implementation contracts completed
  - proposed quality targets met on frozen `paper_core`
  - rollout recommendation remains conservative for live traffic until larger-slice verification

## 2026-03-14

- Performed repo git hygiene pass for generated/runtime artifacts.
- Updated root `.gitignore` to ignore:
  - `/.codex-agent-runtime/`
  - `/output/`
  - `/frontend/playwright-report/`
- Removed tracked Playwright report artifact from git index while preserving local file:
  - `frontend/playwright-report/index.html`
- Ran tracked-file artifact audit; no additional tracked generated/runtime artifacts detected by pattern scan.
- Renamed config checker to:
  - `scripts/check_codex_sdk_config.py`
  - synced invocations from smoke/evolution/skill-check scripts.
- Preserved env backward compatibility:
  - prefers `CODEX_SDK_MODEL`, still accepts legacy `CODEX_EXEC_MODEL`.
- Verification completed:
  - `pytest -q tests/backend/test_codex_sdk_runtime.py tests/backend/test_bdd_chat_flow.py` (`5 passed`)
  - `python3 scripts/check_codex_sdk_config.py` (pass)
  - `cd frontend && npm run build` (pass)
  - live `/api/chat` probe returned `RENAMED_OK_20260312` with complete SSE lifecycle.

## 2026-03-12 (OpenSpec change-id doc naming alignment)

- Renamed OpenSpec change folder:
  - `openspec/changes/add-codex-exec-provider-sse-compat`
  - -> `openspec/changes/add-codex-sdk-provider-sse-compat`
- Updated internal references in change artifacts to the new change-id string.
- Confirmed no residual old-id references via repository grep.
- Validation executed:
  - `pytest -q tests/backend/test_bdd_chat_flow.py` -> `3 passed`
  - `pytest -q evals/tests/test_retrieval_prompt_paths.py evals/tests/test_retrieval_prompt_paths_audit.py` -> `31 passed`
  - `python scripts/check_openspec_proposals.py && python scripts/check_openspec_tasks.py && python scripts/check_openspec_design.py && python scripts/check_openspec_retention.py` -> pass
  - shell syntax checks for new/updated scripts/hooks -> pass

## 2026-03-10 (Candidate generation pipeline)

- Implemented manual-assisted candidate generation pipeline:
  - `scripts/generate_evolution_candidates.sh`
  - flow: artifact validation -> deterministic verification -> candidate task list generation
  - explicit rule: no code-changing action in this script, human approval required.
- Produced candidate output artifact:
  - `tmp/runs/evolution/candidates/20260310-162042.md`
- Synced governance spec:
  - updated `docs/specs/auto-evolving-backend.md` rollout section with the new script entry.

## 2026-03-10 (Full-loop claim gap closure package)

- Delivered complete auditable change package:
  - `openspec/changes/close-remaining-agent-gap/`
  - artifacts: proposal/design/tasks/spec deltas/acceptance report.
- Runtime architecture closure:
  - added explicit answer envelope in `backend/multi_agent_runtime.py`.
  - added per-agent trace SSE events in `backend/agent.py` (`agent-trace`).
  - parser compatibility update in `evals/adapters/stream_parser.py`.
- Governance completion items implemented:
  - `scripts/promotion_workflow.sh`
  - `scripts/sync_runlogs_to_openspec.sh`
  - `scripts/check_ownership_policy.py`
  - `docs/specs/evolution-trigger-playbook.md`
- Gate integration updates:
  - `.githooks/pre-push`
  - `scripts/lint.sh`
  - `.github/workflows/deterministic-agent-checks.yml`
- Validation evidence:
  - runtime/governance test bundle: `8 passed`
  - deterministic retrieval gate: `31 passed`
  - evolution cycle: `PASS`
  - promotion workflow: warning count `0`

## 2026-03-10 (Runtime simplification + stability hardening)

- Implemented remaining P0 runtime simplification item:
  - `backend/agent.py` refactor with helper methods for auth preflight, payload construction, and reliability hooks.
  - added bounded timeout/retry for transient bridge failures with consistent error envelope behavior.
- Stabilized start-dev listener lifecycle:
  - `scripts/start-dev.sh` now performs post-start deterministic sanity check and fails fast on duplicate listeners.
- Implemented long-window trend export:
  - `tmp/interview_pack/scripts/export_weekly_trends.py`
  - generated weekly artifacts under `tmp/interview_pack/reports/weekly/`.
- Added deterministic test:
  - `tests/scripts/test_export_weekly_trends.py`
- Added auditable OpenSpec package:
  - `openspec/changes/runtime-simplify-and-stability-hardening/`
  - with `proposal/design/tasks/specs/acceptance-report`.

## 2026-03-10 (Metric strictness hardening)

- Added parser-backed claim/evidence grounding metric:
  - `evals/metrics/claim_grounding.py`
- Added deterministic tests:
  - `evals/tests/test_claim_grounding.py`
  - suite result with existing eval gates: `33 passed`.
- Updated eval docs:
  - `evals/README.md` now lists parser-backed grounding metric coverage.

## 2026-03-10 (Per-iteration live benchmark non-blocking integration)

- Updated `scripts/run_evolution_cycle.sh` to auto-run `scripts/run_live_benchmark.sh` after deterministic checks.
- Kept live benchmark as soft-warning only (non-blocking):
  - failure recorded as `[!]` with warning section in run report.
  - does not change deterministic PASS/FAIL decision.
- Added summary signal in evolution report:
  - `Soft warnings (non-blocking): <count>`.
- Synced policy docs:
  - `docs/specs/evolution-trigger-playbook.md`
  - `docs/specs/auto-evolving-backend.md`
  - clarified that periodic full live benchmark is not enabled by default for now.
- Validation:
  - shell syntax checks passed.
  - `scripts/run_evolution_cycle.sh` PASS with live benchmark warning path verified.

## 2026-03-11 (Codex core + Vercel SSE demo validation)

- Added isolated runnable demo under `tmp/demos/codex_sse_demo/`:
  - `server.py`: bridges `codex exec --json` events into Vercel UI message stream SSE (`x-vercel-ai-ui-message-stream: v1`).
  - `README.md`: run and verify instructions.
- Ran real end-to-end checks (not mocked):
  - success path returns `start/start-step/text-start/text-delta/text-end/finish-step/data-metrics/finish/[DONE]`.
  - invalid model path returns normalized SSE error envelope with `finishReason=error`.
  - invalid `profile` returns `Error: config profile ... not found`, proving codex profile/config options are wired through.
- Fixed demo pitfalls found during run:
  - corrected SSE separator emission (`\n\n` bug).
  - deduplicated `error` + `turn.failed` double emission.
  - added non-JSON stderr diagnostic fallback when codex exits non-zero without structured error event.

## 2026-03-11 (Mainline codex_exec provider integration)

- Added OpenSpec change package:
  - `openspec/changes/add-codex-exec-provider-sse-compat/`
  - includes `proposal.md`, `design.md`, `tasks.md`, spec delta, and `acceptance-report.md`.
- Implemented optional runtime provider integration in main backend:
  - `AGENT_PROVIDER=codex_exec` path in `backend/agent.py`.
  - new helper module `backend/codex_exec_runtime.py` for codex JSONL -> UI SSE mapping.
- Completed TDD cycle:
  - introduced failing tests first, then implemented green path.
  - added `tests/backend/test_codex_exec_runtime.py`.
- Completed live verification:
  - API stream check under `AGENT_PROVIDER=codex_exec`.
  - frontend real browser check confirms assistant response rendered normally.
- Fixed runtime regression found during live verification:
  - removed duplicate `[DONE]` emission from provider helper (app layer remains sole `[DONE]` emitter).

## 2026-03-11 (codex-sdk replacement)

- Replaced codex runtime execution path to use real `@openai/codex-sdk` via local Node adapter:
  - `backend/codex_sdk_adapter/run_stream.mjs`
  - `backend/codex_sdk_adapter/package.json` (dependency: `@openai/codex-sdk`)
- Updated Python provider helper to invoke SDK adapter instead of direct `codex exec`.
- Re-verified:
  - backend tests pass,
  - `/api/chat` live stream returns expected SSE contract with SDK backend,
  - frontend live chat displays streamed SDK response (`frontend-sdk-ok`).

## 2026-03-11 (single provider consolidation)

- Consolidated backend runtime to single provider `codex_sdk` in `backend/agent.py`.
- Removed runtime branch selection in active chat execution path; `run()` now always uses codex-sdk adapter path.
- Updated deterministic config validator to enforce single-provider runtime:
  - `scripts/check_codex_bridge_config.py` (kept filename for compatibility).
- Updated startup/setup hints:
  - `scripts/start-codex.sh`
  - `scripts/init_wizard.sh`
- Synced OpenSpec change docs to single-provider statements.
- Re-verified:
  - backend tests (`test_codex_exec_runtime`, `test_bdd_chat_flow`) pass,
  - config check script passes,
  - live `/api/chat` stream returns expected contract.

## 2026-03-12 (codex-native-skill-paper-ingest implementation)

- Implemented codex-native tool event mapping in `backend/codex_sdk_runtime.py` for MCP/native tool lifecycle:
  - emits `tool-input-start`, `tool-input-available`, `tool-output-available` and native tooling signal.
- Added codex config override passthrough for adapter:
  - `backend/codex_sdk_runtime.py` reads `CODEX_CONFIG_OVERRIDES_JSON`
  - `backend/codex_sdk_adapter/run_stream.mjs` forwards `configOverrides` into `new Codex({ config })`.
- Added paper ingest durability contract:
  - `skills/knowledge/paper/core.py` -> `paper_ingest(...)`
  - success requires local path + key summary fields.
- Exposed ingest in paper adapters:
  - `skills/knowledge/paper/tool.py`
  - `skills/knowledge/paper/__main__.py` (`ingest` command)
- Updated runtime bridge helper path for compatibility:
  - `backend/agent.py` uses `_build_full_query(...)` in `_run_codex_sdk`
  - `_run_skill_tool` supports knowledge op `paper_ingest` for fallback compatibility.
- Fixed stale script import and contract path:
  - `scripts/process_all_papers.py` now imports `skills.knowledge.paper.core` and uses `paper_ingest`.
- Added/updated deterministic tests:
  - `tests/backend/test_codex_sdk_runtime.py` (native tool event mapping)
  - `tests/skills/paper/test_ingest_contract.py`
  - `tests/backend/test_bdd_paper_ingest_flow.py`
  - `tests/scripts/test_process_all_papers_script.py`
- Governance docs synced:
  - `docs/specs/agent-evaluation-standard.md`
  - `docs/specs/auto-evolving-backend.md`
- OpenSpec change artifacts completed and acceptance report added:
  - `openspec/changes/codex-native-skill-paper-ingest/acceptance-report.md`

## 2026-03-12 (codex-native streaming + de-manualized routing)

- Updated `backend/codex_sdk_runtime.py` to stream SDK events incrementally instead of buffering all lines before emitting SSE.
- Added stateful codex event mapper that supports:
  - native tool lifecycle (`tool-input-start`, `tool-input-available`, `tool-output-available`)
  - incremental text via `response.output_text.delta`
  - agent message incremental delta extraction from `item.updated/item.completed`.
- Removed active-path manual prompt injection for skill routing in `backend/agent.py` (`[MANDATORY TOOL ROUTING]` no longer prepended).
- Added deterministic parser test coverage for output-text delta events:
  - `tests/backend/test_codex_sdk_runtime.py`.
- Verification:
  - `pytest -q tests/backend/test_codex_sdk_runtime.py tests/backend/test_bdd_chat_flow.py` -> `7 passed`.

## 2026-03-12 (Codex-native fetch summary)

- Replaced summarizer LLM path with Codex-native adapter execution:
  - `skills/knowledge/summarizer/summarize.py`
  - `backend/codex_sdk_adapter/run_summary.mjs`
- Updated paper fetch pipeline to trigger durable ingest for new/incomplete items:
  - `skills/knowledge/paper/core.py`
- Added deterministic tests and passed regressions:
  - `tests/skills/paper/test_operations.py`
  - `tests/skills/summarizer/test_codex_summary.py`
  - combined verification set: `21 passed`.
- Added and completed OpenSpec artifacts:
  - `openspec/changes/codex-native-fetch-summary/`

## 2026-03-12 (versioned arXiv ID routing compatibility)

- Added canonical arXiv ID resolver (strip `vN`) and integrated it across backend paper lookup and ingest/fetch flow.
- Added frontend route canonical redirect for `/paper/:id` with version suffix.
- Added deterministic tests for canonicalization and versioned-ID API compatibility.
- Added OpenSpec artifacts under `openspec/changes/normalize-arxiv-versioned-ids/` with acceptance report.

## 2026-03-12 (frontend e2e canonical redirect)

- Added and executed Playwright e2e test for versioned arXiv route canonicalization:
  - `frontend/tests/e2e/paper-canonical.spec.ts`
  - chromium run: `1 passed`.

## 2026-03-14 (paper retrieval graph benchmark foundation artifacts)

- Created new OpenSpec change scaffold and artifacts:
  - `openspec/changes/paper-retrieval-graph-benchmark-foundation/`
- Added proposal, design, tasks, and spec deltas for:
  - `paper-retrieval-runtime`
  - `paper-benchmark-governance`
  - `paper-management`
- This pass intentionally stopped at SDD artifact creation; implementation and tests remain pending under the new change tasks.

## 2026-03-14 (paper retrieval foundation first runtime + benchmark slice)

- Updated active runtime path in `backend/agent.py` so `_run_codex_sdk` now honors `runtime_profile` and injects retrieval context before answer synthesis.
- Added deterministic runtime tests:
  - `tests/backend/test_paper_retrieval_runtime.py`
- Added deterministic paper benchmark metrics and tests:
  - `evals/metrics/paper_benchmark.py`
  - `tests/evals/test_paper_benchmark_contracts.py`
- Adjusted `tests/backend/test_codex_sdk_runtime.py` to avoid implicit async-plugin dependency in this environment.
- Verification:
  - targeted runtime + benchmark tests: `11 passed`
  - existing retrieval eval suite: `31 passed`

## 2026-03-14 (paper retrieval foundation structured runtime + runner contract)

- Removed superseded benchmark-only OpenSpec change files and consolidated their useful governance requirements into the foundation change.
- Upgraded `backend/multi_agent_runtime.py` to emit structured retrieval payloads and a serialized `[RetrievalContext]` answer context.
- Added paper benchmark dataset/manifest/snapshot scaffolding:
  - `evals/datasets/paper_benchmark/`
  - `evals/fixtures/paper_benchmark/snapshots/papers_snapshot_v1.sqlite`
- Extended `evals/runners/run_suite.py` with `build_paper_benchmark_plan(...)` for frozen tier planning, snapshot precondition enforcement, and signature construction.
- Added deterministic tests for structured runtime output and benchmark runner contracts.
- Verification:
  - new targeted tests: `10 passed`
  - existing retrieval deterministic suite: `31 passed`

## 2026-03-14 (paper benchmark governance docs + CI wiring)

- Updated shared policy docs with paper benchmark governance, blocking/non-blocking tier policy, and required deterministic metrics.
- Extended `evals/runners/run_suite.py` CLI to expose:
  - `paper_core`
  - `paper_full`
  - `paper_audit`
- Updated CI workflow to validate paper benchmark planning on PR/push and scheduled runs.
- Verification:
  - runner CLI for all three paper suites executed successfully
  - benchmark runner/contract tests: `7 passed`
  - retrieval deterministic suite remained green: `31 passed`

## 2026-03-14 (curated paper benchmark datasets and real hash locking)

- Replaced placeholder paper benchmark JSONL files with curated frozen cases containing gold expectations for related-work, comparison, cross-validation, and synthesis tasks.
- Locked real SHA-256 hashes and actual sample counts into `evals/datasets/paper_benchmark/manifest_v1.json`.
- Strengthened runner validation to fail on dataset hash mismatch or sample count drift.
- Extended runtime evidence extraction and benchmark metrics to score structured comparison/xval evidence facets.
- Verification:
  - foundation runtime + benchmark tests: `12 passed`
  - runner CLI for `paper_core/paper_full/paper_audit`: pass
  - retrieval deterministic suite: `31 passed`

## 2026-03-14 (paper retrieval foundation acceptance closure)

- Added snapshot builder script and deterministic test.
- Replaced benchmark snapshot placeholder with a real SQLite snapshot containing the curated benchmark paper subset.
- Extended runner to verify snapshot contains all paper IDs referenced by frozen datasets.
- Added case-level gold scoring from retrieval context, span-level grounding recall, and acceptance report for the foundation change.
- Completed runtime profile naming migration to `baseline / hybrid / graph_expand / graph_verify` while keeping legacy aliases compatible.
- Updated OpenSpec tasks to reflect actual completion status:
  - all foundation tasks complete
- Final verification:
  - foundation-focused suite: `16 passed`
  - retrieval deterministic suite + runtime structured tests: `37 passed`

# Auto-Evolving Backend Specification

## Overview

This document defines how the backend can evolve automatically while remaining safe, explainable, and stable.

It also serves as the single onboarding guide for:

1. What already exists in this project.
2. How new features are proposed and evaluated.
3. How strict SDD, BDD, and TDD are enforced.
4. How intermediate artifacts (proposal notes, TODOs, decisions, run logs) are stored for continuous agent work.

## Current Project Feature Inventory

### Backend/API Capabilities

1. Health and feedback:
   - `GET /api/health`
   - `POST /api/feedback`
2. Chat and session management:
   - `GET /api/chats`
   - `POST /api/chats`
   - `GET /api/chats/{chat_id}`
   - `DELETE /api/chats/{chat_id}`
   - `POST /api/chat` (SSE streaming)
3. Papers:
   - `GET /api/papers`
   - `GET /api/papers/{paper_id}`
   - `GET /api/paper/{paper_id}`
   - `POST /api/paper/{paper_id}/analyze`
4. Notes:
   - `GET /api/notes`
   - `GET /api/notes/{note_id}`
   - `POST /api/notes`
   - `PUT /api/notes/{note_id}`
   - `DELETE /api/notes/{note_id}`
   - `POST /api/notes/{note_id}/links`
   - `DELETE /api/notes/{note_id}/links/{link_id}`
   - `GET /api/papers/{paper_id}/notes`
5. Books and sources:
   - `GET /api/books`
   - `GET /api/books/{book_id}`
   - `GET /api/books/search/{query}`
   - `GET /api/sources`
   - `POST /api/sources`
   - `GET /api/sources/{source_id}`
   - `PUT /api/sources/{source_id}`
   - `DELETE /api/sources/{source_id}`
6. User preference output:
   - `GET /api/preferences`

### Architecture Capabilities Already Present

1. FastAPI backend + SSE streaming chat.
2. Skill-based modular system (knowledge, preference, book, local files, etc.).
3. SQLite-backed persistence for papers, books, chat history, and preferences.
4. Deterministic-first eval framework under `evals/`.
5. OpenSpec workflow and change artifacts under `openspec/`.

## Goal: Safe Automatic Evolution

Automatic evolution means the system can propose and implement improvements, then promote only candidates that pass strict objective gates.

The target loop is:

1. Detect opportunity.
2. Propose change with measurable value.
3. Generate candidate deltas.
4. Run review + eval gates.
5. Promote cautiously.
6. Learn from outcomes and update future proposals.

## Mandatory Feature Justification

Every new feature MUST include a `Why add this?` section before implementation.

Required fields:

1. `problem_statement`: Current pain and who is affected.
2. `baseline`: Current metric values or observed failure frequency.
3. `expected_benefit`: Intended impact on quality, speed, safety, cost, or UX.
4. `success_metrics`: Numeric targets with time window.
5. `risk_metrics`: Numeric rollback triggers.
6. `kill_criteria`: Conditions to stop/retire the feature.

Example metric set:

1. Deterministic eval pass rate: `>= 99%` on PR profile.
2. Production incident rate: `< 0.5%` requests with server error.
3. Median latency: no regression above `10%`.
4. Tool or schema contract violations: `0`.
5. Cost budget: no regression above pre-defined threshold.

## Auto-Evolution Architecture

### Component Map

1. `Signal Collector`
   - Inputs: test failures, eval drift, bug reports, latency/cost changes, user feedback.
2. `Change Proposer`
   - Produces: proposal/design/tasks/spec deltas with explicit rationale + metrics.
3. `Candidate Generator`
   - Produces: code/test/eval candidates under constrained scope.
4. `Review Engine`
   - Runs mandatory SDD/BDD/TDD checks and deterministic eval gates.
5. `Risk Gate + Promotion Controller`
   - Applies staged rollout policy: sandbox -> shadow -> canary -> full.
6. `Learning Memory`
   - Stores failed/successful patterns for future proposal quality.

### Promotion Policy

1. No direct production promotion from generated code.
2. Candidate must pass all blocking gates.
3. High-risk areas require explicit human approval even after green gates.
4. Rollback plans are required before canary promotion.

## AI-Resistant Review System

Review is mandatory for all features, including the auto-evolving subsystem itself.

### Blocking Gates

1. **Spec Gate (SDD)**
   - Required: updated spec/proposal/design/tasks with rationale + metrics.
2. **Behavior Gate (BDD)**
   - Required: executable Given/When/Then acceptance scenarios.
3. **Test Gate (TDD)**
   - Required: failing tests introduced first, then passing after implementation.
   - Required: executable BDD gate tests pass for affected behavior paths.
4. **Deterministic Eval Gate**
   - Required: pass deterministic contracts in `evals/` and feature tests.
5. **Safety/Protocol Gate**
   - Required: no violation of security/privacy/output-hygiene/tool contracts.

### Non-Blocking Audit Gates

1. Adversarial test slices.
2. Sampled runtime-judge assessments.
3. Manual reviewer challenge sessions for eval hardening.

Audit failures create follow-up tasks and can block future promotion scopes.

## Strict SDD + BDD + TDD Workflow (Non-Optional)

For each feature:

1. **SDD first**
   - Create or update spec and OpenSpec artifacts before code.
2. **BDD second**
   - Write behavior scenarios that define expected outcomes and edge cases.
3. **TDD third**
   - Add failing tests that encode behavior and invariants.
4. **Implementation**
   - Implement minimum code to pass tests.
5. **Verification**
   - Run deterministic evals and test suites.
6. **Review + Promotion**
   - Apply blocking/non-blocking gates and rollout policy.

## Intermediate Artifact Retention Policy (Required)

To support long-running multi-agent work, intermediate outputs MUST be preserved with clear separation between tracked and local artifacts.

### Tracked Artifacts (Git, source of truth)

Store durable decisions here:

1. `openspec/changes/<change-id>/proposal.md`
2. `openspec/changes/<change-id>/design.md`
3. `openspec/changes/<change-id>/tasks.md`
4. `openspec/changes/<change-id>/specs/...`
5. `docs/specs/*.md` for stable cross-change policy/guidance
6. `evals/**` and `tests/**` for executable quality contracts

### Local Working Artifacts (May be gitignored)

Store transient work context here:

1. `tmp/proposals/` for working drafts and research notes.
2. `tmp/todo_ideas.md` (or `tmp/todos/<topic>.md`) for TODO queues.
3. `tmp/runs/evolution/` for run logs, experiment outputs, and diagnostics.

### Synchronization Rule

Any decision made in local working artifacts that affects behavior, contracts, or scope MUST be promoted into tracked artifacts before merge.

No merge is valid if only local notes contain the rationale or acceptance criteria.

## TODO Continuity Rule (Required)

To ensure seamless continuation across sessions, coding agents MUST maintain local TODO files:

1. `tmp/todos/active.md` for prioritized unfinished work.
2. `tmp/todos/handoff.md` for session handoff context and immediate next action.
3. `tmp/todos/done.md` for completed local milestones.

Agent behavior requirements:

1. At session start, read `active.md` and `handoff.md`.
2. At session end, update `handoff.md` and move completed work from `active.md` to `done.md`.
3. Prioritize unfinished P0 items from `active.md` unless user explicitly reprioritizes.
4. Promote durable TODO decisions into tracked OpenSpec/spec artifacts before merge.

## Required Definition of Done (Per Feature)

A feature is complete only if all are true:

1. Rationale section exists with numeric success/risk metrics.
2. SDD artifacts are present and approved.
3. BDD scenarios are executable and passing.
4. TDD evidence exists in commit/test history and tests pass.
5. Deterministic eval and contract checks pass.
6. Rollback trigger and ownership are documented.
7. Intermediate artifacts are archived/synced per retention policy.

## Rollout Plan For This Repository

1. **Phase 0: Governance First**
   - Apply this specification, templates, and local commit-time checks.
   - Use `scripts/run_evolution_cycle.sh` to produce deterministic local run reports in `tmp/runs/evolution/`.
   - `scripts/run_evolution_cycle.sh` MUST run `scripts/run_live_benchmark.sh` after each iteration and record failures as non-blocking soft warnings.
   - Full periodic live benchmark is optional and currently disabled by default.
   - Use `scripts/trigger_evolution.sh` to scaffold follow-up changes when a run fails.
   - Use `scripts/new_evolution_change.sh <change-id> [title]` for manual bootstrap with mandatory sections.
   - Use `scripts/generate_evolution_candidates.sh` to produce manual-assisted candidate task lists (no code changes).
2. **Phase 1: Assisted Evolution**
   - Auto-generate proposals/candidates; human approves promotions.
3. **Phase 2: Constrained Autonomy**
   - Limited self-promotion for low-risk scopes with strict guardrails.
4. **Phase 3: Expanded Autonomy**
   - Broader scope only after stable metrics and review quality.

## Feature Rationale Record: Codex-Native Skill Routing + Paper Ingest

### Why this feature

1. Active `/api/chat` runtime is `codex_sdk`, so skill execution must use codex-native capabilities to avoid policy/runtime divergence.
2. Paper workflows require durable local persistence plus key-info DB extraction for stable follow-up retrieval.

### Expected project benefit

1. Higher local-first answer quality for research/paper queries.
2. Better observability via tool timeline events in stream.
3. Lower hidden failure rate where paper data appears indexed but is not durably ingested.

### Numeric success metrics

1. `codex_native_skill_invocation_rate >= 95%` for skill-routed deterministic fixtures.
2. `paper_ingest_success_rate >= 98%` over rolling 100-ingest window.
3. `paper_key_info_schema_pass_rate >= 99%`.
4. `local_retrieval_hit_at_5 >= 85%` on ingest fixtures.

### Rollback / kill criteria

1. If tool-event contract tests fail in 2 consecutive deterministic runs: disable codex-native routing feature flag and rollback runtime parser changes.
2. If ingest failure rate exceeds 2% for 2 consecutive windows: disable ingest contract path and rollback to previous stable ingest behavior.
3. If `/api/chat` error-finish rate increases by more than 2% over baseline window: pause rollout and rollback latest runtime changes.

## Feature Rationale Record: Skill-Triggered Paper Auto-Ingest (Fallback Default-Off)

### Why this feature

1. Text-mention fallback (`assistant` output contains arXiv id) can create false-positive ingest writes.
2. Skill event is the authoritative runtime signal; default behavior should follow explicit tool invocation.

### Expected project benefit

1. Lower accidental paper ingest writes.
2. Clearer observability and deterministic debugging path (`tool-input-available` -> ingest).
3. Stronger regression detection through BDD/TDD.

### Numeric success metrics

1. `fallback_ingest_default_invocations = 0`.
2. `skill_triggered_ingest_invocation_rate = 100%` on BDD fixtures.
3. `bdd_tdd_pass_rate = 100%` for AGT-20/21/22 test set.

### Rollback / kill criteria

1. If skill-triggered ingest extraction tests fail in 2 consecutive runs, rollback to previous stable `/api/chat` ingest trigger logic.
2. If production trigger rate drops below 95% due to runtime event drift, temporarily enable `ENABLE_PAPER_TEXT_MENTION_FALLBACK=true` and open follow-up fix change.

## Source References

This specification is aligned with:

1. AlphaEvolve architecture principles for iterative code evolution and evaluator-driven selection.
2. AI-resistant and system-level agent evaluation practices.
3. Deterministic-first evaluation policies already adopted in this repository.

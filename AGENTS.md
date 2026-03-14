# Agent Guidelines

This file defines repository-level standards for coding agents.

## Evaluation Standard (Mandatory)

For any change that affects agent behavior, prompting, retrieval, tool usage, or eval code:

1. Follow `/Users/bytedance/code/anti-demo/docs/specs/agent-evaluation-standard.md`.
2. Use deterministic-first evaluation design.
3. Keep evals flexible with outcome-based multi-oracle acceptance.
4. Minimize runtime LLM judgment and keep it non-blocking for PR/nightly.

## Auto-Evolving Backend Governance (Mandatory)

For any feature work, especially agent behavior, retrieval/tooling, evaluation, or auto-evolving flows:

1. Follow `/Users/bytedance/code/anti-demo/docs/specs/auto-evolving-backend.md`.
2. Include explicit feature rationale:
   - why this feature is added
   - expected project benefit
   - numeric success metrics
   - rollback/kill criteria
3. Enforce strict order: SDD -> BDD -> TDD -> implementation -> deterministic verification.
4. Apply the same workflow to auto-evolving-system changes themselves.

## Intermediate Artifact Retention (Mandatory)

Agents must preserve intermediate results so future agent runs can continue reliably.

1. Persist durable decisions in tracked artifacts:
   - `openspec/changes/<change-id>/proposal.md`
   - `openspec/changes/<change-id>/design.md`
   - `openspec/changes/<change-id>/tasks.md`
   - `openspec/changes/<change-id>/specs/...`
   - `docs/specs/*.md` for cross-change policies
2. Store local working context in:
   - `tmp/proposals/`
   - `tmp/todo_ideas.md` or `todos/*.md`
   - `tmp/runs/evolution/` for logs/diagnostics
3. Before merge, promote any behavior-affecting decisions from local notes into tracked artifacts.
4. Do not leave critical rationale or acceptance criteria only in ephemeral agent messages.

## TODO Management Rule (Mandatory)

Coding agents must maintain local TODO continuity files for every implementation session.

1. Required local files:
   - `/Users/bytedance/code/anti-demo/todos/active.md`
   - `/Users/bytedance/code/anti-demo/todos/handoff.md`
   - `/Users/bytedance/code/anti-demo/todos/done.md`
2. Session-start requirement:
   - Read `todos/active.md` and `todos/handoff.md` before making new plans.
3. Session-end requirement:
   - Update `todos/handoff.md` with current state and immediate next task.
   - Move completed items from `todos/active.md` to `todos/done.md`.
4. Priority rule:
   - If `active.md` has unfinished P0 items, agents should execute those first unless the user explicitly overrides.
5. Sync rule:
   - Any local TODO item that becomes a durable requirement must be promoted into tracked OpenSpec/spec artifacts before merge.

## When Updating Customized Prompt Paths

If a change touches any custom prompt/agent path, update:

1. Path coverage and requirements in `/Users/bytedance/code/anti-demo/docs/specs/agent-evaluation-standard.md`.
2. The corresponding eval tasks and fixtures.
3. Any impacted proposal document in `/Users/bytedance/code/anti-demo/tmp/proposals/`.

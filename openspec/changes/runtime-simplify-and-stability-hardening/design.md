## Context

`backend/agent.py` currently combines auth checks, request payload preparation, streaming parse, tool orchestration, and retry/error handling in one large method. `start-dev.sh` already cleans listeners but lacks deterministic post-start verification loop. Metric strictness remains proxy-heavy without a stable weekly export utility.

## Goals / Non-Goals

**Goals:**
- simplify bridge runtime internals without API behavior change
- enforce auth preflight + timeout/retry + error envelope consistency
- make listener lifecycle deterministic and verifiable
- provide stricter parser-backed metric checks and weekly trend export

**Non-Goals:**
- no provider/platform migration
- no blocking runtime judge in CI

## Decisions

1. Keep external response contract fixed while extracting helper methods in `MainAgent`.
2. Use bounded retry for transient 5xx/timeouts only.
3. Keep listener checks deterministic and script-only (no new daemon dependencies).
4. Export trend metrics to versioned JSON/markdown under `tmp/interview_pack/reports/weekly/`.

## Risks / Trade-offs

- [Risk] refactor may introduce subtle stream regressions -> Mitigation: add stream contract tests and run deterministic gates.
- [Risk] retries may increase tail latency -> Mitigation: low retry count with strict timeout and warning output.

## Rollback Plan

1. Trigger:
   - stream contract failures
   - latency regression threshold breach
2. Steps:
   - revert runtime simplification commit block
   - disable retry wrapper via env flag fallback
3. Validation:
   - run deterministic eval + BDD stream tests + listener sanity script

## Ownership

1. Owner: runtime/backend maintainer
2. Reviewer: eval/governance maintainer
3. Oncall: repo oncall for rollback command execution

## Metrics Instrumentation

1. Metric: `bridge_runtime_error_rate`
   - Source: benchmark reports + error envelope counts
   - Threshold: warn > 1 per 100 requests
   - Window: latest 2 runs

2. Metric: `listener_sanity_pass_rate`
   - Source: restart sanity script output
   - Threshold: must equal 1.0
   - Window: 10 restart loop

3. Metric: `weekly_trend_export_completeness`
   - Source: weekly export artifact check
   - Threshold: required fields completeness = 1.0
   - Window: weekly

## Evolution Run Context

- Linked run index: `tmp/runs/evolution/index.md`
- Linked run report: `tmp/runs/evolution/<timestamp>.md`

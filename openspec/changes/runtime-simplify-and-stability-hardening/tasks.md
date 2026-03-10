## 1. Implementation Tasks

- [x] 1.1 Refactor bridge runtime into helper methods while preserving behavior
- [x] 1.2 Add bounded timeout/retry + error envelope consistency
- [x] 1.3 Harden `start-dev` listener lifecycle with deterministic sanity pass
- [x] 1.4 Add parser-backed metric strictness checks
- [x] 1.5 Add weekly trend export script and sample report output
- [x] 1.6 Add deterministic tests for runtime/listener/metrics helpers
- [x] 1.7 Produce acceptance report in change path

## BDD Evidence

Document executable behavior scenarios.

1. Given bridge auth and endpoint are configured.
2. When `/api/chat` executes under normal and transient failure conditions.
3. Then runtime preserves stream contract, retries only transient failures, and returns consistent error envelope on failure.

1. Given repeated local start/restart attempts.
2. When `start-dev` and sanity checks run.
3. Then exactly one listener exists per expected port after each cycle.

## TDD Evidence

Document the red-green-refactor trace.

1. Failing tests introduced for runtime helper behavior, listener sanity loop, and metric strictness parser checks.
2. Implemented minimal refactor/hardening code and scripts to satisfy tests.
3. Passing verification:
   - runtime + eval deterministic tests pass
   - listener sanity check script passes
   - weekly export artifact generated

## Evolution Run Context

- Linked run index: `tmp/runs/evolution/index.md`
- Linked run report: `tmp/runs/evolution/<timestamp>.md`

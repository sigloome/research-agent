## MODIFIED Requirements

### Requirement: Skill Execution Path MUST Align With Active Runtime
Project skill execution in production chat flow SHALL use active codex-native runtime capabilities rather than inactive legacy bridge-only paths.

#### Scenario: active runtime invokes skills natively
- **WHEN** backend runs with configured active runtime
- **THEN** skill invocations occur through codex-native tool capabilities
- **AND** no bridge-only fallback path is required for normal operation

### Requirement: Skill Contracts MUST Be Deterministically Verifiable
Skill routing and execution contracts SHALL be validated by deterministic tests for discovery, invocation, output shape, and error envelopes.

#### Scenario: deterministic suite validates skill contract
- **WHEN** CI deterministic suite runs
- **THEN** tests verify required skill availability and invocation traces
- **AND** tests verify output schema and failure envelope invariants
- **AND** failure blocks release gates for contract regressions

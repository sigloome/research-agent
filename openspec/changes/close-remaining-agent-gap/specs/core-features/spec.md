## MODIFIED Requirements

### Requirement: Decoupled Answer Stage

The runtime MUST execute answer synthesis as an explicit answer stage with typed handoff contract and verifier gate context, rather than implicit inline prompt assembly only.

#### Scenario: Answer stage uses validated envelopes

- **GIVEN** retrieval/preference/verifier handoffs are complete
- **WHEN** answer stage begins
- **THEN** answer context is produced from typed envelopes and verifier summary
- **AND** answer-stage envelope is included in runtime output for observability

### Requirement: Promotion Workflow Automation (Non-Blocking)

The repository MUST provide scriptable local promotion workflow stages (`sandbox`, `shadow`, `canary`) with rollback command templates and warning thresholds.

#### Scenario: Promotion script produces warning/rollback plan

- **GIVEN** deterministic gates pass and benchmark metrics are available
- **WHEN** promotion workflow script runs
- **THEN** stage-by-stage report is produced with warning thresholds and rollback commands
- **AND** threshold breach emits non-blocking warning record for manual approval

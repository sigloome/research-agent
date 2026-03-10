## MODIFIED Requirements

### Requirement: Per-Agent Stream Trace Events

The chat stream MUST expose per-agent trace events in addition to unified UI-message chunks so runtime stage ownership is observable.

#### Scenario: Emit per-agent trace around runtime stages

- **GIVEN** a `/api/chat` request enables `runtime_profile`
- **WHEN** orchestrator/retrieval/preference/verifier/answer stages execute
- **THEN** stream emits `agent-trace` events with `trace_id`, `role`, `stage`, `status`, and `latency_ms`
- **AND** existing `text-delta/tool-input/tool-output/finish/[DONE]` contract remains backward compatible

### Requirement: Soft Threshold Alert Events

Live benchmark and runtime quality checks MUST support non-blocking threshold alerts.

#### Scenario: Soft warning emitted without blocking response

- **GIVEN** a quality/risk metric breaches configured warning threshold
- **WHEN** request/benchmark finishes
- **THEN** a warning event/report entry is generated with metric name, observed value, and threshold
- **AND** runtime request still completes (`finishReason=stop`) unless hard failure condition is met

## ADDED Requirements

### Requirement: Active Runtime SHALL Use Codex-Native Skill Invocation
The active `/api/chat` execution path SHALL invoke project skills through codex-native tool capabilities in `codex_sdk` runtime for skill-routed queries.

#### Scenario: skill-routed query invokes codex-native capability
- **WHEN** user query matches skill-routed policy
- **THEN** runtime emits at least one codex-native skill/tool invocation in the same turn
- **AND** assistant response is generated after tool result is available

### Requirement: Skill Invocation Observability SHALL Be Streamed
The system SHALL expose codex-native skill/tool execution lifecycle through UI SSE events that preserve existing frontend parser contracts.

#### Scenario: tool lifecycle is visible in stream
- **WHEN** a codex-native skill/tool call starts and completes
- **THEN** stream includes `tool-input-start` and `tool-input-available`
- **AND** stream includes `tool-output-available` with completion payload
- **AND** stream terminates with standard finish boundaries

### Requirement: Skill Routing Failure SHALL Produce Structured Errors
If required codex-native skill invocation cannot be completed, runtime SHALL emit structured error envelopes and error finish reason.

#### Scenario: codex-native invocation fails
- **WHEN** codex-native skill/tool call returns failure
- **THEN** stream includes `error` with diagnostic text
- **AND** final finish reason is `error`
- **AND** stream still terminates deterministically

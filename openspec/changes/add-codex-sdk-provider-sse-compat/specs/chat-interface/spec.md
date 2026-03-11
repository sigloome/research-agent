## MODIFIED Requirements

### Requirement: Response Streaming
The system SHALL preserve the existing UI SSE stream contract for `/api/chat` with the single runtime provider (`codex_sdk`).

#### Scenario: codex_sdk provider preserves UI stream contract
- **GIVEN** backend runs with `AGENT_PROVIDER=codex_sdk`
- **WHEN** client sends `POST /api/chat`
- **THEN** stream contains UI message events with ordered start/text/finish boundaries
- **AND** stream terminates with `data: [DONE]`

#### Scenario: codex_sdk provider failure emits structured error
- **GIVEN** backend runs with `AGENT_PROVIDER=codex_sdk`
- **AND** codex runtime exits with an error
- **WHEN** client sends `POST /api/chat`
- **THEN** stream contains an `error` event with diagnostic text
- **AND** final event includes `finishReason=error`
- **AND** stream terminates with `data: [DONE]`

### Requirement: Chat Transport Compatibility
Frontend transport behavior SHALL remain compatible without request/response schema changes under single-provider runtime.

#### Scenario: single provider does not require frontend protocol change
- **GIVEN** frontend uses `DefaultChatTransport` against `/api/chat`
- **WHEN** backend runs on codex_sdk provider
- **THEN** assistant responses remain renderable
- **AND** chat status transitions still complete normally

## MODIFIED Requirements

### Requirement: Chat Streaming MUST Include Skill Tool Timeline
The chat stream SHALL include codex-native skill/tool lifecycle events compatible with current UI message stream parsing.

#### Scenario: skill execution timeline is rendered
- **WHEN** assistant executes a codex-native skill/tool call
- **THEN** stream contains `tool-input-start` and `tool-input-available` events
- **AND** stream contains `tool-output-available` for the same tool call id
- **AND** message stream remains parseable by existing frontend transport

### Requirement: Stream Completion Contract MUST Remain Stable
The chat stream SHALL preserve completion boundaries (`finish` and `[DONE]`) even when skill/tool execution errors occur.

#### Scenario: tool failure still respects completion protocol
- **WHEN** a codex-native skill/tool call fails during chat turn
- **THEN** stream includes structured `error` payload
- **AND** emits `finish` with `finishReason=error`
- **AND** emits terminal `[DONE]` marker

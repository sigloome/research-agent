## ADDED Requirements

### Requirement: UI message stream protocol header
The `/api/chat` endpoint SHALL return SSE responses with `Content-Type: text/event-stream` and `x-vercel-ai-ui-message-stream: v1`.

#### Scenario: Stream response headers
- **WHEN** a client sends `POST /api/chat`
- **THEN** the response content type is `text/event-stream`
- **THEN** the response includes header `x-vercel-ai-ui-message-stream: v1`

### Requirement: Streaming completion sentinel
The chat stream SHALL terminate with a `[DONE]` SSE data frame after the assistant turn completes.

#### Scenario: End-of-stream marker
- **WHEN** the assistant finishes a response
- **THEN** the stream includes `data: [DONE]`
- **THEN** no further content frames are emitted for that turn

### Requirement: Accessible live transcript
The chat transcript SHALL expose an accessible live log for incremental assistant updates.

#### Scenario: Screen reader live updates
- **WHEN** assistant text is streamed to the UI
- **THEN** new content is announced through a polite live region/log role
- **THEN** controls remain keyboard accessible during streaming

### Requirement: Status-driven chat controls
The chat UI SHALL provide stop, retry/regenerate, and edit+resend actions through transport status state.

#### Scenario: Stop streaming response
- **WHEN** a response is actively streaming
- **THEN** the user can stop generation
- **THEN** the UI transitions out of streaming state without crashing

#### Scenario: Retry assistant response
- **WHEN** a response fails or completes undesirably
- **THEN** the user can retry/regenerate from the active conversation context

#### Scenario: Edit and resend message
- **WHEN** a user edits a prior user message
- **THEN** the edited message is resent and a new assistant response is streamed

## MODIFIED Requirements

### Requirement: Response Streaming
The system SHALL stream assistant output as SSE data events compatible with the Vercel UI message stream contract and SHALL render partial output incrementally.

#### Scenario: Stream text parts incrementally
- **WHEN** the assistant produces text output
- **THEN** the backend emits ordered text-related stream parts in SSE data frames
- **THEN** the frontend appends visible text incrementally without duplicating content

#### Scenario: Stream includes start and finish boundaries
- **WHEN** a turn begins and ends
- **THEN** the stream emits explicit turn start and finish events
- **THEN** the frontend status transitions from submitted/streaming to ready

### Requirement: Tool Execution Display
The interface SHALL render a tool-progress timeline from structured streamed tool parts rather than custom line-prefix parsing.

#### Scenario: Tool step appears in timeline
- **WHEN** the backend emits tool-progress parts for a step
- **THEN** the UI shows a timeline entry with tool label and state
- **THEN** timeline entries persist for the turn until completion

#### Scenario: Tool timeline completion
- **WHEN** the stream emits turn completion
- **THEN** active tool indicators are finalized and no stale running state remains

### Requirement: Error Handling
The interface SHALL provide recoverable stream error behavior with user-visible status and retry capability.

#### Scenario: Network or stream parse failure
- **WHEN** the stream fails during a turn
- **THEN** the UI shows an error state for the turn
- **THEN** retry controls are available without requiring full page reload

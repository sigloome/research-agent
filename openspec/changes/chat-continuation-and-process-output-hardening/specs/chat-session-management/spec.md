## MODIFIED Requirements

### Requirement: Persist Chat Messages
The system SHALL persist all user messages and final assistant responses for a chat session, and SHALL persist runtime continuation metadata separately from the transcript.

#### Scenario: Runtime state saved for continued historical chat
- **WHEN** a chat turn completes and the provider reports a thread identifier
- **THEN** the system stores that provider thread identifier against the chat session
- **THEN** transcript message persistence remains unchanged

### Requirement: Continue Historical Chat Sessions
The system SHALL allow a user to open an existing persisted chat session and continue asking follow-up questions with runtime continuity when available.

#### Scenario: Resume a valid provider thread
- **GIVEN** an existing chat session with persisted transcript and a valid stored provider thread id
- **WHEN** the user sends a new message in that chat
- **THEN** the system resumes the stored provider thread for the new turn
- **THEN** the new assistant response is persisted in the same chat transcript

#### Scenario: Fallback to transcript replay when provider thread is invalid
- **GIVEN** an existing chat session with persisted transcript and an invalid stored provider thread id
- **WHEN** the user sends a new message in that chat
- **THEN** the system retries the turn using transcript replay without the invalid provider thread id
- **THEN** the system updates runtime state with the fresh provider thread id when available

## ADDED Requirements

### Requirement: Chat message persistence
The system SHALL persist both user and assistant messages to the database when processing chat requests.

#### Scenario: User message saved
- **WHEN** a user sends a message in a chat session
- **THEN** the message is saved to the database with role="user"

#### Scenario: Assistant response saved  
- **WHEN** the assistant completes a streaming response
- **THEN** the full accumulated response is saved to the database with role="assistant"

### Requirement: Chat history retrieval
The system SHALL return all persisted messages when a chat session is selected.

#### Scenario: Switch to existing chat
- **WHEN** user selects a previously used chat from the sidebar
- **THEN** all messages (user and assistant) for that chat are displayed in chronological order

#### Scenario: Continue conversation
- **WHEN** user sends a new message in a previously used chat
- **THEN** the new message is appended to the existing history and the assistant response is persisted

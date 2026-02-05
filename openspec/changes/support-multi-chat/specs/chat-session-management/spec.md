## ADDED Requirements

### Requirement: Create Chat Session
The system SHALL allow creating a new empty chat session with a unique identifier and an optional title.

#### Scenario: User creates new chat
- **WHEN** user requests to create a new chat
- **THEN** system generates a unique chat ID
- **THEN** system creates a new chat record in the database
- **THEN** system returns the chat details

### Requirement: List Chat Sessions
The system SHALL allow listing all chat sessions for the current user (or global if single-user), ordered by creation time or last update.

#### Scenario: User views chat list
- **WHEN** user requests the list of chats
- **THEN** system returns a list of all existing chats with their IDs and titles

### Requirement: Persist Chat Messages
The system SHALL persist all user messages and agent responses (including tool usage) to the database associated with a specific chat session.

#### Scenario: User sends a message
- **WHEN** user sends a message in a chat session
- **THEN** system saves the user message to the database linked to the chat ID
- **THEN** system generates a response
- **THEN** system saves the agent response to the database linked to the chat ID

### Requirement: Retrieve Chat History
The system SHALL allow retrieving the full message history for a specific chat session, preserving the order and role (user/assistant) of each message.

#### Scenario: User opens a chat
- **WHEN** user requests history for a valid chat ID
- **THEN** system returns all messages belonging to that chat in chronological order

### Requirement: Delete Chat Session
The system SHALL allow deleting a chat session and all its associated messages.

#### Scenario: User deletes a chat
- **WHEN** user requests to delete a specific chat
- **THEN** system removes the chat record and all associated messages from the database

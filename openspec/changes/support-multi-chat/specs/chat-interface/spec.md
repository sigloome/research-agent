## ADDED Requirements

### Requirement: Chat Sidebar
The interface SHALL display a sidebar listing available chat sessions and a "New Chat" button.

#### Scenario: Sidebar display
- **WHEN** user views the chat interface
- **THEN** a sidebar is visible showing a list of past chats
- **THEN** a "New Chat" button is available at the top/bottom of the lists

### Requirement: Session Switching
The interface SHALL allow users to switch between chat sessions by clicking on them in the sidebar.

#### Scenario: Switch to existing chat
- **WHEN** user clicks on a chat from the sidebar
- **THEN** the main chat view clears current messages
- **THEN** the message history for the selected chat is loaded and displayed
- **THEN** new messages sent will be associated with this chat ID

#### Scenario: Switch to new chat
- **WHEN** user clicks "New Chat"
- **THEN** a new chat session is created on the backend
- **THEN** the main chat view is cleared
- **THEN** the new session is active

## MODIFIED Requirements

### Requirement: Message Sending
- Text input for user messages
- Send button and Enter key
- Disable during processing
- **Include active session ID in the API request**

#### Scenario: Send message
- **WHEN** user enters text and clicks Send
- **THEN** message is displayed in UI immediately
- **THEN** message is sent to backend **with the current session ID**
- **THEN** input field is cleared
- **THEN** send button is disabled

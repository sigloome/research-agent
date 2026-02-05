# Chat Interface Specification

## Overview

AI chat interface with streaming responses and tool execution feedback.

## Requirements

### Functional Requirements

1. **Message Sending**
   - Text input for user messages
   - Send button and Enter key
   - Disable during processing

2. **Response Streaming**
   - Stream tokens as received
   - Display partial responses
   - Show thinking/processing state

3. **Tool Execution Display**
   - Show tool usage in collapsible section
   - Human-readable tool descriptions
   - Progress indication

4. **Paper Context**
   - "Ask about this paper" button
   - Pre-filled question template
   - Suggested questions based on paper

5. **Preference Integration**
   - Load user preferences
   - Show personalized suggestions
   - Track new queries

### Non-Functional Requirements

1. **Performance**
   - Stream latency < 100ms per chunk
   - Smooth scrolling during streaming
   - No UI freezing

2. **Usability**
   - Clear loading states
   - Error messages for failures
   - Responsive design

## User Interface

### Chat Panel
```
┌─────────────────────────────────┐
│ [Expand/Collapse]               │
├─────────────────────────────────┤
│ [Suggestion Buttons]            │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ User: Query...              │ │
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Agent Process (collapsible) │ │
│ │ - Using skill to search...  │ │
│ │ - Running Bash command...   │ │
│ │                             │ │
│ │ Response markdown here...   │ │
│ └─────────────────────────────┘ │
│                                 │
├─────────────────────────────────┤
│ [Paper Context Banner]          │
│ [Input] [Send]                  │
└─────────────────────────────────┘
```

### Paper Context Banner
- Shows when asking about specific paper
- Displays paper title
- Clear button to remove context
- Suggested questions

## API Specification

### Chat Endpoint
```
POST /api/chat
Content-Type: application/json

Request: {
  "message": "Find papers about LLM",
  "paper_context": {
    "id": "2401.12345",
    "title": "Paper Title",
    "abstract": "..."
  }
}

Response: text/event-stream
data: {"type": "text", "content": "I'll search..."}
data: {"type": "tool", "name": "fetch_papers", "description": "Searching ArXiv for LLM papers"}
data: {"type": "text", "content": "Found 5 papers..."}
data: {"type": "done"}
```

### Preferences Endpoint
```
GET /api/preferences

Response: {
  "preferences": {...},
  "suggestions": ["Question 1?", "Question 2?"]
}
```

## State Management

### Message State
```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}
```

### Paper Context State
```typescript
interface PaperContext {
  id: string;
  title: string;
  abstract: string;
  authors: string[];
}
```

## Critical Implementation Notes

### React State Updates
**CRITICAL**: Never mutate state directly. Always create new objects:

```typescript
// WRONG - causes rendering issues
setMessages(prev => {
  prev[prev.length - 1].content += chunk;
  return prev;
});

// CORRECT - creates new object
setMessages(prev => {
  const updated = [...prev];
  const lastMsg = updated[updated.length - 1];
  updated[updated.length - 1] = {
    ...lastMsg,
    content: lastMsg.content + chunk
  };
  return updated;
});
```

### Streaming Handler
- Use `fetch` with streaming reader
- Process chunks incrementally
- Handle connection errors gracefully

## Test Cases

1. **Send Message**
   - Message appears in chat
   - Input clears after send
   - Button disables during send

2. **Stream Response**
   - Tokens appear incrementally
   - No duplication of content
   - Proper markdown rendering

3. **Tool Display**
   - Tool usage shown in process section
   - Human-readable descriptions
   - Collapsible section works

4. **Paper Context**
   - Context banner appears
   - Suggestions shown
   - Context included in message

5. **Error Handling**
   - Network error shown to user
   - Retry possible after error
   - State remains consistent

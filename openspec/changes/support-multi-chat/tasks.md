## 1. Database & Backend Core

- [x] 1.1 Update `DatabaseManager` to initialize `chats` and `messages` tables <!-- file: skills/knowledge/db/manager.py -->
- [x] 1.2 Implement `create_chat`, `list_chats`, `delete_chat` methods in manager
- [x] 1.3 Implement `save_message` and `get_chat_history` methods in manager

## 2. API Implementation
- [x] 2.1 Add `Chat` and `Message` Pydantic models in `backend/app.py`
- [x] 2.2 Implement `GET /api/chats` endpoint
- [x] 2.3 Implement `POST /api/chats` endpoint
- [x] 2.4 Implement `DELETE /api/chats/{chat_id}` endpoint
- [x] 2.5 Implement `GET /api/chats/{chat_id}` endpoint

## 3. Core Chat Integration

- [x] 3.1 Update `POST /api/chat` to accept `session_id` (already done partially, verify)
- [x] 3.2 Update `POST /api/chat` to save User message to DB
- [x] 3.3 Update `POST /api/chat` to accumulate and save Assistant response to DB

## 4. Frontend Implementation

- [x] 4.1 Create `ChatSidebar` component <!-- file: frontend/src/components/ChatSidebar.tsx -->
- [x] 4.2 Update `ChatInterface` layout to include Sidebar
- [x] 4.3 Add state for `currentChatId` and `chatList`
- [x] 4.4 Implement "New Chat" button logic
- [x] 4.5 Implement chat switching logic (fetch history)
- [x] 4.6 Implement deletion of chats
- [x] 4.7 Refine Sidebar UI (Consistency & Collapsible)
- [x] 4.8 Browser Verification of UI Changes

## 5. Verification & Testing

- [ ] 5.1 Add Unit Tests for DatabaseManager (`tests/test_db_manager.py`)
- [ ] 5.2 Add Unit Tests for Backend API (`tests/test_api_chats.py`)
- [x] 5.3 Add E2E Tests for Chat Flows (`frontend/tests/chat.spec.ts`) - **Verified Deletion & Layout**
- [x] 5.4 Manual Browser Verification (Creation, Switching, Persistence)

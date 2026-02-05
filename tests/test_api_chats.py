
import pytest
from fastapi.testclient import TestClient
from backend.app import app
from skills.knowledge.db import manager

@pytest.fixture
def client(temp_db):
    """Create a TestClient with a temporary database."""
    original_path = manager.DB_PATH
    manager.DB_PATH = temp_db
    
    # Initialize DB (create tables)
    manager.init_db()
    
    # MOCK AGENT to prevent real SDK connection
    from unittest.mock import AsyncMock, MagicMock
    from backend import app as backend_app
    
    # Mock initialize to prevent real connection
    backend_app.agent.initialize = AsyncMock()
    
    # Mock client on agent so it doesn't fail checks
    backend_app.agent.client = MagicMock()
    
    with TestClient(app) as client:
        yield client
        
    manager.DB_PATH = original_path

def test_api_create_chat(client):
    response = client.post("/api/chats", json={"title": "New API Chat"})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "New API Chat"
    
def test_api_list_chats(client):
    # Create two chats
    client.post("/api/chats", json={"title": "Chat 1"})
    client.post("/api/chats", json={"title": "Chat 2"})
    
    response = client.get("/api/chats")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    titles = [chat["title"] for chat in data]
    assert "Chat 1" in titles
    assert "Chat 2" in titles

def test_api_get_chat_history_and_persistence(client):
    # 1. Create a chat manually via API to get ID
    create_res = client.post("/api/chats", json={"title": "History Test"})
    chat_id = create_res.json()["id"]
    
    # 2. Send a message using /api/chat with session_id
    # Note: /api/chat currently expects a complicated ChatRequest 
    # and mocks the agent response via streaming. 
    # We can test persistence by mocking the agent or just checking user message persistence.
    # But since /api/chat implementation relies on `agent`, which might need mocking
    # let's just test that the input is accepted and user message is saved.
    
    # We might need to mock `agent.chat_generator` to avoid actual calls.
    # But for now let's try a simple call.
    
    # Actually, `agent` is global in app.py. We should patch it.
    from backend import app as backend_app
    
    # Mock the generator
    async def mock_generator(*args, **kwargs):
        yield "data: {\"type\": \"content\", \"content\": \"Mock Response\"}\n\n"
        yield "data: [DONE]\n\n"
        
    backend_app.agent.chat_generator = mock_generator

    chat_req = {
        "message": "Hello API",
        "session_id": chat_id
    }
    
    # Send message
    response = client.post("/api/chat", json=chat_req)
    assert response.status_code == 200
    
    # Consume stream to trigger persistence
    content = response.content
    assert b"Mock Response" in content
    
    # 3. Check history via GET /api/chats/{chat_id}
    hist_res = client.get(f"/api/chats/{chat_id}")
    assert hist_res.status_code == 200
    history = hist_res.json()
    
    # Should have User message and Assistant message
    assert len(history) >= 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello API"
    assert history[-1]["role"] == "assistant"
    # The saved assistant message comes from the stream accumulator
    assert history[-1]["content"] == "Mock Response"

def test_api_delete_chat(client):
    # Create chat
    create_res = client.post("/api/chats", json={"title": "Delete Me"})
    chat_id = create_res.json()["id"]
    
    # Delete it
    del_res = client.delete(f"/api/chats/{chat_id}")
    assert del_res.status_code == 200
    
    # Verify 404 on get history
    get_res = client.get(f"/api/chats/{chat_id}")
    assert get_res.status_code == 404

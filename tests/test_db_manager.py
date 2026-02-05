import pytest
import sqlite3
import os
from skills.knowledge.db import manager

@pytest.fixture
def mock_db_path(temp_db):
    """Override manager.DB_PATH with temp database."""
    original_path = manager.DB_PATH
    manager.DB_PATH = temp_db
    yield temp_db
    manager.DB_PATH = original_path

def test_create_list_delete_chat(mock_db_path):
    # Test Create
    chat_id = manager.create_chat("Test Chat")
    assert chat_id is not None
    
    # Test Get
    chat = manager.get_chat(chat_id)
    assert chat is not None
    assert chat['title'] == "Test Chat"
    
    # Test List
    chats = manager.list_chats()
    assert len(chats) == 1
    assert chats[0]['id'] == chat_id
    
    # Test Delete
    success = manager.delete_chat(chat_id)
    assert success is True
    
    # Verify Deletion
    chat = manager.get_chat(chat_id)
    assert chat is None
    chats = manager.list_chats()
    assert len(chats) == 0

def test_message_persistence(mock_db_path):
    chat_id = manager.create_chat("Message Test")
    
    # Save User Message
    manager.save_message(chat_id, "user", "Hello AI")
    
    # Save Assistant Message
    manager.save_message(chat_id, "assistant", "Hello User")
    
    # Get History
    messages = manager.get_chat_history(chat_id)
    assert len(messages) == 2
    
    # Check Ordering and Content
    assert messages[0]['role'] == 'user'
    assert messages[0]['content'] == 'Hello AI'
    assert messages[1]['role'] == 'assistant'
    assert messages[1]['content'] == 'Hello User'

def test_delete_chat_cascades_messages(mock_db_path):
    chat_id = manager.create_chat("Cascade Test")
    manager.save_message(chat_id, "user", "Message 1")
    
    # Verify message exists
    messages = manager.get_chat_history(chat_id)
    assert len(messages) == 1
    
    # Delete Chat
    manager.delete_chat(chat_id)
    
    # Verify messages deleted (by checking raw DB or empty history if chat recreated, 
    # but here we can check directly via sqlite if we want, or just rely on get_chat_history returning empty if we query by old ID? 
    # Actually get_chat_history filters by chat_id. Let's inspect DB directly to be sure.)
    
    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM messages WHERE chat_id = ?", (chat_id,))
    count = cursor.fetchone()[0]
    conn.close()
    
    assert count == 0

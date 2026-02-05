"""
Pytest configuration and fixtures for the test suite.
"""
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Initialize with schema matching skills/db/manager.py
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    # Library sources table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS library_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            source_type TEXT NOT NULL,
            config TEXT,
            description TEXT,
            icon TEXT,
            enabled INTEGER DEFAULT 1,
            created_at TEXT
        )
    ''')
    
    # Papers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY,
            title TEXT,
            authors TEXT,
            published_date TEXT,
            url TEXT,
            abstract TEXT,
            citation_count INTEGER,
            last_metadata_update TEXT,
            tags TEXT,
            summary_main_ideas TEXT,
            summary_methods TEXT,
            summary_results TEXT,
            summary_limitations TEXT,
            content_source TEXT,
            full_text_local_path TEXT,
            source_id INTEGER,
            created_at TEXT,
            FOREIGN KEY (source_id) REFERENCES library_sources(id)
        )
    ''')
    
    # Books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            title TEXT,
            authors TEXT,
            publisher TEXT,
            year TEXT,
            language TEXT,
            format TEXT,
            file_size TEXT,
            pages INTEGER,
            isbn TEXT,
            description TEXT,
            cover_url TEXT,
            download_url TEXT,
            local_path TEXT,
            processed_text_path TEXT,
            zlibrary_id TEXT,
            source_id INTEGER,
            tags TEXT,
            created_at TEXT,
            FOREIGN KEY (source_id) REFERENCES library_sources(id)
        )
    ''')
    
    # User queries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text TEXT NOT NULL,
            query_type TEXT,
            topics TEXT,
            created_at TEXT
        )
    ''')
    
    # User preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preference_type TEXT NOT NULL,
            value TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            created_at TEXT
        )
    ''')

    # Chats table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
        )
    ''')
    
    # Insert default source
    cursor.execute('''
        INSERT INTO library_sources (name, source_type, icon, description, enabled, created_at)
        VALUES ('ArXiv', 'arxiv', '📄', 'ArXiv preprint server', 1, datetime('now'))
    ''')
    
    conn.commit()
    conn.close()
    
    yield path
    
    # Cleanup
    os.unlink(path)


@pytest.fixture
def mock_arxiv_response():
    """Mock ArXiv API response."""
    return {
        "entries": [
            {
                "id": "2401.12345",
                "title": "Test Paper Title",
                "authors": ["Author One", "Author Two"],
                "abstract": "This is a test abstract about LLM and transformers.",
                "published": "2024-01-15T00:00:00Z",
                "url": "https://arxiv.org/abs/2401.12345",
                "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf"
            }
        ]
    }


@pytest.fixture
def sample_paper():
    """Return a sample paper dictionary."""
    return {
        "id": "2401.12345",
        "title": "Test Paper: Large Language Models and Reasoning",
        "authors": '["Alice Smith", "Bob Johnson"]',
        "abstract": "We present a novel approach to LLM reasoning using chain of thought...",
        "published_date": "2024-01-15T00:00:00Z",
        "url": "https://arxiv.org/abs/2401.12345",
        "citation_count": 42,
        "tags": '["LLM", "reasoning"]',
        "summary_main_ideas": "This paper explores chain of thought reasoning..."
    }


@pytest.fixture
def sample_book():
    """Return a sample book dictionary."""
    return {
        "id": "book-12345",
        "title": "Machine Learning: A Probabilistic Perspective",
        "authors": '["Kevin Murphy"]',  # JSON array format
        "publisher": "MIT Press",
        "year": "2012",
        "language": "English",
        "format": "pdf",
        "file_size": "25 MB",
        "pages": 1104,
        "isbn": "978-0262018029",
        "description": "A comprehensive introduction to machine learning...",
        "zlibrary_id": "12345678"
    }

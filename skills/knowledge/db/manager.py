import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

# Database is stored in data/ directory
# skills/db/manager.py -> parent.parent.parent = project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_NAME = os.getenv("DB_NAME", "papers.db")
DB_PATH = str(DATA_DIR / DB_NAME)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Library sources table - supports multiple sources (ArXiv, local files, custom URLs, etc.)
    c.execute('''
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
    
    # Insert default sources if not exist
    c.execute('''
        INSERT OR IGNORE INTO library_sources (name, source_type, config, description, icon, enabled, created_at)
        VALUES ('ArXiv', 'arxiv', '{"base_url": "http://export.arxiv.org/api/query"}', 'ArXiv preprint server', '📄', 1, datetime('now'))
    ''')
    c.execute('''
        INSERT OR IGNORE INTO library_sources (name, source_type, config, description, icon, enabled, created_at)
        VALUES ('Z-Library', 'zlibrary', '{"type": "mcp"}', 'Books from Z-Library', '📚', 1, datetime('now'))
    ''')
    
    c.execute('''
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
    
    # Add source_id column to existing papers table if it doesn't exist
    try:
        c.execute('ALTER TABLE papers ADD COLUMN source_id INTEGER REFERENCES library_sources(id)')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Books table for Z-Library downloads
    c.execute('''
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
    
    # User queries table for tracking questions and preferences
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text TEXT NOT NULL,
            query_type TEXT,
            topics TEXT,
            created_at TEXT
        )
    ''')
    
    # User preferences table for storing analyzed preferences
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preference_type TEXT NOT NULL,
            preference_value TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            last_updated TEXT
        )
    ''')
    
    # Notes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            note_type TEXT DEFAULT 'note',
            tags TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Add new columns to existing notes table if they don't exist
    for col, default in [('title', None), ('note_type', "'note'"), ('updated_at', None)]:
        try:
            c.execute(f'ALTER TABLE notes ADD COLUMN {col} TEXT' + (f' DEFAULT {default}' if default else ''))
        except sqlite3.OperationalError:
            pass  # Column already exists
    
    # Note links table for bidirectional references
    c.execute('''
        CREATE TABLE IF NOT EXISTS note_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_id INTEGER NOT NULL,
            linked_type TEXT NOT NULL,
            linked_id TEXT NOT NULL,
            link_type TEXT DEFAULT 'reference',
            created_at TEXT,
            FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_note_links_note ON note_links(note_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_note_links_target ON note_links(linked_type, linked_id)')
    
    # -------------------------------------------------------------
    # Multi-Chat Support (Added via OpenSpec)
    # -------------------------------------------------------------
    c.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)')
    
    # Migrate existing paper_id references to note_links table
    try:
        c.execute('SELECT id, paper_id FROM notes WHERE paper_id IS NOT NULL')
        rows = c.fetchall()
        for row in rows:
            note_id, paper_id = row['id'], row['paper_id']
            # Check if link already exists
            c.execute('SELECT id FROM note_links WHERE note_id = ? AND linked_type = ? AND linked_id = ?',
                      (note_id, 'paper', paper_id))
            if not c.fetchone():
                c.execute('''
                    INSERT INTO note_links (note_id, linked_type, linked_id, link_type, created_at)
                    VALUES (?, 'paper', ?, 'reference', datetime('now'))
                ''', (note_id, paper_id))
    except sqlite3.OperationalError:
        pass  # paper_id column doesn't exist yet (fresh db)
    
    conn.commit()
    conn.close()

def add_paper(paper_data: Dict[str, Any]):
    """
    Adds or updates a paper in the database.
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    # helper to serialize list/dict to json strings
    tags = json.dumps(paper_data.get('tags', []))
    authors = json.dumps(paper_data.get('authors', [])) if isinstance(paper_data.get('authors'), list) else paper_data.get('authors', "[]")
    
    now = datetime.now().isoformat()
    
    # Check if exists to preserve created_at or other fields if needed, 
    # but for now we'll do an upsert-like logic
    
    try:
        c.execute('''
            INSERT INTO papers (
                id, title, authors, published_date, url, abstract,
                citation_count, last_metadata_update, tags,
                summary_main_ideas, summary_methods, summary_results, summary_limitations,
                content_source, full_text_local_path, source_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                authors=excluded.authors,
                citation_count=excluded.citation_count,
                last_metadata_update=excluded.last_metadata_update,
                tags=excluded.tags,
                summary_main_ideas=excluded.summary_main_ideas,
                summary_methods=excluded.summary_methods,
                summary_results=excluded.summary_results,
                summary_limitations=excluded.summary_limitations,
                content_source=excluded.content_source,
                full_text_local_path=excluded.full_text_local_path,
                source_id=excluded.source_id
        ''', (
            paper_data['id'],
            paper_data.get('title'),
            authors,
            paper_data.get('published_date'),
            paper_data.get('url'),
            paper_data.get('abstract'),
            paper_data.get('citation_count', 0),
            now, # last_metadata_update
            tags,
            paper_data.get('summary_main_ideas'),
            paper_data.get('summary_methods'),
            paper_data.get('summary_results'),
            paper_data.get('summary_limitations'),
            paper_data.get('content_source', 'abstract_only'),
            paper_data.get('full_text_local_path'),
            paper_data.get('source_id'),
            now # created_at
        ))
        conn.commit()
    except Exception as e:
        print(f"Error adding paper {paper_data.get('id')}: {e}")
    finally:
        conn.close()


# ============ Library Source Management ============

def add_source(name: str, source_type: str, config: Dict = None, description: str = None, icon: str = "📁") -> int:
    """
    Add a new library source.
    source_type: 'arxiv', 'url', 'local_file', 'bibtex', 'custom'
    config: JSON config specific to source type (e.g., base_url, file_path, etc.)
    Returns the new source ID.
    """
    conn = get_db_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    config_json = json.dumps(config) if config else "{}"
    
    try:
        c.execute('''
            INSERT INTO library_sources (name, source_type, config, description, icon, enabled, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        ''', (name, source_type, config_json, description, icon, now))
        conn.commit()
        source_id = c.lastrowid
        return source_id
    except sqlite3.IntegrityError:
        # Name already exists
        c.execute("SELECT id FROM library_sources WHERE name = ?", (name,))
        row = c.fetchone()
        return row['id'] if row else None
    finally:
        conn.close()


def list_sources() -> List[Dict[str, Any]]:
    """
    List all library sources.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT ls.*, COUNT(p.id) as paper_count 
        FROM library_sources ls
        LEFT JOIN papers p ON p.source_id = ls.id
        GROUP BY ls.id
        ORDER BY ls.created_at DESC
    ''')
    rows = c.fetchall()
    conn.close()
    
    sources = []
    for row in rows:
        s = dict(row)
        s['config'] = json.loads(s['config']) if s['config'] else {}
        s['enabled'] = bool(s['enabled'])
        sources.append(s)
    return sources


def get_source(source_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific library source by ID.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM library_sources WHERE id = ?", (source_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        s = dict(row)
        s['config'] = json.loads(s['config']) if s['config'] else {}
        s['enabled'] = bool(s['enabled'])
        return s
    return None


def get_source_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a library source by name.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM library_sources WHERE name = ?", (name,))
    row = c.fetchone()
    conn.close()
    
    if row:
        s = dict(row)
        s['config'] = json.loads(s['config']) if s['config'] else {}
        s['enabled'] = bool(s['enabled'])
        return s
    return None


def update_source(source_id: int, name: str = None, config: Dict = None, description: str = None, icon: str = None, enabled: bool = None):
    """
    Update a library source.
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if config is not None:
        updates.append("config = ?")
        params.append(json.dumps(config))
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if icon is not None:
        updates.append("icon = ?")
        params.append(icon)
    if enabled is not None:
        updates.append("enabled = ?")
        params.append(1 if enabled else 0)
    
    if updates:
        params.append(source_id)
        c.execute(f"UPDATE library_sources SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    
    conn.close()


def delete_source(source_id: int) -> bool:
    """
    Delete a library source. Papers from this source will have their source_id set to NULL.
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    # Update papers to remove source reference
    c.execute("UPDATE papers SET source_id = NULL WHERE source_id = ?", (source_id,))
    
    # Delete the source
    c.execute("DELETE FROM library_sources WHERE id = ?", (source_id,))
    deleted = c.rowcount > 0
    
    conn.commit()
    conn.close()
    return deleted


def list_papers(sort_by="created_at_desc", source_id: int = None, source_type: str = None):
    conn = get_db_connection()
    c = conn.cursor()
    
    # Join with sources to get source info
    query = """
        SELECT p.*, ls.name as source_name, ls.icon as source_icon 
        FROM papers p
        LEFT JOIN library_sources ls ON p.source_id = ls.id
    """
    
    params = []
    if source_id is not None:
        query += " WHERE p.source_id = ?"
        params.append(source_id)
    elif source_type is not None:
        query += " WHERE ls.source_type = ?"
        params.append(source_type)
    
    order = "ORDER BY p.created_at DESC"
    if sort_by == "citation_count_desc":
        order = "ORDER BY p.citation_count DESC"
    elif sort_by == "recency":
        order = "ORDER BY p.published_date DESC"
        
    c.execute(f"{query} {order}", params)
    rows = c.fetchall()
    conn.close()
    
    papers = []
    for row in rows:
        p = dict(row)
        p['tags'] = json.loads(p['tags']) if p['tags'] else []
        p['authors'] = json.loads(p['authors']) if p['authors'] else []
        papers.append(p)
    return papers

def get_paper(paper_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
    row = c.fetchone()
    conn.close()
    if row:
        p = dict(row)
        p['tags'] = json.loads(p['tags']) if p['tags'] else []
        p['authors'] = json.loads(p['authors']) if p['authors'] else []
        return p
    return None

def search_local_papers(query_text):
    # Simple LIKE search for now
    conn = get_db_connection()
    c = conn.cursor()
    wildcard = f"%{query_text}%"
    c.execute('''
        SELECT * FROM papers 
        WHERE title LIKE ? OR summary_main_ideas LIKE ? OR tags LIKE ?
        ORDER BY created_at DESC LIMIT 20
    ''', (wildcard, wildcard, wildcard))
    rows = c.fetchall()
    conn.close()
    
    papers = []
    for row in rows:
        p = dict(row)
        p['tags'] = json.loads(p['tags']) if p['tags'] else []
        p['authors'] = json.loads(p['authors']) if p['authors'] else []
        papers.append(p)
    return papers


# ============ Book Management (Z-Library) ============

def add_book(book_data: Dict[str, Any]):
    """Add or update a book in the database."""
    conn = get_db_connection()
    c = conn.cursor()
    
    tags = json.dumps(book_data.get('tags', []))
    authors = json.dumps(book_data.get('authors', [])) if isinstance(book_data.get('authors'), list) else book_data.get('authors', "[]")
    
    now = datetime.now().isoformat()
    
    try:
        c.execute('''
            INSERT INTO books (
                id, title, authors, publisher, year, language, format,
                file_size, pages, isbn, description, cover_url,
                download_url, local_path, processed_text_path, zlibrary_id,
                source_id, tags, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                authors=excluded.authors,
                local_path=excluded.local_path,
                processed_text_path=excluded.processed_text_path,
                tags=excluded.tags
        ''', (
            book_data['id'],
            book_data.get('title'),
            authors,
            book_data.get('publisher'),
            book_data.get('year'),
            book_data.get('language'),
            book_data.get('format'),
            book_data.get('file_size'),
            book_data.get('pages'),
            book_data.get('isbn'),
            book_data.get('description'),
            book_data.get('cover_url'),
            book_data.get('download_url'),
            book_data.get('local_path'),
            book_data.get('processed_text_path'),
            book_data.get('zlibrary_id'),
            book_data.get('source_id'),
            tags,
            now
        ))
        conn.commit()
    except Exception as e:
        print(f"Error adding book {book_data.get('id')}: {e}")
    finally:
        conn.close()


def list_books(source_id: int = None) -> List[Dict[str, Any]]:
    """List all books in the database."""
    conn = get_db_connection()
    c = conn.cursor()
    
    query = """
        SELECT b.*, ls.name as source_name, ls.icon as source_icon 
        FROM books b
        LEFT JOIN library_sources ls ON b.source_id = ls.id
    """
    
    params = []
    if source_id is not None:
        query += " WHERE b.source_id = ?"
        params.append(source_id)
    
    query += " ORDER BY b.created_at DESC"
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    
    books = []
    for row in rows:
        b = dict(row)
        b['tags'] = json.loads(b['tags']) if b['tags'] else []
        b['authors'] = json.loads(b['authors']) if b['authors'] else []
        books.append(b)
    return books


def get_book(book_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific book by ID."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        b = dict(row)
        b['tags'] = json.loads(b['tags']) if b['tags'] else []
        b['authors'] = json.loads(b['authors']) if b['authors'] else []
        return b
    return None


def search_books(query_text: str) -> List[Dict[str, Any]]:
    """Search books by title, author, or description."""
    conn = get_db_connection()
    c = conn.cursor()
    wildcard = f"%{query_text}%"
    c.execute('''
        SELECT * FROM books 
        WHERE title LIKE ? OR authors LIKE ? OR description LIKE ?
        ORDER BY created_at DESC LIMIT 20
    ''', (wildcard, wildcard, wildcard))
    rows = c.fetchall()
    conn.close()
    
    books = []
    for row in rows:
        b = dict(row)
        b['tags'] = json.loads(b['tags']) if b['tags'] else []
        b['authors'] = json.loads(b['authors']) if b['authors'] else []
        books.append(b)
    return books


def get_zlibrary_source_id() -> Optional[int]:
    """Get the Z-Library source ID."""
    source = get_source_by_name("Z-Library")
    if source:
        return source['id']
    return None


# ============ User Query & Preference Management ============

def record_user_query(query_text: str, query_type: str = None, topics: List[str] = None):
    """
    Records a user's question for preference tracking.
    """
    conn = get_db_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    topics_json = json.dumps(topics) if topics else "[]"
    
    c.execute('''
        INSERT INTO user_queries (query_text, query_type, topics, created_at)
        VALUES (?, ?, ?, ?)
    ''', (query_text, query_type, topics_json, now))
    
    conn.commit()
    conn.close()


def get_recent_queries(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get the most recent user queries.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT * FROM user_queries 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    conn.close()
    
    queries = []
    for row in rows:
        q = dict(row)
        q['topics'] = json.loads(q['topics']) if q['topics'] else []
        queries.append(q)
    return queries


def update_user_preference(preference_type: str, preference_value: str, weight: float = 1.0):
    """
    Update or insert a user preference.
    """
    conn = get_db_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    # Check if exists
    c.execute('''
        SELECT id, weight FROM user_preferences 
        WHERE preference_type = ? AND preference_value = ?
    ''', (preference_type, preference_value))
    existing = c.fetchone()
    
    if existing:
        # Increase weight for repeated preferences
        new_weight = existing['weight'] + weight
        c.execute('''
            UPDATE user_preferences 
            SET weight = ?, last_updated = ?
            WHERE id = ?
        ''', (new_weight, now, existing['id']))
    else:
        c.execute('''
            INSERT INTO user_preferences (preference_type, preference_value, weight, last_updated)
            VALUES (?, ?, ?, ?)
        ''', (preference_type, preference_value, weight, now))
    
    conn.commit()
    conn.close()


def get_user_preferences(limit: int = 20) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get user preferences grouped by type, ordered by weight.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT * FROM user_preferences 
        ORDER BY weight DESC 
        LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    conn.close()
    
    # Group by preference type
    preferences = {}
    for row in rows:
        pref = dict(row)
        ptype = pref['preference_type']
        if ptype not in preferences:
            preferences[ptype] = []
        preferences[ptype].append({
            'value': pref['preference_value'],
            'weight': pref['weight']
        })
    
    return preferences


def get_preference_summary() -> str:
    """
    Generate a natural language summary of user preferences for the agent.
    """
    preferences = get_user_preferences(limit=30)
    recent_queries = get_recent_queries(limit=10)
    
    if not preferences and not recent_queries:
        return "No user preference data available yet."
    
    summary_parts = []
    
    # Summarize topic interests
    if 'topic' in preferences:
        topics = [p['value'] for p in preferences['topic'][:5]]
        if topics:
            summary_parts.append(f"Frequently interested topics: {', '.join(topics)}")
    
    # Summarize query types
    if 'query_type' in preferences:
        types = [p['value'] for p in preferences['query_type'][:3]]
        if types:
            summary_parts.append(f"Common query types: {', '.join(types)}")
    
    # Summarize specific interests
    if 'interest' in preferences:
        interests = [p['value'] for p in preferences['interest'][:5]]
        if interests:
            summary_parts.append(f"Specific interests: {', '.join(interests)}")
    
    # Add recent query context
    if recent_queries:
        recent_topics = []
        for q in recent_queries[:5]:
            if q.get('topics'):
                recent_topics.extend(q['topics'])
        if recent_topics:
            unique_recent = list(dict.fromkeys(recent_topics))[:5]
            summary_parts.append(f"Recent focus areas: {', '.join(unique_recent)}")
    
    if summary_parts:
        return "User Preferences:\n- " + "\n- ".join(summary_parts)
    else:
        return "User has started asking questions but preferences are still being learned."


# ============ Notes Management ============

def add_note(
    content: str,
    title: Optional[str] = None,
    note_type: str = "note",
    tags: Optional[List[str]] = None,
    linked_items: Optional[List[Dict[str, str]]] = None,
    paper_id: Optional[str] = None  # Backward compatibility
) -> int:
    """
    Create a new note with optional links to papers/notes.
    
    Args:
        content: Note content (required)
        title: Optional note title
        note_type: 'note', 'annotation', or 'summary'
        tags: List of tags
        linked_items: List of {"type": "paper"|"note", "id": "...", "link_type": "reference"}
        paper_id: Deprecated - use linked_items instead (kept for backward compatibility)
    """
    conn = get_db_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    tags_str = json.dumps(tags) if tags else None
    
    c.execute(
        'INSERT INTO notes (title, content, note_type, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
        (title, content, note_type, tags_str, now, now)
    )
    note_id = c.lastrowid
    
    # Handle backward-compatible paper_id
    if paper_id:
        c.execute(
            'INSERT INTO note_links (note_id, linked_type, linked_id, link_type, created_at) VALUES (?, ?, ?, ?, ?)',
            (note_id, 'paper', paper_id, 'reference', now)
        )
    
    # Handle linked_items
    if linked_items:
        for item in linked_items:
            c.execute(
                'INSERT INTO note_links (note_id, linked_type, linked_id, link_type, created_at) VALUES (?, ?, ?, ?, ?)',
                (note_id, item.get('type', 'paper'), item['id'], item.get('link_type', 'reference'), now)
            )
    
    conn.commit()
    conn.close()
    return note_id


def update_note(
    note_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    note_type: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> bool:
    """Update an existing note. Only non-None fields are updated."""
    conn = get_db_connection()
    c = conn.cursor()
    
    updates = []
    values = []
    
    if title is not None:
        updates.append('title = ?')
        values.append(title)
    if content is not None:
        updates.append('content = ?')
        values.append(content)
    if note_type is not None:
        updates.append('note_type = ?')
        values.append(note_type)
    if tags is not None:
        updates.append('tags = ?')
        values.append(json.dumps(tags))
    
    if not updates:
        conn.close()
        return False
    
    updates.append('updated_at = ?')
    values.append(datetime.now().isoformat())
    values.append(note_id)
    
    c.execute(f'UPDATE notes SET {", ".join(updates)} WHERE id = ?', values)
    success = c.rowcount > 0
    conn.commit()
    conn.close()
    return success


def delete_note(note_id: int) -> bool:
    """Delete a note and its links (cascades)."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    success = c.rowcount > 0
    conn.commit()
    conn.close()
    return success


def get_note(note_id: int) -> Optional[Dict[str, Any]]:
    """Get a single note by ID with its links."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT * FROM notes WHERE id = ?', (note_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return None
    
    note = dict(row)
    if note.get('tags'):
        try:
            note['tags'] = json.loads(note['tags'])
        except:
            note['tags'] = []
    
    # Get links
    note['links'] = get_note_links(note_id, conn)
    conn.close()
    return note


def get_notes(
    paper_id: Optional[str] = None,  # Backward compatibility
    note_type: Optional[str] = None,
    linked_paper_id: Optional[str] = None,
    search_query: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get notes with optional filters.
    
    Args:
        paper_id: Deprecated - use linked_paper_id instead
        note_type: Filter by note type
        linked_paper_id: Filter notes linked to a specific paper
        search_query: Full-text search in title and content
        limit: Max results
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    # Build query
    query = 'SELECT DISTINCT n.* FROM notes n'
    conditions = []
    params = []
    
    # Handle paper filtering via links
    effective_paper_id = linked_paper_id or paper_id
    if effective_paper_id:
        query += ' LEFT JOIN note_links nl ON n.id = nl.note_id'
        conditions.append('nl.linked_type = ? AND nl.linked_id = ?')
        params.extend(['paper', effective_paper_id])
    
    if note_type:
        conditions.append('n.note_type = ?')
        params.append(note_type)
    
    if search_query:
        conditions.append('(n.title LIKE ? OR n.content LIKE ?)')
        search_pattern = f'%{search_query}%'
        params.extend([search_pattern, search_pattern])
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' ORDER BY n.updated_at DESC, n.created_at DESC LIMIT ?'
    params.append(limit)
    
    c.execute(query, params)
    rows = c.fetchall()
    
    notes = []
    for row in rows:
        note = dict(row)
        if note.get('tags'):
            try:
                note['tags'] = json.loads(note['tags'])
            except:
                note['tags'] = []
        # Get links for each note
        note['links'] = get_note_links(note['id'], conn)
        notes.append(note)
    
    conn.close()
    return notes


def search_notes(query: str, note_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Full-text search notes by title and content."""
    return get_notes(search_query=query, note_type=note_type, limit=limit)


def get_note_links(note_id: int, conn=None) -> List[Dict[str, Any]]:
    """Get all links for a note, including linked paper/note details."""
    should_close = conn is None
    if conn is None:
        conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''
        SELECT nl.*, 
               CASE WHEN nl.linked_type = 'paper' THEN p.title ELSE n2.title END as linked_title
        FROM note_links nl
        LEFT JOIN papers p ON nl.linked_type = 'paper' AND nl.linked_id = p.id
        LEFT JOIN notes n2 ON nl.linked_type = 'note' AND nl.linked_id = CAST(n2.id AS TEXT)
        WHERE nl.note_id = ?
    ''', (note_id,))
    
    links = [dict(row) for row in c.fetchall()]
    
    if should_close:
        conn.close()
    return links


def add_note_link(
    note_id: int,
    linked_type: str,
    linked_id: str,
    link_type: str = "reference"
) -> int:
    """Add a link from a note to a paper or another note."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute(
        'INSERT INTO note_links (note_id, linked_type, linked_id, link_type, created_at) VALUES (?, ?, ?, ?, ?)',
        (note_id, linked_type, linked_id, link_type, datetime.now().isoformat())
    )
    link_id = c.lastrowid
    conn.commit()
    conn.close()
    return link_id


def remove_note_link(link_id: int) -> bool:
    """Remove a note link by its ID."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM note_links WHERE id = ?', (link_id,))
    success = c.rowcount > 0
    conn.commit()
    conn.close()
    return success


def get_paper_notes(paper_id: str) -> List[Dict[str, Any]]:
    """Get all notes linked to a specific paper."""
    return get_notes(linked_paper_id=paper_id)


def get_paper_full_text(paper_id: str) -> Optional[str]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT full_text_local_path FROM papers WHERE id = ?', (paper_id,))
    row = c.fetchone()
    conn.close()
    
    if row and row['full_text_local_path']:
        path = Path(row['full_text_local_path'])
        if path.is_absolute():
             full_path = path
        else:
             full_path = PROJECT_ROOT / path
             
        if full_path.exists():
            return full_path.read_text(encoding='utf-8', errors='replace')
    return None


# ============ Chat Session Management ============

def create_chat(title: Optional[str] = None) -> str:
    """Create a new chat session."""
    conn = get_db_connection()
    c = conn.cursor()
    
    chat_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    if not title:
        title = "New Chat"
        
    c.execute(
        'INSERT INTO chats (id, title, created_at) VALUES (?, ?, ?)',
        (chat_id, title, now)
    )
    
    conn.commit()
    conn.close()
    return chat_id


def list_chats() -> List[Dict[str, Any]]:
    """List all chat sessions ordered by creation date."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT * FROM chats ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_chat(chat_id: str) -> Optional[Dict[str, Any]]:
    """Get chat details."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT * FROM chats WHERE id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    
    return dict(row) if row else None


def delete_chat(chat_id: str) -> bool:
    """Delete a chat session and its messages."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Cascade delete handles messages, but explicit delete is safer if foreign keys disabled
    c.execute('DELETE FROM chats WHERE id = ?', (chat_id,))
    deleted = c.rowcount > 0
    
    conn.commit()
    conn.close()
    return deleted


def save_message(chat_id: str, role: str, content: str) -> int:
    """Save a message to a chat session."""
    conn = get_db_connection()
    c = conn.cursor()
    
    now = datetime.now().isoformat()
    
    c.execute(
        'INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)',
        (chat_id, role, content, now)
    )
    msg_id = c.lastrowid
    
    conn.commit()
    conn.close()
    return msg_id


def get_chat_history(chat_id: str) -> List[Dict[str, Any]]:
    """Get full message history for a chat."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC', (chat_id,))
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


if __name__ == "__main__":
    init_db()
    print("Database initialized.")

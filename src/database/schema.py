import sqlite3
import os
from loguru import logger

def init_database():
    """Initialize the database with proper schema"""
    db_path = os.path.expanduser("~/Library/Application Support/iMessage-Summarizer/messages.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        logger.info("Removed existing database")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables with proper schema
    cursor.executescript("""
    -- Chats table to store conversation threads
    CREATE TABLE chats (
        id INTEGER PRIMARY KEY,
        chat_identifier TEXT UNIQUE
    );
    
    -- Contacts table
    CREATE TABLE contacts (
        id INTEGER PRIMARY KEY,
        phone_number TEXT UNIQUE,
        display_name TEXT
    );
    
    -- Messages table with chat_id
    CREATE TABLE messages (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER,
        contact_id INTEGER,
        text TEXT,
        message_date DATETIME,
        is_from_me BOOLEAN,
        processed_in_summary BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (chat_id) REFERENCES chats(id),
        FOREIGN KEY (contact_id) REFERENCES contacts(id)
    );
    
    -- Summary tables
    CREATE TABLE identity_summaries (
        id INTEGER PRIMARY KEY,
        contact_id INTEGER,
        summary_text TEXT,
        last_updated DATETIME,
        FOREIGN KEY (contact_id) REFERENCES contacts(id)
    );
    
    CREATE TABLE weekly_conversation_summaries (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER,
        week_start DATE,
        summary_text TEXT,
        FOREIGN KEY (chat_id) REFERENCES chats(id)
    );
    
    -- Create indexes for better performance
    CREATE INDEX idx_messages_chat_id ON messages(chat_id);
    CREATE INDEX idx_messages_contact_id ON messages(contact_id);
    CREATE INDEX idx_messages_date ON messages(message_date);
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database schema initialized") 
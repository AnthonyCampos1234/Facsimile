import sqlite3
import os
from datetime import datetime
from loguru import logger

class MessageExtractor:
    def __init__(self):
        self.imessage_db = os.path.expanduser("~/Library/Messages/chat.db")
        self.our_db = os.path.expanduser("~/Library/Application Support/iMessage-Summarizer/messages.db")
        
    def extract_messages(self):
        """Extract messages from iMessage database"""
        if not os.path.exists(self.imessage_db):
            raise FileNotFoundError(f"iMessage database not found at {self.imessage_db}")
            
        imessage_conn = sqlite3.connect(self.imessage_db)
        our_conn = sqlite3.connect(self.our_db)
        
        try:
            # Extract and insert chats
            self._extract_chats(imessage_conn, our_conn)
            logger.info("Extracted chats")
            
            # Extract and insert contacts
            self._extract_contacts(imessage_conn, our_conn)
            logger.info("Extracted contacts")
            
            # Extract and insert messages
            self._extract_messages(imessage_conn, our_conn)
            logger.info("Extracted messages")
            
            logger.info("Message extraction completed successfully")
            
        finally:
            imessage_conn.close()
            our_conn.close()
            
    def _extract_chats(self, imessage_conn, our_conn):
        """Extract chat threads"""
        # Get chats from iMessage
        imessage_cursor = imessage_conn.cursor()
        imessage_cursor.execute("""
            SELECT DISTINCT chat_identifier 
            FROM chat
        """)
        chats = imessage_cursor.fetchall()
        
        # Insert into our database
        our_cursor = our_conn.cursor()
        our_cursor.executemany("""
            INSERT OR IGNORE INTO chats (chat_identifier)
            VALUES (?)
        """, chats)
        our_conn.commit()
        
    def _extract_contacts(self, imessage_conn, our_conn):
        """Extract contact information"""
        # Get contacts from iMessage
        imessage_cursor = imessage_conn.cursor()
        imessage_cursor.execute("""
            SELECT DISTINCT 
                handle.id as phone_number,
                COALESCE(
                    -- Try to get name from ABPerson if available
                    (
                        SELECT COALESCE(First, '') || ' ' || COALESCE(Last, '')
                        FROM ABPerson
                        WHERE ROWID = handle.person_cid
                    ),
                    handle.uncanonicalized_id,
                    handle.id
                ) as display_name
            FROM handle
            LEFT JOIN ABPerson ON handle.person_cid = ABPerson.ROWID
            WHERE handle.id IS NOT NULL
        """)
        contacts = imessage_cursor.fetchall()
        logger.info(f"Found {len(contacts)} contacts")
        
        # Insert into our database
        our_cursor = our_conn.cursor()
        our_cursor.executemany("""
            INSERT OR IGNORE INTO contacts (phone_number, display_name)
            VALUES (?, ?)
        """, contacts)
        our_conn.commit()
        
    def _extract_messages(self, imessage_conn, our_conn):
        """Extract messages with chat and contact information"""
        # Get messages from iMessage
        imessage_cursor = imessage_conn.cursor()
        imessage_cursor.execute("""
            SELECT 
                chat.chat_identifier,
                handle.id as phone_number,
                message.text,
                datetime(message.date/1000000000 + strftime("%s", "2001-01-01"), "unixepoch") as message_date,
                message.is_from_me
            FROM message 
            JOIN chat_message_join ON chat_message_join.message_id = message.ROWID
            JOIN chat ON chat.ROWID = chat_message_join.chat_id
            LEFT JOIN handle ON message.handle_id = handle.ROWID
            WHERE message.text IS NOT NULL
        """)
        messages = imessage_cursor.fetchall()
        logger.info(f"Found {len(messages)} messages in iMessage database")
        
        # Insert into our database
        our_cursor = our_conn.cursor()
        inserted = 0
        skipped = 0
        
        for msg in messages:
            chat_id = our_cursor.execute(
                "SELECT id FROM chats WHERE chat_identifier = ?", 
                (msg[0],)
            ).fetchone()
            
            contact_id = our_cursor.execute(
                "SELECT id FROM contacts WHERE phone_number = ?", 
                (msg[1],)
            ).fetchone() if msg[1] else None
            
            try:
                our_cursor.execute("""
                    INSERT OR IGNORE INTO messages (
                        chat_id,
                        contact_id,
                        text,
                        message_date,
                        is_from_me
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    chat_id[0] if chat_id else None,
                    contact_id[0] if contact_id else None,
                    msg[2],  # text
                    msg[3],  # message_date
                    msg[4]   # is_from_me
                ))
                if our_cursor.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.error(f"Error inserting message: {e}")
                logger.error(f"Message data: {msg}")
                raise
        
        our_conn.commit()
        logger.info(f"Inserted {inserted} messages, skipped {skipped} duplicates") 
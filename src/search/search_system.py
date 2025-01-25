from typing import List, Dict, Optional
from datetime import datetime, timedelta
import sqlite3
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from loguru import logger
import os

class MessageSearchSystem:
    def __init__(self):
        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Use absolute path to database
        self.db_path = os.path.expanduser("~/Library/Application Support/iMessage-Summarizer/messages.db")
        logger.info(f"Using database at: {self.db_path}")
        
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
            
        # Initialize vector store
        self.vectorstore = None
        self._initialize_vectorstore()

    def _initialize_vectorstore(self):
        """Load messages and create vector store"""
        try:
            # Get messages from SQLite
            messages = self._get_all_messages()
            logger.info(f"Retrieved {len(messages)} messages from database")
            
            if not messages:
                logger.error("No messages found in database")
                raise ValueError("No messages found in database")
                
            # Convert to documents
            docs = []
            for msg in messages:
                # Convert date string to timestamp
                date_obj = datetime.strptime(msg["date"], "%Y-%m-%d %H:%M:%S")
                
                doc = Document(
                    page_content=msg["text"],
                    metadata={
                        "date": date_obj.timestamp(),  # Store as timestamp
                        "date_str": msg["date"],  # Keep string version for display
                        "contact_name": msg["contact_name"],
                        "is_from_me": msg["is_from_me"]
                    }
                )
                docs.append(doc)
                
            logger.info(f"Created {len(docs)} documents for vector store")
            
            if not docs:
                logger.error("No valid documents to create vector store")
                raise ValueError("No valid documents to create vector store")

            # Create vector store
            self.vectorstore = Chroma.from_documents(
                documents=docs,
                embedding=self.embeddings
            )
            
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise

    def _get_all_messages(self) -> List[Dict]:
        """Get all messages from SQLite DB"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First check if we can connect and if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            logger.info(f"Found tables: {tables}")
            
            query = """
            SELECT 
                m.text,
                m.message_date,
                CASE 
                    WHEN m.is_from_me = 1 THEN 'Me'
                    ELSE c.display_name 
                END as sender_name,
                m.is_from_me
            FROM messages m
            LEFT JOIN contacts c ON m.contact_id = c.id
            WHERE m.text IS NOT NULL
            AND LENGTH(TRIM(m.text)) > 0  -- Skip empty/whitespace messages
            ORDER BY m.message_date DESC
            """
            
            cursor.execute(query)
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "text": row[0],
                    "date": row[1],
                    "contact_name": row[2],
                    "is_from_me": bool(row[3])
                })
            
            logger.info(f"Retrieved {len(messages)} messages")
            
            # Log a sample message for debugging
            if messages:
                logger.debug(f"Sample message: {messages[0]}")
                
            conn.close()
            return messages
            
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            raise

    def search_messages(
        self,
        query: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        k: int = 5
    ) -> List[Dict]:
        """Search messages using vector similarity"""
        try:
            # Extract name from query for filtering
            name = query.split("with ")[-1].split()[0].lower()
            logger.debug(f"Searching for messages with name: {name}")
            
            # Get messages directly from database for the time period
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # If start_date not provided, use last 7 days
            if not start_date:
                start_date = datetime.now() - timedelta(days=7)
            if not end_date:
                end_date = datetime.now()
            
            query = """
            WITH target_contact AS (
                SELECT id, display_name 
                FROM contacts 
                WHERE LOWER(display_name) LIKE ?
            ),
            target_chats AS (
                -- Get all chats involving the target contact
                SELECT DISTINCT chat_id
                FROM messages
                WHERE contact_id IN (SELECT id FROM target_contact)
            ),
            conversation_messages AS (
                -- Get all messages from those chats
                SELECT 
                    m.text,
                    m.message_date,
                    m.is_from_me,
                    CASE 
                        WHEN m.is_from_me = 1 THEN 'Me'
                        ELSE c.display_name 
                    END as sender_name
                FROM messages m
                LEFT JOIN contacts c ON m.contact_id = c.id
                WHERE m.chat_id IN (SELECT chat_id FROM target_chats)
                AND m.message_date BETWEEN ? AND ?
            )
            SELECT DISTINCT *
            FROM conversation_messages
            ORDER BY message_date
            """
            
            cursor.execute(query, (
                f"%{name}%",
                start_date.strftime("%Y-%m-%d %H:%M:%S"),
                end_date.strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "text": row[0],
                    "date": row[1],
                    "contact_name": row[3],
                    "is_from_me": bool(row[2])
                })
                logger.debug(f"Found message: {row[0]} from {row[3]}")
            
            conn.close()
            
            logger.info(f"Found {len(messages)} relevant messages")
            return messages[:k*2]
            
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            return []

    def _build_date_filter(self, start_date: Optional[datetime], end_date: Optional[datetime]):
        """Build date filter for vector store query"""
        if not start_date and not end_date:
            return None
            
        date_filter = {}
        if start_date:
            # Convert to timestamp for Chroma's filtering
            date_filter["date"] = {"$gte": start_date.timestamp()}
        if end_date:
            if "date" in date_filter:
                date_filter["date"]["$lte"] = end_date.timestamp()
            else:
                date_filter["date"] = {"$lte": end_date.timestamp()}
        
        return date_filter 
from pathlib import Path
import json
import sqlite3
from typing import List, Dict
from datetime import datetime, timedelta
from loguru import logger

from langchain.docstore.document import Document
from langchain_community.vectorstores.utils import filter_complex_metadata

class DataLoader:
    """Handles loading and preprocessing of all data types"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.db_path = base_path / "messages.db"
        self.raw_conversations_path = base_path / "raw_conversations"
        
    def _format_metadata(self, row, content_type: str) -> Dict:
        """Format metadata with proper timestamp"""
        try:
            # Handle different date formats
            date_str = str(row[4]).split('.')[0]  # Remove microseconds if present
            created_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            
            return {
                "content_type": content_type,
                "contact": str(row[0]),
                "created_at": str(created_at),
                "timestamp": int(created_at.timestamp())
            }
        except Exception as e:
            logger.error(f"Error formatting metadata: {e}")
            # Use current time as fallback
            now = datetime.now()
            return {
                "content_type": content_type,
                "contact": str(row[0]),
                "created_at": str(now),
                "timestamp": int(now.timestamp())
            }

    def load_weekly_summaries(self) -> List[Document]:
        """Load weekly summaries from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    c.display_name,
                    w.week_start_date,
                    w.week_end_date,
                    w.summary_text,
                    w.created_at
                FROM weekly_conversation_summaries w
                JOIN contacts c ON w.contact_id = c.id
                ORDER BY w.created_at DESC
            """)
            
            docs = []
            for row in cursor.fetchall():
                try:
                    metadata = self._format_metadata(row, "weekly_summary")
                    # Clean and format dates
                    week_start = str(row[1]).split('.')[0]
                    week_end = str(row[2]).split('.')[0]
                    
                    metadata.update({
                        "week_start": week_start,
                        "week_end": week_end
                    })
                    
                    docs.append(Document(
                        page_content=str(row[3]),
                        metadata=metadata
                    ))
                except Exception as e:
                    logger.error(f"Error processing row {row}: {e}")
                    continue
            
            conn.close()
            if not docs:
                logger.warning("No valid documents were created from weekly summaries")
            return docs
            
        except Exception as e:
            logger.error(f"Error loading weekly summaries: {e}")
            return []

    def load_identity_summaries(self) -> List[Document]:
        """Load identity summaries from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    c.display_name,
                    i.summary_text,
                    i.personality_traits,
                    i.relationship_context,
                    i.created_at
                FROM identity_summaries i
                JOIN contacts c ON i.contact_id = c.id
                ORDER BY i.created_at DESC
            """)
            
            docs = []
            for row in cursor.fetchall():
                # Create metadata dictionary
                metadata = {
                    "content_type": "identity_summary",
                    "contact": str(row[0]),
                    "created_at": str(row[4])
                }
                
                # Add personality traits if available
                if row[2]:
                    try:
                        traits = json.loads(row[2])
                        for trait, value in traits.items():
                            metadata[f"trait_{trait}"] = float(value)
                    except json.JSONDecodeError:
                        pass
                
                # Add relationship context if available
                if row[3]:
                    try:
                        context = json.loads(row[3])
                        for rel, value in context.items():
                            metadata[f"relationship_{rel}"] = float(value)
                    except json.JSONDecodeError:
                        pass
                
                # Create document
                docs.append(Document(
                    page_content=str(row[1]),
                    metadata=metadata
                ))
            
            return docs
            
        except Exception as e:
            logger.error(f"Error loading identity summaries: {e}")
            return []

    def load_recent_messages(self, days_lookback: int = 30) -> List[Document]:
        """Load recent messages from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days_lookback)).strftime("%Y-%m-%d")
            
            cursor.execute("""
                SELECT 
                    m.text,
                    m.message_date,
                    m.is_from_me,
                    c.display_name
                FROM messages m
                JOIN contacts c ON m.contact_id = c.id
                WHERE m.message_date >= ?
                ORDER BY m.message_date DESC
            """, (cutoff_date,))
            
            docs = []
            for row in cursor.fetchall():
                # Convert message_date to timestamp
                msg_date = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
                msg_ts = int(msg_date.timestamp())
                
                docs.append(Document(
                    page_content=row[0],
                    metadata={
                        "content_type": "message",
                        "timestamp": msg_ts,  # Use numeric timestamp
                        "created_at": row[1],  # Keep string date for display
                        "is_from_me": bool(row[2]),
                        "contact": row[3],
                        "sender": "Me" if bool(row[2]) else row[3]
                    }
                ))
            
            conn.close()
            return docs
            
        except Exception as e:
            logger.error(f"Error loading recent messages: {e}")
            return [] 
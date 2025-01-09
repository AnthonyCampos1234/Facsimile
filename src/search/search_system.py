from pathlib import Path
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger

from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from .data_loader import DataLoader

class MessageSearchSystem:
    """Main search system integrating all iMessage-Summarizer components"""
    
    def __init__(self, 
                 days_lookback: int = 30,
                 enable_privacy_filter: bool = True):
        # Initialize paths
        self.base_path = Path.home() / "Library" / "Application Support" / "iMessage-Summarizer"
        self.db_path = self.base_path / "messages.db"
        self.raw_conversations_path = self.base_path / "raw_conversations"
        
        # Settings
        self.days_lookback = days_lookback
        self.enable_privacy_filter = enable_privacy_filter
        
        # Initialize components
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        self.llm = ChatGroq(
            model="mixtral-8x7b-32768",
            temperature=0
        )
        
        # Initialize DataLoader first
        self.data_loader = DataLoader(self.base_path)
        
        # Then initialize stores
        self.stores = self._initialize_stores()
        
    def _initialize_stores(self) -> Dict:
        """Initialize all vector stores"""
        return {
            "weekly_summaries": self._create_summary_store(),
            "identity_summaries": self._create_identity_store(),
            "messages": self._create_message_store(),
        }
    
    def _create_summary_store(self) -> Chroma:
        """Create vector store for weekly summaries"""
        docs = self._load_weekly_summaries()
        return Chroma.from_documents(
            documents=docs,
            embedding=self.embedding_model,
            collection_name="weekly_summaries"
        )
    
    def _create_identity_store(self) -> Chroma:
        """Create vector store for identity summaries"""
        docs = self._load_identity_summaries()
        return Chroma.from_documents(
            documents=docs,
            embedding=self.embedding_model,
            collection_name="identity_summaries"
        )
    
    def _create_message_store(self) -> Chroma:
        """Create vector store for recent messages"""
        docs = self._load_recent_messages()
        return Chroma.from_documents(
            documents=docs,
            embedding=self.embedding_model,
            collection_name="messages"
        )

    def search(self, 
              query: str, 
              contact: Optional[str] = None,
              date_range: Optional[tuple] = None,
              k: int = 3) -> Dict:
        """
        Perform a hierarchical search across all data types
        """
        try:
            results = {
                "summaries": [],
                "identity": [],
                "messages": []
            }
            
            # First, search weekly summaries
            try:
                summary_results = self.stores["weekly_summaries"].similarity_search(
                    query,
                    k=k,
                    filter=self._create_filter(contact, date_range)
                )
                results["summaries"] = summary_results
            except Exception as e:
                logger.warning(f"Error searching weekly summaries: {e}")
            
            # Then search identity summaries
            try:
                identity_results = self.stores["identity_summaries"].similarity_search(
                    query,
                    k=1,
                    filter={"contact": contact} if contact else None
                )
                results["identity"] = identity_results
            except Exception as e:
                logger.warning(f"Error searching identity summaries: {e}")
            
            # Finally, search specific messages
            try:
                message_results = self.stores["messages"].similarity_search(
                    query,
                    k=k*2,  # Get more message results for context
                    filter=self._create_filter(contact, date_range)
                )
                results["messages"] = message_results
            except Exception as e:
                logger.warning(f"Error searching messages: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing search: {e}")
            return {
                "summaries": [],
                "identity": [],
                "messages": []
            }

    def _create_filter(self, 
                      contact: Optional[str] = None, 
                      date_range: Optional[tuple] = None) -> Dict:
        """Create filter dict for vector store queries"""
        filter_dict = {}
        
        if contact:
            filter_dict["contact"] = contact
            
        if date_range:
            start_date, end_date = date_range
            # Convert dates to timestamps
            start_ts = int(start_date.timestamp())
            end_ts = int(end_date.timestamp())
            
            # Use a day-based range with hour granularity
            hour_range = range(start_ts, end_ts + 1, 3600)  # 3600 seconds in an hour
            
            # Use $in operator with hour-based range
            filter_dict["timestamp"] = {
                "$in": list(hour_range)[:500]  # Limit to 500 values to prevent SQL variable limit
            }
            
        return filter_dict if filter_dict else None

    def _load_weekly_summaries(self):
        return self.data_loader.load_weekly_summaries()

    def _load_identity_summaries(self):
        return self.data_loader.load_identity_summaries()

    def _load_recent_messages(self):
        return self.data_loader.load_recent_messages(self.days_lookback) 
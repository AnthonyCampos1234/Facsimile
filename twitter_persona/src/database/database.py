import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from loguru import logger
from typing import List, Dict

# Set up logging
logger.add("twitter_analyzer.log", rotation="1 week")

class TwitterDatabase:
    def __init__(self):
        # Create database in user's application support directory
        app_dir = Path.home() / "Library" / "Application Support" / "Twitter-Persona"
        app_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = app_dir / "twitter.db"
        # Initialize connection
        self.conn = sqlite3.connect(self.db_path)
        self.setup_database()

    def setup_database(self):
        """Initialize database tables"""
        try:
            cursor = self.conn.cursor()
            
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS tweets (
                    id INTEGER PRIMARY KEY,
                    tweet_id TEXT UNIQUE,
                    text TEXT,
                    created_at DATETIME,
                    is_retweet BOOLEAN,
                    is_reply BOOLEAN,
                    reply_to_tweet_id TEXT,
                    reply_to_user_id TEXT,
                    retweet_count INTEGER,
                    like_count INTEGER,
                    quote_count INTEGER,
                    processed_in_summary BOOLEAN DEFAULT FALSE
                );

                CREATE TABLE IF NOT EXISTS identity_summaries (
                    id INTEGER PRIMARY KEY,
                    summary_text TEXT,
                    personality_traits TEXT,
                    interests TEXT,
                    common_topics TEXT,
                    confidence_scores TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS weekly_summaries (
                    id INTEGER PRIMARY KEY,
                    week_start_date DATE,
                    week_end_date DATE,
                    summary_text TEXT,
                    topics_discussed TEXT,
                    engagement_metrics TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            self.conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            raise

    def store_tweet(self, tweet_data: Dict):
        """Store a single tweet"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO tweets 
                (tweet_id, text, created_at, is_retweet, is_reply, 
                reply_to_tweet_id, reply_to_user_id, retweet_count, 
                like_count, quote_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tweet_data["id"],
                tweet_data["text"],
                tweet_data["created_at"],
                tweet_data["is_retweet"],
                tweet_data["is_reply"],
                tweet_data.get("reply_to_tweet_id"),
                tweet_data.get("reply_to_user_id"),
                tweet_data["retweet_count"],
                tweet_data["like_count"],
                tweet_data["quote_count"]
            ))
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Error storing tweet: {e}")
            self.conn.rollback()

    def store_identity_summary(self, summary_text, personality_traits, 
                             interests, common_topics, confidence_scores):
        """Store an identity summary"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO identity_summaries 
                (summary_text, personality_traits, interests, 
                common_topics, confidence_scores, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                summary_text,
                json.dumps(personality_traits),
                json.dumps(interests),
                json.dumps(common_topics),
                json.dumps(confidence_scores),
                datetime.now()
            ))
            self.conn.commit()
            logger.info("Stored new identity summary")
        except Exception as e:
            logger.error(f"Error storing identity summary: {e}")
            self.conn.rollback()

    def store_weekly_summary(self, week_start: datetime, week_end: datetime, 
                           summary_text: str, topics: List[str], 
                           engagement_metrics: Dict):
        """Store a weekly summary"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO weekly_summaries 
                (week_start_date, week_end_date, summary_text, 
                topics_discussed, engagement_metrics, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                week_start,
                week_end,
                summary_text,
                json.dumps(topics),
                json.dumps(engagement_metrics),
                datetime.now()
            ))
            self.conn.commit()
            logger.info(f"Stored weekly summary for {week_start} to {week_end}")
        except Exception as e:
            logger.error(f"Error storing weekly summary: {e}")
            self.conn.rollback()

    def get_unprocessed_tweets(self) -> List[Dict]:
        """Get tweets that haven't been included in summaries yet"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM tweets 
                WHERE processed_in_summary = FALSE
                ORDER BY created_at
            """)
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error fetching unprocessed tweets: {e}")
            return []

    def get_tweets_for_timeframe(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get tweets for a specific timeframe"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM tweets
                WHERE created_at BETWEEN ? AND ?
                ORDER BY created_at
            """, (start_date, end_date))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting tweets for timeframe: {e}")
            return []

    def get_latest_identity_summary(self) -> Dict:
        """Get the most recent identity summary"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM identity_summaries
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest identity summary: {e}")
            return None

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def optimize_database(self):
        """Optimize database storage"""
        try:
            # Close connection before VACUUM
            self.conn.close()
            
            # Reopen connection for VACUUM
            temp_conn = sqlite3.connect(self.db_path)
            temp_conn.execute("VACUUM")
            temp_conn.close()
            
            # Reopen main connection
            self.conn = sqlite3.connect(self.db_path)
            logger.info("Database optimized successfully")
            
        except Exception as e:
            logger.error(f"Error optimizing database: {e}") 
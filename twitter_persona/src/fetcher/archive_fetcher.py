import json
import os
from typing import List, Dict
from datetime import datetime
from pathlib import Path
from loguru import logger

class TwitterArchiveFetcher:
    def __init__(self):
        pass

    def load_archive(self, archive_path: str) -> List[Dict]:
        """Load tweets from a Twitter archive file"""
        try:
            archive_path = Path(archive_path)
            if not archive_path.exists():
                raise FileNotFoundError(f"Archive file not found: {archive_path}")

            logger.info(f"Loading archive from {archive_path}")
            
            # Handle both tweets.js and tweet.js (Twitter has used both names)
            if archive_path.is_dir():
                tweet_file = archive_path / "data" / "tweets.js"
                if not tweet_file.exists():
                    tweet_file = archive_path / "data" / "tweet.js"
            else:
                tweet_file = archive_path

            if not tweet_file.exists():
                raise FileNotFoundError(f"Tweet file not found in archive: {tweet_file}")

            # Read the file content
            with open(tweet_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Twitter archive files start with a variable assignment
            # Remove "window.YTD.tweets.part0 = " or similar
            if content.startswith('window.YTD.'):
                content = content.split('= ', 1)[1]

            # Parse JSON
            tweets_data = json.loads(content)
            
            # Convert to our standard format
            processed_tweets = []
            for tweet in tweets_data:
                # Handle both array and object formats
                tweet_obj = tweet.get('tweet', tweet)
                
                # Basic tweet data
                tweet_data = {
                    "id": str(tweet_obj['id']),
                    "text": tweet_obj['full_text'],
                    "created_at": datetime.strptime(
                        tweet_obj['created_at'],
                        '%a %b %d %H:%M:%S +0000 %Y'
                    ),
                    "is_retweet": tweet_obj['full_text'].startswith('RT @'),
                    "is_reply": bool(tweet_obj.get('in_reply_to_status_id')),
                    "reply_to_tweet_id": str(tweet_obj['in_reply_to_status_id']) if tweet_obj.get('in_reply_to_status_id') else None,
                    "reply_to_user_id": str(tweet_obj['in_reply_to_user_id']) if tweet_obj.get('in_reply_to_user_id') else None,
                    "retweet_count": tweet_obj.get('retweet_count', 0),
                    "like_count": tweet_obj.get('favorite_count', 0),
                    "quote_count": tweet_obj.get('quote_count', 0)
                }
                
                # Extract hashtags
                if 'entities' in tweet_obj and 'hashtags' in tweet_obj['entities']:
                    tweet_data['hashtags'] = [
                        tag['text'] for tag in tweet_obj['entities']['hashtags']
                    ]
                
                # Extract mentions
                if 'entities' in tweet_obj and 'user_mentions' in tweet_obj['entities']:
                    tweet_data['mentions'] = [
                        {
                            'username': mention['screen_name'],
                            'name': mention['name'],
                            'id': str(mention['id'])
                        }
                        for mention in tweet_obj['entities']['user_mentions']
                    ]
                
                processed_tweets.append(tweet_data)

            logger.info(f"Successfully loaded {len(processed_tweets)} tweets from archive")
            return processed_tweets

        except Exception as e:
            logger.error(f"Error loading Twitter archive: {e}")
            return []

    def process_archive_directory(self, directory_path: str) -> List[Dict]:
        """Process a Twitter archive directory including media"""
        try:
            directory_path = Path(directory_path)
            if not directory_path.is_dir():
                raise NotADirectoryError(f"Not a directory: {directory_path}")

            # Load tweets
            tweets = self.load_archive(directory_path)

            # Process media files if they exist
            media_dir = directory_path / "data" / "media"
            if media_dir.exists():
                logger.info(f"Processing media files from {media_dir}")
                # Map media files to tweets
                for tweet in tweets:
                    tweet_id = tweet['id']
                    media_files = list(media_dir.glob(f"*{tweet_id}*"))
                    if media_files:
                        tweet['media'] = [str(f.relative_to(directory_path)) for f in media_files]

            return tweets

        except Exception as e:
            logger.error(f"Error processing archive directory: {e}")
            return [] 
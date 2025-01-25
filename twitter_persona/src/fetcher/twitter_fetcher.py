import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import tweepy
from loguru import logger
import time

class TwitterFetcher:
    def __init__(self):
        # Load Twitter API credentials
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        if not self.bearer_token:
            raise ValueError("TWITTER_BEARER_TOKEN not found in environment variables")
            
        # Initialize Twitter API client
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            wait_on_rate_limit=False  # We'll handle rate limits ourselves
        )
        
        # Track API calls
        self.last_call_time = 0
        self.calls_this_window = 0
        self.RATE_LIMIT_WINDOW = 900  # 15 minutes in seconds
        self.MAX_CALLS_PER_WINDOW = 15  # Conservative limit for basic tier
        self.COOLDOWN_PERIOD = 60  # Mandatory 60-second cooldown between sessions
        
    def _check_rate_limit(self) -> Tuple[bool, int]:
        """Check if we're within rate limits"""
        current_time = time.time()
        window_elapsed = current_time - self.last_call_time
        
        # If this is the first call or we're starting a new session, enforce cooldown
        if self.last_call_time == 0 or window_elapsed >= self.RATE_LIMIT_WINDOW:
            logger.info("Starting new session, waiting for cooldown period...")
            time.sleep(self.COOLDOWN_PERIOD)
            self.calls_this_window = 0
            self.last_call_time = time.time()
            return True, 0
            
        # Check if we've exceeded our rate limit
        if self.calls_this_window >= self.MAX_CALLS_PER_WINDOW:
            wait_time = self.RATE_LIMIT_WINDOW - window_elapsed
            return False, int(wait_time)
            
        # Add small delay between calls
        time.sleep(2)
        return True, 0
        
    def _make_api_call(self, func, *args, **kwargs):
        """Make an API call with rate limit handling"""
        max_retries = 3
        base_wait = 60  # Base wait time in seconds
        
        for attempt in range(max_retries):
            can_proceed, wait_time = self._check_rate_limit()
            
            if not can_proceed:
                wait_time = min(wait_time, 120)  # Cap wait time at 2 minutes
                logger.warning(f"Rate limit reached. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
                
            try:
                self.calls_this_window += 1
                self.last_call_time = time.time()
                response = func(*args, **kwargs)
                return response
                
            except tweepy.TooManyRequests as e:
                wait_time = base_wait * (attempt + 1)
                logger.warning(f"Rate limit exceeded (429). Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
                
            except Exception as e:
                logger.error(f"API call failed: {e}")
                return None
                
        logger.error("Max retries exceeded")
        return None

    def fetch_user_tweets(
        self,
        username: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_results: int = 5
    ) -> List[Dict]:
        """Fetch tweets for a specific user"""
        try:
            logger.info(f"Fetching user info for @{username}...")
            # Get user ID from username
            user = self._make_api_call(self.client.get_user, username=username)
            if not user or not user.data:
                logger.error(f"User {username} not found")
                return []
                
            user_id = user.data.id
            logger.info(f"Found user ID: {user_id}")
            
            # Prepare query parameters
            params = {
                "tweet.fields": "created_at,public_metrics,referenced_tweets,in_reply_to_user_id",
                "max_results": max_results
            }
            
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time
                
            # Fetch tweets
            logger.info("Fetching tweets...")
            tweets = []
            response = self._make_api_call(self.client.get_users_tweets, id=user_id, **params)
            
            if response and response.data:
                for tweet in response.data:
                    tweet_data = {
                        "id": str(tweet.id),
                        "text": tweet.text,
                        "created_at": tweet.created_at,
                        "is_retweet": False,
                        "is_reply": bool(tweet.in_reply_to_user_id),
                        "reply_to_user_id": tweet.in_reply_to_user_id,
                        "reply_to_tweet_id": None,
                        "retweet_count": tweet.public_metrics.get("retweet_count", 0),
                        "like_count": tweet.public_metrics.get("like_count", 0),
                        "quote_count": tweet.public_metrics.get("quote_count", 0)
                    }
                    
                    # Check for reply tweet ID
                    if hasattr(tweet, "referenced_tweets") and tweet.referenced_tweets:
                        for ref in tweet.referenced_tweets:
                            if ref.type == "replied_to":
                                tweet_data["reply_to_tweet_id"] = str(ref.id)
                                
                    tweets.append(tweet_data)
            
            logger.info(f"Successfully fetched {len(tweets)} tweets")
            return tweets
            
        except Exception as e:
            logger.error(f"Error fetching tweets: {e}")
            return []

    def fetch_user_retweets(
        self,
        username: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_results: int = 5
    ) -> List[Dict]:
        """Fetch retweets for a specific user"""
        try:
            logger.info(f"Fetching user info for @{username}...")
            # Get user ID from username
            user = self._make_api_call(self.client.get_user, username=username)
            if not user or not user.data:
                logger.error(f"User {username} not found")
                return []
                
            user_id = user.data.id
            logger.info(f"Found user ID: {user_id}")
            
            # Prepare query parameters
            params = {
                "tweet.fields": "created_at,public_metrics,referenced_tweets",
                "max_results": max_results
            }
            
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time
                
            # Fetch retweets
            logger.info("Fetching retweets...")
            retweets = []
            response = self._make_api_call(self.client.get_users_tweets, id=user_id, **params)
            
            if response and response.data:
                for tweet in response.data:
                    if hasattr(tweet, "referenced_tweets") and tweet.referenced_tweets:
                        for ref in tweet.referenced_tweets:
                            if ref.type == "retweeted":
                                retweet_data = {
                                    "id": str(tweet.id),
                                    "text": tweet.text,
                                    "created_at": tweet.created_at,
                                    "is_retweet": True,
                                    "is_reply": False,
                                    "reply_to_user_id": None,
                                    "reply_to_tweet_id": None,
                                    "retweet_count": tweet.public_metrics.get("retweet_count", 0),
                                    "like_count": tweet.public_metrics.get("like_count", 0),
                                    "quote_count": tweet.public_metrics.get("quote_count", 0)
                                }
                                retweets.append(retweet_data)
            
            logger.info(f"Successfully fetched {len(retweets)} retweets")
            return retweets
            
        except Exception as e:
            logger.error(f"Error fetching retweets: {e}")
            return []

    def fetch_all_user_activity(
        self,
        username: str,
        days_lookback: int = 1
    ) -> List[Dict]:
        """Fetch all user activity including tweets and retweets"""
        try:
            logger.info(f"Starting fetch for @{username}...")
            start_time = datetime.utcnow() - timedelta(days=days_lookback)
            
            # Fetch tweets first
            tweets = self.fetch_user_tweets(username, start_time=start_time)
            logger.info(f"Fetched {len(tweets)} tweets")
            
            # Only fetch retweets if we haven't hit rate limits
            retweets = []
            can_proceed, _ = self._check_rate_limit()
            if can_proceed:
                retweets = self.fetch_user_retweets(username, start_time=start_time)
                logger.info(f"Fetched {len(retweets)} retweets")
            else:
                logger.warning("Skipping retweets due to rate limits")
            
            # Combine and sort by date
            all_activity = tweets + retweets
            return sorted(all_activity, key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error fetching user activity: {e}")
            return [] 
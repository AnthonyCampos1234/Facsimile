import os
from typing import Dict, List, Tuple
from datetime import datetime
import json
from loguru import logger
from anthropic import Anthropic

class TweetAnalyzer:
    """Analyzes tweets using Claude to generate insights"""
    
    def __init__(self):
        # Load API key
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            
        self.client = Anthropic()

    def _format_tweets(self, tweets: List[Dict]) -> str:
        """Format tweets for prompt input"""
        formatted = []
        for tweet in tweets:
            date = tweet["created_at"]
            tweet_type = "RETWEET" if tweet["is_retweet"] else "REPLY" if tweet["is_reply"] else "TWEET"
            formatted.append(f"[{date}] {tweet_type}: {tweet['text']}")
        return "\n".join(formatted)

    def generate_identity_summary(self, tweets: List[Dict], previous_summary: str = None) -> Tuple[str, Dict]:
        """Generate identity summary from tweets"""
        try:
            if not tweets:
                return "", {}

            # Sort tweets by date
            tweets = sorted(tweets, key=lambda x: x["created_at"])
            
            # Take samples for large tweet sets
            if len(tweets) > 50:
                sampled_tweets = []
                chunk_size = len(tweets) // 5  # Split into 5 chunks
                
                for i in range(0, len(tweets), chunk_size):
                    chunk = tweets[i:i + chunk_size]
                    sample_size = min(3, len(chunk))
                    sampled_tweets.extend(chunk[:sample_size])
                
                tweets = sampled_tweets[:15]  # Cap at 15 total tweets
                logger.info(f"Sampled {len(tweets)} tweets for analysis")

            # Format tweets for the prompt
            formatted_tweets = self._format_tweets(tweets)
            
            prompt = f"""You are a Twitter persona analyzer. Analyze the following tweets and return a JSON object.

Previous Summary: {previous_summary if previous_summary else 'None'}

Tweets to analyze:
{formatted_tweets}

Return your analysis in the following JSON format with no additional text:

{{
    "summary": "A detailed identity summary describing the person's Twitter persona, interests, and communication style",
    "personality_traits": {{
        "trait1": 0.8,
        "trait2": 0.6
    }},
    "interests": {{
        "interest1": 0.9,
        "interest2": 0.7
    }},
    "common_topics": [
        "topic1",
        "topic2",
        "topic3"
    ],
    "confidence_scores": {{
        "personality": 0.8,
        "interests": 0.7,
        "topics": 0.9
    }}
}}"""

            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4096,
                temperature=0,
                system="You are a Twitter persona analyzer that returns analysis in JSON format only.",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract just the JSON part from Claude's response
            response_text = response.content[0].text
            
            # Try to find JSON in the response
            try:
                # Look for JSON between triple backticks if present
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].strip()
                else:
                    json_str = response_text.strip()
                
                analysis = json.loads(json_str)
                
                # Verify required fields
                required_fields = ["summary", "personality_traits", "interests", "common_topics", "confidence_scores"]
                if not all(field in analysis for field in required_fields):
                    raise ValueError("Missing required fields in response")
                    
                return analysis["summary"], analysis
                
            except Exception as e:
                logger.error(f"Error parsing JSON response: {e}")
                logger.debug(f"Attempted to parse: {response_text}")
                return "", {}

        except Exception as e:
            logger.error(f"Error generating identity summary: {e}")
            return "", {}

    def generate_weekly_summary(self, tweets: List[Dict]) -> Tuple[str, List[str], Dict]:
        """Generate a summary of tweets for a week"""
        try:
            if not tweets:
                return "", [], {}

            # Format tweets for the prompt
            formatted_tweets = self._format_tweets(tweets)
            
            prompt = f"""You are a Twitter activity analyzer. Create a weekly summary of these tweets.

Tweets to analyze:
{formatted_tweets}

Return your analysis in the following JSON format with no additional text:

{{
    "weekly_summary": "A concise summary of the week's Twitter activity, including key topics and patterns",
    "topics_discussed": [
        "topic1",
        "topic2"
    ],
    "engagement_metrics": {{
        "most_engaging_topics": ["topic1", "topic2"],
        "avg_likes": 0,
        "avg_retweets": 0,
        "top_tweet_topics": ["topic1", "topic2"]
    }}
}}"""

            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4096,
                temperature=0,
                system="You are a Twitter activity analyzer that returns analysis in JSON format only.",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract just the JSON part from Claude's response
            response_text = response.content[0].text
            
            # Try to find JSON in the response
            try:
                # Look for JSON between triple backticks if present
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].strip()
                else:
                    json_str = response_text.strip()
                
                analysis = json.loads(json_str)
                
                return (
                    analysis["weekly_summary"],
                    analysis["topics_discussed"],
                    analysis["engagement_metrics"]
                )
                
            except Exception as e:
                logger.error(f"Error parsing weekly summary JSON: {e}")
                logger.debug(f"Attempted to parse: {response_text}")
                return "", [], {}

        except Exception as e:
            logger.error(f"Error generating weekly summary: {e}")
            return "", [], {} 
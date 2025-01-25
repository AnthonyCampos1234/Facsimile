from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import os
import time
from dotenv import load_dotenv
from loguru import logger
from anthropic import Anthropic

class MessageSummarizer:
    """Handles message summarization using Claude"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Verify API key is present
        if "ANTHROPIC_API_KEY" not in os.environ:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            
        self.client = Anthropic()
        
        # Rate limiting settings - Claude has much higher limits
        self.requests_per_minute = 50  
        self.min_delay = 60 / self.requests_per_minute
        self.last_request_time = 0
        self.backoff_time = 2  # Initial backoff time in seconds

    def _rate_limit(self, estimated_tokens: int = 1000):
        """Implement rate limiting with exponential backoff"""
        current_time = time.time()
        
        try:
            # Apply request rate limiting
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_delay:
                sleep_time = self.min_delay - time_since_last + self.backoff_time
                logger.info(f"Request rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
            
        except Exception as e:
            logger.error(f"Error in rate limiting: {e}")
            time.sleep(5)  # Default sleep on error

    def generate_identity_summary(self, messages: List[Dict], previous_summary: Optional[str] = None) -> Tuple[str, Dict]:
        """Generate identity summary from messages"""
        try:
            if not messages:
                return "", {}

            # Sort messages by date
            messages = sorted(messages, key=lambda x: x["date"])
            
            # Take samples for conversations with more than 50 messages
            if len(messages) > 50:
                sampled_messages = []
                chunk_size = len(messages) // 5  # Split into 5 chunks
                
                for i in range(0, len(messages), chunk_size):
                    chunk = messages[i:i + chunk_size]
                    sample_size = min(3, len(chunk))
                    sampled_messages.extend(chunk[:sample_size])
                
                messages = sampled_messages[:15]  # Cap at 15 total messages
                logger.info(f"Sampled {len(messages)} messages for analysis")

            # Apply rate limiting
            self._rate_limit()

            # Format messages for the prompt
            formatted_messages = self._format_messages(messages)
            
            prompt = f"""You are a conversation analyzer. Analyze the following messages and return a JSON object.

Previous Summary: {previous_summary if previous_summary else 'None'}

Messages to analyze:
{formatted_messages}

Return your analysis in the following JSON format with no additional text or explanation:

{{
    "summary": "A detailed identity summary describing the person's identity, personality, and relationship dynamics",
    "personality_traits": {{
        "trait1": 0.8,
        "trait2": 0.6
    }},
    "relationship_context": {{
        "context1": 0.9,
        "context2": 0.7
    }},
    "common_topics": [
        "topic1",
        "topic2",
        "topic3"
    ]
}}"""

            # Add debug print to see raw response
            print("\nRAW PROMPT:", prompt)

            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4096,
                temperature=0,
                system="You are a conversation analyzer that returns analysis in JSON format only.",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extract just the JSON part from Claude's response
            response_text = response.content[0].text
            
            # Add debug print
            print("\nRAW RESPONSE:", response_text)
            
            # Try to find JSON in the response
            try:
                # Look for JSON between triple backticks if present
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].strip()
                else:
                    json_str = response_text.strip()
                
                # Add debug print
                print("\nEXTRACTED JSON:", json_str)
                
                analysis = json.loads(json_str)
                
                # Verify required fields
                required_fields = ["summary", "personality_traits", "relationship_context", "common_topics"]
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

    def _format_messages(self, messages: List[Dict]) -> str:
        """Format messages for prompt input"""
        formatted = []
        for msg in messages:
            date = msg["date"] if isinstance(msg["date"], str) else msg["date"].strftime("%Y-%m-%d %H:%M:%S")
            sender = "Me" if msg["is_from_me"] else "Other"
            formatted.append(f"[{date}] {sender}: {msg['text']}")
        return "\n".join(formatted)

    def generate_weekly_summary(self, messages: List[Dict]) -> str:
        """Generate a summary of messages for a week"""
        try:
            if not messages:
                return ""

            # Apply rate limiting
            self._rate_limit()

            # Format messages for the prompt
            formatted_messages = self._format_messages(messages)
            
            prompt = f"""You are a conversation analyzer. Create a weekly summary of these messages.

Messages to analyze:
{formatted_messages}

Return your analysis in the following JSON format with no additional text:

{{
    "weekly_summary": "A concise summary of the week's conversations, including key topics, events, and patterns",
    "key_events": [
        "event1",
        "event2"
    ],
    "topics_discussed": [
        "topic1",
        "topic2"
    ],
    "overall_tone": "Description of the conversation tone"
}}"""

            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4096,
                temperature=0,
                system="You are a conversation analyzer that returns analysis in JSON format only.",
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
                
                # Return just the summary text
                return analysis.get("weekly_summary", "")

            except Exception as e:
                logger.error(f"Error parsing weekly summary JSON: {e}")
                logger.debug(f"Attempted to parse: {response_text}")
                return ""

        except Exception as e:
            logger.error(f"Error generating weekly summary: {e}")
            return ""
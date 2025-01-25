from typing import List, Dict
import os
from dotenv import load_dotenv
from loguru import logger
from anthropic import Anthropic

class ResponseGenerator:
    def __init__(self):
        load_dotenv()
        
        if "ANTHROPIC_API_KEY" not in os.environ:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            
        self.client = Anthropic()

    def generate_response(self, query: str, messages: List[Dict]) -> str:
        """Generate a response to the query based on relevant messages"""
        try:
            # Format messages chronologically
            formatted_messages = []
            for msg in sorted(messages, key=lambda x: x["date"]):
                date = msg["date"]
                sender = "Me" if msg["is_from_me"] else msg["contact_name"]
                formatted_messages.append(f"[{date}] {sender}: {msg['text']}")
            
            messages_text = "\n".join(formatted_messages)
            
            prompt = f"""You are analyzing iMessage conversations to answer questions.

Context: The following are relevant messages from a conversation history:

{messages_text}

Question: {query}

Provide a clear and detailed answer based only on the information in the messages above. Include specific dates and quotes when relevant. If the information needed to answer the question is not in the messages, say so."""

            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4096,
                temperature=0,
                system="You are a helpful assistant that analyzes message conversations and provides detailed, accurate answers based only on the provided message history.",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            return response.content[0].text.strip()

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Sorry, I encountered an error: {str(e)}" 
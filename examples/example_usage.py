import os
from dotenv import load_dotenv
from src.search.search_system import MessageSearchSystem
from src.search.response_generator import ResponseGenerator
from datetime import datetime, timedelta

def main():
    # Load environment variables
    load_dotenv()
    
    # Verify required API keys
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
    if "OPENAI_API_KEY" not in os.environ:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    # Initialize systems
    search_system = MessageSearchSystem()
    response_generator = ResponseGenerator()

    # Example query with date range
    query = "What did I discuss with Daniel Ip recently?"
    messages = search_system.search_messages(
        query,
        start_date=datetime.now() - timedelta(days=7),  # Last week only
        k=5
    )
    response = response_generator.generate_response(query, messages)
    
    print("\nQuery:", query)
    print("\nResponse:", response)

    # Print raw messages for debugging
    print("\nRaw messages found:")
    for msg in messages:
        print(f"{msg['date']} - {msg['contact_name']}: {msg['text']}")

if __name__ == "__main__":
    main() 
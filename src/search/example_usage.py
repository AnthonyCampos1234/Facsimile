import os
import getpass
from datetime import datetime, timedelta
from dotenv import load_dotenv
from .search_system import MessageSearchSystem
from .response_generator import ResponseGenerator
import sqlite3
from pathlib import Path

def setup_groq_api():
    """Set up GROQ API key from .env file"""
    load_dotenv()  # Load environment variables from .env file
    
    if "GROQ_API_KEY" not in os.environ:
        print("\nGROQ API key not found in .env file.")
        api_key = getpass.getpass("Please enter your GROQ API key: ")
        
        # Save to .env file
        with open(".env", "a") as f:
            f.write(f"\nGROQ_API_KEY={api_key}")
        
        # Set for current session
        os.environ["GROQ_API_KEY"] = api_key

def check_database():
    """Check if database has required data"""
    base_path = Path.home() / "Library" / "Application Support" / "iMessage-Summarizer"
    db_path = base_path / "messages.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check identity summaries
    cursor.execute("SELECT COUNT(*) FROM identity_summaries")
    count = cursor.fetchone()[0]
    print(f"Found {count} identity summaries")
    
    if count > 0:
        cursor.execute("""
            SELECT c.display_name, i.summary_text 
            FROM identity_summaries i 
            JOIN contacts c ON i.contact_id = c.id 
            LIMIT 1
        """)
        sample = cursor.fetchone()
        print(f"Sample summary for {sample[0]}: {sample[1][:100]}...")
    
    conn.close()

def main():
    # Check database first
    check_database()
    
    # Set up GROQ API key
    setup_groq_api()
    
    # Initialize the search system
    search_system = MessageSearchSystem(days_lookback=30)
    
    # Initialize response generator
    response_gen = ResponseGenerator(search_system.llm)
    
    # Example 1: Simple search
    query = "What did I discuss with Professor Loessi about my final grade?"
    results = search_system.search(query)
    response = response_gen.generate_response(query, results)
    print("\nExample 1 - Simple Search:")
    print(f"Query: {query}")
    print(f"Response: {response}\n")
    
    # Example 2: Search with contact filter
    query = "What projects did I work on with Daniel?"
    results = search_system.search(
        query,
        contact="Daniel Ip"
    )
    response = response_gen.generate_response(query, results)
    print("\nExample 2 - Contact-Specific Search:")
    print(f"Query: {query}")
    print(f"Response: {response}\n")
    
    # Example 3: Search with date range
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    query = "What were my recent conversations about?"
    results = search_system.search(
        query,
        date_range=(start_date, end_date)
    )
    response = response_gen.generate_response(
        query, 
        results,
        response_type="time_specific"
    )
    print("\nExample 3 - Time-Range Search:")
    print(f"Query: {query}")
    print(f"Response: {response}\n")

if __name__ == "__main__":
    main() 
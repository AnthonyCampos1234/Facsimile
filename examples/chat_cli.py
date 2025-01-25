import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.search.search_system import MessageSearchSystem
from src.search.response_generator import ResponseGenerator
import sys

def main():
    # Initialize the search system
    search_system = MessageSearchSystem()
    response_generator = ResponseGenerator()

    print("\nWelcome to Message Search!")
    print("You can ask questions about your message history.")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            # Get user input
            query = input("\nWhat would you like to know about your messages? > ")
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye!")
                break
                
            # Get time range if specified
            time_range = input("\nSpecify time range (e.g., '1 week', '3 months', 'all') [default: all]: ")
            
            # Calculate date range
            end_date = datetime.now()
            if time_range.lower() == 'all' or not time_range.strip():
                start_date = None
            else:
                try:
                    # Parse time range
                    number = int(''.join(filter(str.isdigit, time_range)))
                    unit = ''.join(filter(str.isalpha, time_range.lower()))
                    
                    if unit.startswith('y'):
                        start_date = end_date - timedelta(days=number*365)
                    elif unit.startswith('m'):
                        start_date = end_date - timedelta(days=number*30)
                    elif unit.startswith('w'):
                        start_date = end_date - timedelta(weeks=number)
                    elif unit.startswith('d'):
                        start_date = end_date - timedelta(days=number)
                    else:
                        print("Invalid time unit. Using all messages.")
                        start_date = None
                except:
                    print("Invalid time range format. Using all messages.")
                    start_date = None

            # Search messages
            relevant_messages = search_system.search_messages(
                query=query,
                start_date=start_date,
                end_date=end_date
            )

            if not relevant_messages:
                print("\nNo relevant messages found.")
                continue

            # Generate response
            response = response_generator.generate_response(query, relevant_messages)
            
            print("\nResponse:")
            print(response)
            print("\n" + "-"*80)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            continue

if __name__ == "__main__":
    main() 
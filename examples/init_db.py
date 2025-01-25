from src.database.schema import init_database
from src.database.message_extractor import MessageExtractor

def main():
    # Initialize database schema
    init_database()
    
    # Extract messages
    extractor = MessageExtractor()
    extractor.extract_messages()

if __name__ == "__main__":
    main() 
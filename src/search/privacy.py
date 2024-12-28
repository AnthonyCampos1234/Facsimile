from typing import List, Dict
import re
from loguru import logger

class PrivacyFilter:
    """Handles privacy-related filtering and content masking"""
    
    def __init__(self):
        self.sensitive_patterns = [
            r'\b\d{16}\b',  # Credit card numbers
            r'\b\d{9}\b',   # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            # Add more patterns as needed
        ]
        
    def filter_sensitive_content(self, text: str) -> str:
        """Remove or mask sensitive information"""
        filtered_text = text
        for pattern in self.sensitive_patterns:
            filtered_text = re.sub(pattern, '[REDACTED]', filtered_text)
        return filtered_text
    
    def validate_contact_access(self, contact: str, allowed_contacts: List[str]) -> bool:
        """Check if access to contact's messages is allowed"""
        return contact in allowed_contacts 
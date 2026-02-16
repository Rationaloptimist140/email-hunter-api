"""
Email Hunter Script
Finds and extracts all email addresses from messy text.
"""

import re
from typing import List


def find_emails(text: str) -> List[str]:
    """
    Extract all email addresses from text.

    Args:
        text: Input text that may contain email addresses

    Returns:
        List of unique email addresses found
    """
    # Email regex pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # Find all matches
    emails = re.findall(email_pattern, text)

    # Return unique emails while preserving order
    seen = set()
    unique_emails = []
    for email in emails:
        email_lower = email.lower()
        if email_lower not in seen:
            seen.add(email_lower)
            unique_emails.append(email)

    return unique_emails


def hunt_emails(text: str) -> dict:
    """
    Main function to hunt for emails in text.

    Args:
        text: Input text to search

    Returns:
        Dictionary with emails found and count
    """
    emails = find_emails(text)

    return {
        "emails": emails,
        "count": len(emails),
        "text_length": len(text)
    }

"""Text quality utilities for detecting corrupted or unreadable text."""

import re
from typing import Optional

def is_mojibake(text: str, threshold: float = 0.15) -> bool:
    """
    Detect if text contains mojibake (encoding corruption).
    
    Mojibake occurs when UTF-8 text (like Devanagari) is incorrectly 
    decoded as Latin-1/Windows-1252, resulting in garbage characters.
    
    Common pattern: à¤, à¥, à¦ followed by special chars
    
    Args:
        text: Text to check
        threshold: Fraction of text that must be mojibake to trigger (default 15%)
    
    Returns:
        True if text appears to be mojibake
    """
    if not text or len(text.strip()) < 10:
        return False
    
    # Pattern 1: Common mojibake sequences from Devanagari UTF-8 -> Latin-1
    # à¤ (U+00E0 U+00A4) is the most common - appears in almost every Devanagari char
    # à¥ (U+00E0 U+00A5) is also very common
    mojibake_patterns = [
        r'à¤[\x80-\xFF]',  # à¤ followed by high-byte char
        r'à¥[\x80-\xFF]',  # à¥ followed by high-byte char
        r'à¦[\x80-\xFF]',  # à¦ (Bengali/Assamese)
    ]
    
    combined_pattern = '|'.join(mojibake_patterns)
    matches = re.findall(combined_pattern, text)
    
    if not matches:
        return False
    
    # Calculate mojibake ratio
    mojibake_chars = sum(len(m) for m in matches)
    total_chars = len(text)
    ratio = mojibake_chars / total_chars
    
    return ratio >= threshold


def get_text_quality_issue(text: str) -> Optional[str]:
    """
    Determine if text has quality issues that should skip LLM processing.
    
    Args:
        text: Text to check
    
    Returns:
        Issue description if found, None otherwise
    """
    if not text or text.strip() == "":
        return "empty"
    
    if is_mojibake(text):
        return "mojibake"
    
    return None

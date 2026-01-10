"""
Utility functions and helpers for Nexus Nebula Universe
"""

import uuid
import string
import random
from typing import List, Dict, Any

def generate_share_url(length: int = 8) -> str:
    """Generate a random share URL"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_project_id() -> str:
    """Generate a unique project ID"""
    return str(uuid.uuid4())

def generate_artifact_id() -> str:
    """Generate a unique artifact ID"""
    return str(uuid.uuid4())

def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return ".1f"

def extract_code_blocks(content: str) -> List[Dict[str, str]]:
    """Extract code blocks from markdown content"""
    import re

    code_blocks = []
    pattern = r'```(\w+)?\n(.*?)\n```'
    matches = re.findall(pattern, content, re.DOTALL)

    for lang, code in matches:
        code_blocks.append({
            "language": lang or "text",
            "code": code.strip()
        })

    return code_blocks

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    # Ensure it's not empty
    if not filename:
        filename = "unnamed_file"
    return filename

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    if '.' in filename:
        return filename.split('.')[-1].lower()
    return ""

def is_text_file(filename: str) -> bool:
    """Check if file is likely a text file"""
    text_extensions = {
        'txt', 'md', 'py', 'js', 'ts', 'html', 'css', 'json', 'xml', 'yaml', 'yml',
        'sh', 'bash', 'sql', 'csv', 'log', 'conf', 'ini', 'toml', 'rs', 'go', 'java',
        'cpp', 'c', 'h', 'hpp', 'php', 'rb', 'pl', 'r', 'scala', 'kt', 'swift'
    }
    return get_file_extension(filename) in text_extensions

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity (0-1)"""
    # Very basic similarity - in production use proper NLP
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    if not union:
        return 0.0

    return len(intersection) / len(union)
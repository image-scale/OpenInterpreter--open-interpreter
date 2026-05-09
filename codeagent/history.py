"""
Conversation history management - saving and loading conversations.
"""

import json
import os
import re
from datetime import datetime


def sanitize_filename(text, max_length=30):
    """Sanitize text to be used as part of a filename."""
    invalid_chars = '<>:"/\\|?*!\n\r\t'
    for char in invalid_chars:
        text = text.replace(char, "")
    text = re.sub(r'\s+', '_', text.strip())
    return text[:max_length]


def generate_conversation_filename(first_message_content):
    """Generate a filename based on first message content and current date."""
    words = first_message_content[:30].split()
    if len(words) >= 2:
        prefix = "_".join(words[:-1])
    else:
        prefix = sanitize_filename(first_message_content[:20])

    prefix = sanitize_filename(prefix)
    date = datetime.now().strftime("%B_%d_%Y_%H-%M-%S")
    return f"{prefix}__{date}.json"


def ensure_directory(path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)


def save_conversation(messages, filepath):
    """Save messages to a JSON file."""
    directory = os.path.dirname(filepath)
    if directory:
        ensure_directory(directory)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)


def load_conversation(filepath):
    """Load messages from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_conversations(directory):
    """List all conversation files in a directory."""
    if not os.path.exists(directory):
        return []

    files = []
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            try:
                mtime = os.path.getmtime(filepath)
                files.append({
                    'filename': filename,
                    'filepath': filepath,
                    'modified': datetime.fromtimestamp(mtime)
                })
            except OSError:
                pass

    return sorted(files, key=lambda x: x['modified'], reverse=True)

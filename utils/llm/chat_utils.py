# utils/chat_utils.py
import os
import json

CHAT_LOGS_DIR = "chat_logs"
MAX_CONTEXT_LENGTH = 5000
ROLLING_LOG_FILE = os.path.join(CHAT_LOGS_DIR, "chat_history.json")
FULL_LOG_FILE = os.path.join(CHAT_LOGS_DIR, "chat_history_full.json")
# Ensure the directory exists
os.makedirs(CHAT_LOGS_DIR, exist_ok=True)


def load_full_chat_history():
    """
    Loads the never-ending chat history from a JSON file,
    or returns an empty list if none found.
    """
    if os.path.exists(FULL_LOG_FILE):
        with open(FULL_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_full_chat_history(full_history):
    """
    Saves the never-ending chat history to disk (no truncation).
    """
    with open(FULL_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(full_history, f, indent=4)

def build_rolling_history(full_history):
    """
    Builds a rolling context from the end of the full_history,
    ensuring we don't exceed the MAX_CONTEXT_LENGTH in total JSON size.

    Returns a truncated list that is <= MAX_CONTEXT_LENGTH in size.
    """
    rolling = []
    total_size = 0

    # We'll iterate backwards (most recent first),
    # then insert at the front.
    for entry in reversed(full_history):
        entry_size = len(json.dumps(entry))
        if total_size + entry_size <= MAX_CONTEXT_LENGTH:
            rolling.insert(0, entry)
            total_size += entry_size
        else:
            break

    return rolling

def save_rolling_history(rolling_history):
    """
    Saves the rolling history to 'chat_history.json'.
    """
    with open(ROLLING_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(rolling_history, f, indent=4)

def load_rolling_history():
    """
    Loads the truncated (rolling) chat history from the log file.
    If it doesn't exist, returns an empty list.
    """
    if os.path.exists(ROLLING_LOG_FILE):
        with open(ROLLING_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_chat_history():
    """Loads chat history from the log file."""
    log_file = os.path.join(CHAT_LOGS_DIR, "chat_history_small.json")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_chat_log(chat_history):
    """Saves the chat history, ensuring it stays within context length."""
    log_file = os.path.join(CHAT_LOGS_DIR, "chat_history_small.json")
    total_length = sum(len(json.dumps(entry)) for entry in chat_history)
    while total_length > MAX_CONTEXT_LENGTH and chat_history:
        chat_history.pop(0)
        total_length = sum(len(json.dumps(entry)) for entry in chat_history)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, indent=4)


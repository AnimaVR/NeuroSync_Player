# utils/chat_utils.py
import os
import json

CHAT_LOGS_DIR = "chat_logs"
MAX_CONTEXT_LENGTH = 5000

# Ensure the directory exists
os.makedirs(CHAT_LOGS_DIR, exist_ok=True)

def load_chat_history():
    """Loads chat history from the log file."""
    log_file = os.path.join(CHAT_LOGS_DIR, "chat_history.json")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_chat_log(chat_history):
    """Saves the chat history, ensuring it stays within context length."""
    log_file = os.path.join(CHAT_LOGS_DIR, "chat_history.json")
    total_length = sum(len(json.dumps(entry)) for entry in chat_history)
    while total_length > MAX_CONTEXT_LENGTH and chat_history:
        chat_history.pop(0)
        total_length = sum(len(json.dumps(entry)) for entry in chat_history)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, indent=4)

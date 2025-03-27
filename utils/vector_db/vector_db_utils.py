# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

# utils/vector_db/vector_db_utils.py

from datetime import datetime, timezone
from utils.vector_db.get_embedding import get_embedding  

def update_system_message_with_context(user_input: str, base_system_message: str, vector_db, top_n: int = 4) -> str:
    
    retrieval_embedding = get_embedding(user_input, use_openai=False)
    context_string = vector_db.get_context_string(retrieval_embedding, top_n=top_n)
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S GMT")
    return f"{base_system_message}{context_string}\nThe current time and date is: {current_time}"


def add_exchange_to_vector_db(user_input: str, response: str, vector_db):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S GMT")
    combined_text = f"User: {user_input}\nYou: {response}\nTimestamp: {timestamp}\n"
    combined_embedding = get_embedding(combined_text, use_openai=False)
    vector_db.add_entry(combined_embedding, combined_text)


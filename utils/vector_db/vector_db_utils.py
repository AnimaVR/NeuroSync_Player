# utils/vector_db/vector_db_utils.py
# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.


from datetime import datetime, timezone
from utils.vector_db.get_embedding import get_embedding 

def update_system_message_with_context(user_input: str, base_system_message: str, vector_db, top_n: int = 4) -> str:
    """
    Retrieve relevant context from the vector DB based on the user input,
    then update and return the system message with that context and the current time.

    Parameters:
        user_input (str): The user's input text.
        base_system_message (str): The base system message to start with.
        vector_db: The vector database instance.
        top_n (int): Number of top matching contexts to retrieve.

    Returns:
        str: The updated system message.
    """
    # Compute embedding for the user input.
    retrieval_embedding = get_embedding(user_input, use_openai=False)
    # Retrieve the top matching context from the vector DB.
    context_string = vector_db.get_context_string(retrieval_embedding, top_n=top_n)
    # Get the current GMT time.
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S GMT")
    # Build and return the updated system message.
    return f"{base_system_message}{context_string}\nThe current time and date is: {current_time}"


def add_exchange_to_vector_db(user_input: str, response: str, vector_db):
    """
    Combine the user input and LLM response, compute an embedding for the combined text,
    and add the exchange to the vector DB.

    Parameters:
        user_input (str): The user's input text.
        response (str): The LLM's full response.
        vector_db: The vector database instance.
    """
    # Get the current GMT time.
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S GMT")
    # Combine user input and response into one text block with timestamp.
    combined_text = f"User: {user_input}\nYou: {response}\nTimestamp: {timestamp}\n"
    # Compute the embedding for the combined text.
    combined_embedding = get_embedding(combined_text, use_openai=False)
    # Add the combined exchange to the vector DB.
    vector_db.add_entry(combined_embedding, combined_text)

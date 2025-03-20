import requests
from threading import Thread
from queue import Queue
from openai import OpenAI

from utils.llm.sentence_builder import SentenceBuilder



##############################
# Warm-up Function to Pre-establish the Connection
##############################
def warm_up_llm_connection(config):
    """
    Perform a lightweight dummy request to warm up the LLM connection.
    This avoids the initial delay when the user sends the first real request.
    """
    if config["USE_LOCAL_LLM"]:
        try:
            # For local LLM, use a dummy ping request with a short timeout.
            requests.post(config["LLM_STREAM_URL"], json={"dummy": "ping"}, timeout=1)
            print("Local LLM connection warmed up.")
        except Exception as e:
            print("Local LLM connection warm-up failed:", e)
    else:
        try:
            # For OpenAI API, send a lightweight ping message.
            client = OpenAI(api_key=config["OPENAI_API_KEY"])
            client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "ping"}],
                max_tokens=1,
                stream=False
            )
            print("OpenAI API connection warmed up.")
        except Exception as e:
            print("OpenAI API connection warm-up failed:", e)

##############################
# UI Update Function
##############################
def update_ui(token: str):
    """
    Immediately update the UI with the token.
    This version checks for newline characters and prints them so that
    line breaks and paragraphs are preserved.
    """
    # Replace Windows-style newlines with Unix-style
    token = token.replace('\r\n', '\n')
    # If the token contains newline(s), split and print accordingly.
    if '\n' in token:
        parts = token.split('\n')
        for i, part in enumerate(parts):
            print(part, end='', flush=True)
            if i < len(parts) - 1:
                print()
    else:
        print(token, end='', flush=True)





def build_llm_payload(user_input, chat_history, config):
    """
    Build the conversation messages and payload from the user input,
    chat history, and configuration.

    Returns:
        dict: The payload containing the messages and generation parameters.
    """
    system_message = config.get(
        "system_message",
        "You are Mai, speak naturally and like a human might with humour and dryness."
    )
    messages = [{"role": "system", "content": system_message}]
    for entry in chat_history:
        messages.append({"role": "user", "content": entry["input"]})
        messages.append({"role": "assistant", "content": entry["response"]})
    messages.append({"role": "user", "content": user_input})
    
    payload = {
        "messages": messages,
        "max_new_tokens": 4000,
        "temperature": 1,
        "top_p": 0.9
    }
    return payload


def stream_local_llm_streaming(user_input, chat_history, chunk_queue, config):
    """
    Streams tokens from a local LLM using streaming.
    """
    payload = build_llm_payload(user_input, chat_history, config)
    full_response = ""
    max_chunk_length = config.get("max_chunk_length", 500)
    flush_token_count = config.get("flush_token_count", 10)
    
    # Create the SentenceBuilder and a dedicated token_queue.
    sentence_builder = SentenceBuilder(chunk_queue, max_chunk_length, flush_token_count)
    token_queue = Queue()  
    sb_thread = Thread(target=sentence_builder.run, args=(token_queue,))
    sb_thread.start()
    
    try:
        session = requests.Session()
        with session.post(config["LLM_STREAM_URL"], json=payload, stream=True) as response:
            response.raise_for_status()
            print("\n\nAssistant Response (streaming - local):\n", flush=True)
            for token in response.iter_content(chunk_size=1, decode_unicode=True):
                if not token:
                    continue
                full_response += token
                update_ui(token)
                token_queue.put(token)
        session.close()
        
        token_queue.put(None)
        sb_thread.join()
        return full_response.strip()
    
    except Exception as e:
        print(f"\nError during streaming local LLM call: {e}")
        return "Error: Streaming LLM call failed."

def stream_local_llm_non_streaming(user_input, chat_history, chunk_queue, config):
    """
    Calls a local LLM non-streaming endpoint and processes the entire response.
    """
    payload = build_llm_payload(user_input, chat_history, config)
    full_response = ""
    max_chunk_length = config.get("max_chunk_length", 500)
    flush_token_count = config.get("flush_token_count", 10)
    
    # Set up the SentenceBuilder.
    sentence_builder = SentenceBuilder(chunk_queue, max_chunk_length, flush_token_count)
    token_queue = Queue()
    sb_thread = Thread(target=sentence_builder.run, args=(token_queue,))
    sb_thread.start()
    
    try:
        session = requests.Session()
        response = session.post(config["LLM_API_URL"], json=payload)
        session.close()
        if response.ok:
            result = response.json()
            text = result.get('assistant', {}).get('content', "Error: No response.")
            print("Assistant Response (non-streaming - local):\n", flush=True)
            tokens = text.split(' ')
            for token in tokens:
                token_with_space = token + " "
                full_response += token_with_space
                update_ui(token_with_space)
                token_queue.put(token_with_space)
            
            token_queue.put(None)
            sb_thread.join()
            return full_response.strip()
        else:
            print(f"LLM call failed: HTTP {response.status_code}")
            return "Error: LLM call failed."
    
    except Exception as e:
        print(f"Error calling local LLM: {e}")
        return "Error: Exception occurred."



def stream_openai_llm_streaming(user_input, chat_history, chunk_queue, config):
    """
    Streams tokens from the OpenAI API.
    """
    payload = build_llm_payload(user_input, chat_history, config)
    full_response = ""
    max_chunk_length = config.get("max_chunk_length", 500)
    flush_token_count = config.get("flush_token_count", 10)
    
    # Set up the SentenceBuilder.
    sentence_builder = SentenceBuilder(chunk_queue, max_chunk_length, flush_token_count)
    token_queue = Queue()
    sb_thread = Thread(target=sentence_builder.run, args=(token_queue,))
    sb_thread.start()
    
    try:
        client = OpenAI(api_key=config["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=payload["messages"],
            max_tokens=4000,
            temperature=1,
            top_p=0.9,
            stream=True
        )
        print("Assistant Response (streaming - OpenAI):\n", flush=True)
        for chunk in response:
            token = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
            if not token:
                continue
            full_response += token
            update_ui(token)
            token_queue.put(token)
        
        token_queue.put(None)
        sb_thread.join()
        return full_response.strip()
    
    except Exception as e:
        print(f"Error calling OpenAI API (streaming): {e}")
        return "Error: OpenAI API call failed."



def stream_openai_llm_non_streaming(user_input, chat_history, chunk_queue, config):
    """
    Calls the OpenAI API without streaming.
    """
    payload = build_llm_payload(user_input, chat_history, config)
    full_response = ""
    max_chunk_length = config.get("max_chunk_length", 500)
    flush_token_count = config.get("flush_token_count", 10)
    
    # Set up the SentenceBuilder.
    sentence_builder = SentenceBuilder(chunk_queue, max_chunk_length, flush_token_count)
    token_queue = Queue()
    sb_thread = Thread(target=sentence_builder.run, args=(token_queue,))
    sb_thread.start()
    
    try:
        client = OpenAI(api_key=config["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=payload["messages"],
            max_tokens=4000,
            temperature=1,
            top_p=0.9
        )
        text = response.choices[0].message.content
        
        print("Assistant Response (non-streaming - OpenAI):\n", flush=True)
        tokens = text.split(' ')
        for token in tokens:
            token_with_space = token + " "
            full_response += token_with_space
            update_ui(token_with_space)
            token_queue.put(token_with_space)
        
        token_queue.put(None)
        sb_thread.join()
        return full_response.strip()
    
    except Exception as e:
        print(f"Error calling OpenAI API (non-streaming): {e}")
        return "Error: OpenAI API call failed."


def stream_llm_chunks(user_input, chat_history, chunk_queue, config):
    """
    Dispatches the LLM call to the proper variant based on the configuration.
    """
    USE_LOCAL_LLM = config["USE_LOCAL_LLM"]
    USE_STREAMING = config["USE_STREAMING"]
    
    if USE_LOCAL_LLM:
        if USE_STREAMING:
            return stream_local_llm_streaming(user_input, chat_history, chunk_queue, config)
        else:
            return stream_local_llm_non_streaming(user_input, chat_history, chunk_queue, config)
    else:
        if USE_STREAMING:
            return stream_openai_llm_streaming(user_input, chat_history, chunk_queue, config)
        else:
            return stream_openai_llm_non_streaming(user_input, chat_history, chunk_queue, config)


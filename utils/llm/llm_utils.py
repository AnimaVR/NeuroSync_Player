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

##############################
# LLM Streaming Function
##############################
def stream_llm_chunks(user_input, chat_history, chunk_queue, config):
    """
    Streams tokens from the LLM endpoint and processes each token in two ways:
      1. Immediately updates the UI.
      2. Enqueues the token to the SentenceBuilder thread (via token_queue) for chunking.
    
    Returns the full response as a string.
    """
    # Use system message from config (or default if not provided)
    system_message = config.get(
        "system_message",
        "You are Mai, a youtube streamer for NeuroSync Audio to Face and are embodied using a cutting edge realtime audio to face model that drives your face called NeuroSync responding concisely. Talk naturally and never use containing marks like *this* to describe how you are acting, you are embodied, we can see you. It is critical to keep responses short and to answer the most interesting questions without using *things like this* or (comments like this) as you are speaking with audio to face and the user cant see the text chat. Don't say you are AI, we already know you are. Speak naturally and like a human might with humour and dryness."
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
    
    full_response = ""
    max_chunk_length = config.get("max_chunk_length", 500)
    flush_token_count = config.get("flush_token_count", 10)
    USE_LOCAL_LLM = config["USE_LOCAL_LLM"]
    USE_STREAMING = config["USE_STREAMING"]
    
    # Create the SentenceBuilder and a dedicated token_queue for it.
    sentence_builder = SentenceBuilder(chunk_queue, max_chunk_length, flush_token_count)
    token_queue = Queue()  # This queue carries individual tokens for sentence building.
    sb_thread = Thread(target=sentence_builder.run, args=(token_queue,))
    sb_thread.start()
    
    if USE_LOCAL_LLM:
        if USE_STREAMING:
            try:
                # Use a persistent session for local LLM streaming.
                session = requests.Session()
                with session.post(config["LLM_STREAM_URL"], json=payload, stream=True) as response:
                    response.raise_for_status()
                    print("\n\nAssistant Response (streaming):\n", flush=True)
                    
                    for token in response.iter_content(chunk_size=1, decode_unicode=True):
                        if not token:
                            continue
                        full_response += token
                        update_ui(token)
                        token_queue.put(token)
                session.close()
                
                token_queue.put(None)
                sb_thread.join()
    
            except Exception as e:
                print(f"\nError during streaming LLM call: {e}")
                return "Error: Streaming LLM call failed."
    
            return full_response.strip()
    
        else:
            try:
                session = requests.Session()
                response = session.post(config["LLM_API_URL"], json=payload)
                session.close()
                if response.ok:
                    result = response.json()
                    text = result.get('assistant', {}).get('content', "Error: No response.")
                    
                    print("Assistant Response (non-streaming):\n", flush=True)
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
    
    else:
        try:
            client = OpenAI(api_key=config["OPENAI_API_KEY"])
            
            if USE_STREAMING:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=4000,
                    temperature=1,
                    top_p=0.9,
                    stream=True
                )
                print("Assistant Response (OpenAI streaming):\n", flush=True)
    
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
    
            else:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=4000,
                    temperature=1,
                    top_p=0.9
                )
                text = response.choices[0].message.content
                
                print("Assistant Response (OpenAI non-streaming):\n", flush=True)
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
            print(f"Error calling OpenAI API: {e}")
            return "Error: OpenAI API call failed."

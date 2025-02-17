# utils/llm_utils.py
import re
import requests
import openai

def chunk_text(text, max_chunk_length=500):
    """
    Splits text into chunks based on sentence boundaries and a maximum chunk length.
    Used in non-streaming mode.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if current_chunk:
            tentative = current_chunk + " " + sentence
        else:
            tentative = sentence
        if len(tentative) <= max_chunk_length:
            current_chunk = tentative
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def stream_llm_chunks(user_input, chat_history, chunk_queue, config):
    """
    Streams tokens from the LLM and buffers them into text chunks that end at sentence boundaries,
    exceed the maximum chunk length, or after a given number of tokens have been received.
    Each chunk is put into chunk_queue for TTS processing.
    Returns the full response as a string.
    
    config should be a dict containing:
      - USE_LOCAL_LLM (bool)
      - USE_STREAMING (bool)
      - LLM_API_URL (str)
      - LLM_STREAM_URL (str)
      - OPENAI_API_KEY (str)
      - max_chunk_length (int)
      - flush_token_count (int)  # flush after this many tokens if no punctuation seen
    """
    messages = [{"role": "system", "content": "You are an AI assistant responding concisely."}]
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
    
    buffer = ""
    full_response = ""
    token_count = 0
    max_chunk_length = config.get("max_chunk_length", 500)
    flush_token_count = config.get("flush_token_count", 10)
    USE_LOCAL_LLM = config["USE_LOCAL_LLM"]
    USE_STREAMING = config["USE_STREAMING"]
    
    if USE_LOCAL_LLM:
        if USE_STREAMING:
            try:
                with requests.post(config["LLM_STREAM_URL"], json=payload, stream=True) as response:
                    response.raise_for_status()
                    print("Assistant Response (streaming): ", end='\n\n', flush=True)
                    for token in response.iter_lines(decode_unicode=True):
                        if token:
                            print(token, end='\n\n', flush=True)
                            full_response += token
                            buffer += token
                            token_count += 1
                            # Flush if token ends with punctuation, buffer is long, or after flush_token_count tokens.
                            if (token.strip() and token.strip()[-1] in ".!?") or (len(buffer) >= max_chunk_length) or (token_count >= flush_token_count):
                                chunk_text_val = buffer.strip()
                                if chunk_text_val:
                                    chunk_queue.put(chunk_text_val)
                                buffer = ""
                                token_count = 0
                    if buffer.strip():
                        chunk_queue.put(buffer.strip())
            except Exception as e:
                print(f"Error during streaming LLM call: {e}")
                return "Error: Streaming LLM call failed."
            return full_response
        else:
            # Non-streaming mode: get full response then chunk it.
            try:
                response = requests.post(config["LLM_API_URL"], json=payload)
                if response.ok:
                    result = response.json()
                    text = result.get('assistant', {}).get('content', "Error: No response.")
                    for chunk in chunk_text(text, max_chunk_length):
                        chunk_queue.put(chunk)
                    return text
                else:
                    print(f"LLM call failed: HTTP {response.status_code}")
                    return "Error: LLM call failed."
            except Exception as e:
                print(f"Error calling local LLM: {e}")
                return "Error: Exception occurred."
    else:
        try:
            openai.api_key = config["OPENAI_API_KEY"]
            if USE_STREAMING:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=messages,
                    max_tokens=4000,
                    temperature=1,
                    top_p=0.9,
                    stream=True
                )
                for chunk in response:
                    token = chunk["choices"][0].get("delta", {}).get("content", "")
                    print(token, end='\n\n', flush=True)
                    full_response += token
                    buffer += token
                    token_count += 1
                    if (token.strip() and token.strip()[-1] in ".!?") or (len(buffer) >= max_chunk_length) or (token_count >= flush_token_count):
                        chunk_text_val = buffer.strip()
                        if chunk_text_val:
                            chunk_queue.put(chunk_text_val)
                        buffer = ""
                        token_count = 0
                if buffer.strip():
                    chunk_queue.put(buffer.strip())
                return full_response
            else:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=messages,
                    max_tokens=4000,
                    temperature=1,
                    top_p=0.9
                )
                text = response["choices"][0]["message"]["content"]
                for chunk in chunk_text(text, max_chunk_length):
                    chunk_queue.put(chunk)
                return text
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return "Error: OpenAI API call failed."

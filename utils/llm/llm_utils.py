import requests
from threading import Thread
from queue import Queue
import re
import string
from openai import OpenAI

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
            # Print the part
            print(part, end='', flush=True)
            # If not the last part, print an explicit newline.
            if i < len(parts) - 1:
                print()
    else:
        print(token, end='', flush=True)

##############################
# SentenceBuilder Class
##############################
class SentenceBuilder:
    """
    Accumulates tokens into sentences (or partial chunks) and flushes
    complete chunks to a provided chunk_queue for further processing.
    """
    SENTENCE_ENDINGS = {'.', '!', '?'}
    ABBREVIATIONS = {
        "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.", "st.",
        "vs.", "e.g.", "i.e.", "etc.", "p.s."
    }

    def __init__(self, chunk_queue, max_chunk_length=500, flush_token_count=300):
        self.chunk_queue = chunk_queue
        self.max_chunk_length = max_chunk_length
        self.flush_token_count = flush_token_count

        # Internal buffer to accumulate tokens
        self.buffer = []
        self.token_count = 0

    def add_token(self, token: str):
        """
        Add a token to the internal buffer.
        Flush the buffer if:
          - The token contains a newline (considered a sentence break).
          - The combined length exceeds max_chunk_length.
          - The token count exceeds flush_token_count.
          - A sentence-ending punctuation is encountered (unless it's an abbreviation).
        """
        self.buffer.append(token)
        self.token_count += 1

        # Flush immediately if the token contains a newline.
        if '\n' in token:
            self._flush_buffer()
            return

        # Flush if raw character length is exceeded
        if self._current_length() >= self.max_chunk_length:
            self._flush_buffer()
            return

        # Flush if token count is exceeded
        if self.token_count >= self.flush_token_count:
            self._flush_buffer()
            return

        # Flush if we detect a sentence end (unless it is an abbreviation)
        if self._ends_sentence(token):
            if not self._is_abbreviation():
                self._flush_buffer()

    def flush_remaining(self):
        """
        Flush any remaining tokens in the buffer.
        """
        if self.buffer:
            self._flush_buffer(force=True)

    def _current_length(self) -> int:
        """
        Return the combined length of the tokens in the buffer.
        """
        return sum(len(t) for t in self.buffer)

    def _ends_sentence(self, token: str) -> bool:
        """
        Return True if the token ends with punctuation that typically ends a sentence.
        """
        token = token.strip()
        if not token:
            return False
        return token[-1] in self.SENTENCE_ENDINGS

    def _is_abbreviation(self) -> bool:
        """
        Check if the last word in the buffer is an abbreviation.
        For example, "Dr." should not trigger a flush.
        """
        combined = ''.join(self.buffer).strip()
        if not combined:
            return False
        words = combined.split()
        if not words:
            return False
        last_word = words[-1].lower()
        return last_word in self.ABBREVIATIONS

    def _flush_buffer(self, force=False):
        chunk_text_val = ''.join(self.buffer).strip()
        # Clean the chunk text using the helper function.
        clean_chunk = clean_text_for_tts(chunk_text_val)
        if clean_chunk:  # Only enqueue if there's something meaningful.
            self.chunk_queue.put(clean_chunk)
        self.buffer = []
        self.token_count = 0

    def run(self, token_queue: Queue):
        """
        Continuously read tokens from the provided token_queue,
        process them, and flush when appropriate.
        """
        while True:
            token = token_queue.get()  # Wait until a token is available.
            if token is None:  # Sentinel value indicates no more tokens.
                break
            self.add_token(token)
            token_queue.task_done()
        # Flush any remaining tokens after exiting loop.
        self.flush_remaining()


def clean_text_for_tts(text: str) -> str:
    """
    Remove unwanted patterns from text:
      - Anything between asterisks, e.g. *some words*
      - Anything between parentheses, e.g. (some words)
    Then trim whitespace. If the result is empty or only punctuation,
    return an empty string.
    """
    # Remove text enclosed in asterisks (e.g., *example*)
    text = re.sub(r'\*[^*]+\*', '', text)
    # Remove text enclosed in parentheses (e.g., (example))
    text = re.sub(r'\([^)]*\)', '', text)
    # Trim whitespace
    clean_text = text.strip()
    # If the cleaned text is empty, exactly '...', or only punctuation/spaces, return empty.
    if (not clean_text or clean_text == "..." or 
        all(char in string.punctuation or char.isspace() for char in clean_text)):
        return ""
    return clean_text


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
    # Build messages from chat history and user input
    messages = [{"role": "system", "content": "You are Mai, a youtube streamer for NeuroSync Audio to Face and are embodied using a cutting edge realtime audio to face model that drives your face called NeuroSync responding concisely. Talk naturally and never use containing marks like *this* to describe how you are acting, you are embodied, we can see you. It is critical to keep responses short and to answer the most interesting questions without using *things like this* or (comments like this) as you are speaking with audio to face and the user cant see the text chat. Don't say you are AI, we already know you are. Speak naturally and like a human might with humour and dryness."}]
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
                # CHANGED: Use a persistent session for local LLM streaming.
                session = requests.Session()
                with session.post(config["LLM_STREAM_URL"], json=payload, stream=True) as response:
                    response.raise_for_status()
                    print("\n\nAssistant Response (streaming):\n", flush=True)
                    
                    # Process tokens as soon as they are available.
                    for token in response.iter_content(chunk_size=1, decode_unicode=True):
                        if not token:
                            continue
                        full_response += token
                        update_ui(token)
                        token_queue.put(token)
                session.close()  # Close the session after use.
                
                # Signal the SentenceBuilder thread that we are done.
                token_queue.put(None)
                sb_thread.join()
    
            except Exception as e:
                print(f"\nError during streaming LLM call: {e}")
                return "Error: Streaming LLM call failed."
    
            return full_response.strip()
    
        else:
            try:
                # CHANGED: Use a persistent session for non-streaming local LLM.
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
        # Using OpenAI's API with the new SDK (v1.0.0+)
        try:
            client = OpenAI(api_key=config["OPENAI_API_KEY"])
            
            if USE_STREAMING:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=4000,
                    temperature=1,
                    top_p=0.9,
                    stream=True  # Ensure streaming is enabled
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

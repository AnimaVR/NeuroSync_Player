import re
import requests
import openai

class SentenceBuilder:
    SENTENCE_ENDINGS = {'.', '!', '?'}
    ABBREVIATIONS = {
        "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.", "st.", 
        "vs.", "e.g.", "i.e.", "etc.", "p.s."
        # Add more as needed
    }

    def __init__(self, chunk_queue, max_chunk_length=500, flush_token_count=50):
        self.chunk_queue = chunk_queue
        self.max_chunk_length = max_chunk_length
        self.flush_token_count = flush_token_count

        # Internal buffer for building up the current sentence
        self.buffer = []
        self.token_count = 0

    def add_token(self, token: str):
        """
        Add a single token to the internal buffer.
        If a sentence boundary is detected (and not an abbreviation),
        flush the buffer to the chunk_queue.
        Also flush if we exceed max_chunk_length or flush_token_count.
        """

        # Print partial token so user sees streaming in console
        print(token, end='', flush=True)

        # Add token to buffer
        self.buffer.append(token)
        self.token_count += 1

        # If we exceed the raw character limit, flush
        if self._current_length() >= self.max_chunk_length:
            self._flush_buffer()
            return

        # If we exceed token count, flush
        if self.token_count >= self.flush_token_count:
            self._flush_buffer()
            return

        # Check for sentence completion
        if self._ends_sentence(token):
            # But check if it's an abbreviation
            if not self._is_abbreviation():
                # If it's a real sentence boundary (not an abbreviation), flush
                self._flush_buffer()

    def flush_remaining(self):
        """
        Flush any remaining text in the buffer if it’s non-empty.
        """
        if self.buffer:
            self._flush_buffer(force=True)

    def _current_length(self) -> int:
        """
        Returns the combined character length of the buffer.
        """
        return sum(len(t) for t in self.buffer)

    def _ends_sentence(self, token: str) -> bool:
        """
        Returns True if the token ends with a punctuation from SENTENCE_ENDINGS.
        """
        token = token.strip()
        if not token:
            return False
        return token[-1] in self.SENTENCE_ENDINGS

    def _is_abbreviation(self) -> bool:
        """
        Check the last "word" in buffer. If the last word is in ABBREVIATIONS,
        we consider it not a true sentence end. For example "Dr." or "Mr."
        """
        # Combine buffer as a single string, then split by whitespace
        combined = ''.join(self.buffer).strip()
        if not combined:
            return False

        # The last word might have punctuation
        words = combined.split()
        if not words:
            return False

        last_word = words[-1].lower()  # e.g. "Dr."
        return last_word in self.ABBREVIATIONS

    def _flush_buffer(self, force=False):
        """
        Sends the current buffer to the chunk_queue, then resets counters.
        If force=True, we just flush whatever is in the buffer.
        """
        chunk_text_val = ''.join(self.buffer).strip()
        if chunk_text_val:
            self.chunk_queue.put(chunk_text_val)

        # Reset
        self.buffer = []
        self.token_count = 0

        if not force:
            # Print a slight line-break for readability after a sentence
            print("\n", end='', flush=True)


def stream_llm_chunks(user_input, chat_history, chunk_queue, config):
    """
    Streams tokens from the LLM and uses SentenceBuilder to accumulate
    tokens into sentences (or partial chunks).
    Each chunk is then put into chunk_queue for TTS processing.

    Returns the full response as a string.
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
    
    full_response = ""
    max_chunk_length = config.get("max_chunk_length", 500)
    flush_token_count = config.get("flush_token_count", 10)
    USE_LOCAL_LLM = config["USE_LOCAL_LLM"]
    USE_STREAMING = config["USE_STREAMING"]
    
    # --- CHANGED: Use the new SentenceBuilder ---
    sentence_builder = SentenceBuilder(
        chunk_queue,
        max_chunk_length=max_chunk_length,
        flush_token_count=flush_token_count
    )

    if USE_LOCAL_LLM:
        if USE_STREAMING:
            try:
                with requests.post(config["LLM_STREAM_URL"], json=payload, stream=True) as response:
                    response.raise_for_status()
                    print("Assistant Response (streaming): \n", flush=True)
                    
                    for raw_line in response.iter_lines(decode_unicode=True):
                        if not raw_line:
                            continue

                        # The streaming endpoint might send chunked tokens or lines
                        # Splitting so we handle tokens individually
                        # Some endpoints might return entire strings at once, so we carefully split
                        tokens = raw_line.split(' ')
                        for token in tokens:
                            full_response += token + " "
                            # Add token to sentence builder
                            sentence_builder.add_token(token + " ")  # Keep spacing

                    # After the loop ends, flush any partial sentence
                    sentence_builder.flush_remaining()

            except Exception as e:
                print(f"Error during streaming LLM call: {e}")
                return "Error: Streaming LLM call failed."

            return full_response.strip()

        else:
            # --- Non-streaming path: get the full text, then feed it token by token to the SentenceBuilder ---
            try:
                response = requests.post(config["LLM_API_URL"], json=payload)
                if response.ok:
                    result = response.json()
                    text = result.get('assistant', {}).get('content', "Error: No response.")
                    
                    # We'll parse it token-by-token
                    print("Assistant Response (non-streaming): \n", flush=True)
                    tokens = text.split(' ')
                    for token in tokens:
                        full_response += token + " "
                        sentence_builder.add_token(token + " ")
                    
                    # Flush
                    sentence_builder.flush_remaining()
                    return full_response.strip()
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
                print("Assistant Response (OpenAI streaming): \n", flush=True)

                for chunk in response:
                    token = chunk["choices"][0].get("delta", {}).get("content", "")
                    if not token:
                        continue

                    # Print partial token and feed into builder
                    full_response += token
                    sentence_builder.add_token(token)

                sentence_builder.flush_remaining()
                return full_response.strip()

            else:
                # Non-streaming path with OpenAI
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=messages,
                    max_tokens=4000,
                    temperature=1,
                    top_p=0.9
                )
                text = response["choices"][0]["message"]["content"]
                
                print("Assistant Response (OpenAI non-streaming): \n", flush=True)
                tokens = text.split(' ')
                for token in tokens:
                    full_response += token + " "
                    sentence_builder.add_token(token + " ")
                
                sentence_builder.flush_remaining()
                return full_response.strip()

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return "Error: OpenAI API call failed."

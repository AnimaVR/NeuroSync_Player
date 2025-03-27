# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

import re
import string
from queue import Queue

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

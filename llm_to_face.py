import os
import json
import re  # for splitting text into sentences
from threading import Thread
from queue import Queue
import pygame
import requests
import openai

from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

from utils.api_utils import save_generated_data, initialize_directories
from utils.generated_utils import run_audio_animation_from_bytes
from utils.neurosync_api_connect import send_audio_to_neurosync

from utils.local_tts import call_local_tts 
from utils.eleven_labs import get_elevenlabs_audio

# Constants
USE_LOCAL_LLM = True      # Set to False to use OpenAI API
USE_STREAMING = True      # Enable streaming tokens
LLM_API_URL = "http://192.168.1.1:5050/generate_llama"
LLM_STREAM_URL = "http://192.168.1.1:5050/generate_stream"
CHAT_LOGS_DIR = "chat_logs"
VOICE_NAME = 'Lily'
MAX_CONTEXT_LENGTH = 5000
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Set your OpenAI API key in environment variables

# Flag for local audio generation using your Flask TTS endpoint
USE_LOCAL_AUDIO = True    # Set to True to use local TTS; if False, use ElevenLabs

# Ensure chat_logs directory exists
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
        chat_history.pop(0)  # Remove oldest log
        total_length = sum(len(json.dumps(entry)) for entry in chat_history)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, indent=4)

def call_llm(user_input, chat_history):
    """
    Calls either the local LLM (via streaming or standard endpoint) or the OpenAI API,
    and prints tokens as they are received if streaming is enabled.
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
    
    if USE_LOCAL_LLM:
        if USE_STREAMING:
            try:
                with requests.post(LLM_STREAM_URL, json=payload, stream=True) as response:
                    response.raise_for_status()
                    full_response = ""
                    print("Assistant Response (streaming): ", end='', flush=True)
                    for chunk in response.iter_lines(decode_unicode=True):
                        if chunk:
                            print(chunk, end='', flush=True)
                            full_response += chunk
                    print()  # Newline after streaming completes
                    return full_response
            except Exception as e:
                print(f"Error during streaming LLM call: {e}")
                return "Error: Streaming LLM call failed."
        else:
            try:
                response = requests.post(LLM_API_URL, json=payload)
                if response.ok:
                    result = response.json()
                    return result.get('assistant', {}).get('content', "Error: No response.")
                else:
                    print(f"LLM call failed: HTTP {response.status_code}")
                    return "Error: LLM call failed."
            except Exception as e:
                print(f"Error calling local LLM: {e}")
                return "Error: Exception occurred."
    else:
        try:
            openai.api_key = OPENAI_API_KEY
            if USE_STREAMING:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=messages,
                    max_tokens=4000,
                    temperature=1,
                    top_p=0.9,
                    stream=True
                )
                full_response = ""
                print("Assistant Response (streaming): ", end='', flush=True)
                for chunk in response:
                    token = chunk["choices"][0].get("delta", {}).get("content", "")
                    print(token, end='', flush=True)
                    full_response += token
                print()  # Newline after streaming is complete
                return full_response
            else:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=messages,
                    max_tokens=4000,
                    temperature=1,
                    top_p=0.9
                )
                return response["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return "Error: OpenAI API call failed."

def chunk_text(text, max_chunk_length=500):
    """
    Splits text into chunks, ensuring that chunks end at sentence boundaries
    and are no longer than max_chunk_length.
    """
    # Split text into sentences based on punctuation.
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

def audio_queue_worker(audio_queue, py_face, socket_connection, default_animation_thread):
    """
    Worker function to process audio items from the queue sequentially.
    Each item is a tuple (audio_bytes, facial_data) that will be played back.
    """
    while True:
        item = audio_queue.get()
        if item is None:
            break
        audio_bytes, facial_data = item
        # This function should block until the audio and face animation finish playing.
        run_audio_animation_from_bytes(audio_bytes, facial_data, py_face, socket_connection, default_animation_thread)
        audio_queue.task_done()

def main():
    initialize_directories()
    py_face = initialize_py_face()
    socket_connection = create_socket_connection()
    chat_history = load_chat_history()
    
    default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
    default_animation_thread.start()
    
    # Create a queue for audio chunks
    audio_queue = Queue()
    
    # Start a worker thread to process audio chunks sequentially
    audio_worker_thread = Thread(target=audio_queue_worker, args=(audio_queue, py_face, socket_connection, default_animation_thread))
    audio_worker_thread.start()
    
    try:
        while True:
            user_input = input("Enter text (or 'q' to quit): ").strip()
            if user_input.lower() == 'q':
                break
            
            # Get the full LLM response
            llm_response = call_llm(user_input, chat_history)
            print(f"\nLLM Response (final): {llm_response}")
            
            chat_history.append({"input": user_input, "response": llm_response})
            save_chat_log(chat_history)
            
            # Chunk the LLM response into segments based on sentence boundaries and max length
            text_chunks = chunk_text(llm_response, max_chunk_length=1000)
            print("Text chunks:", text_chunks)
            
            for chunk in text_chunks:
                # Generate audio for the chunk using the selected TTS
                if USE_LOCAL_AUDIO:
                    audio_bytes = call_local_tts(chunk)
                else:
                    audio_bytes = get_elevenlabs_audio(chunk, VOICE_NAME)
                
                if audio_bytes:
                    # Get the facial data for the audio chunk
                    facial_data = send_audio_to_neurosync(audio_bytes)
                    if facial_data:
                        # Queue the audio and facial data for sequential playback
                        audio_queue.put((audio_bytes, facial_data))
                    else:
                        print("Failed to get blendshapes from API for chunk:", chunk)
                else:
                    print("Failed to generate audio for chunk:", chunk)
    
    finally:
        # Wait until all queued audio items have been processed
        audio_queue.join()
        # Signal the audio worker to exit
        audio_queue.put(None)
        audio_worker_thread.join()
        
        stop_default_animation.set()
        default_animation_thread.join()
        pygame.quit()
        socket_connection.close()

if __name__ == "__main__":
    main()

# llm_to_face.py

import os
from threading import Thread, Event
from queue import Queue, Empty
import pygame

from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

from utils.api_utils import initialize_directories
from utils.chat_utils import load_chat_history, save_chat_log
from utils.llm_utils import stream_llm_chunks
from utils.audio_workers import tts_worker, audio_queue_worker

# Constants
USE_LOCAL_LLM = True      # Set to False to use OpenAI API
USE_STREAMING = True      # Enable streaming tokens
LLM_API_URL = "http://192.168.1.1:5050/generate_llama"
LLM_STREAM_URL = "http://192.168.1.1:5050/generate_stream"
VOICE_NAME = 'Lily'
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Set your OpenAI API key in environment variables

# Flag for local audio generation using your Flask TTS endpoint
USE_LOCAL_AUDIO = True    # Set to True to use local TTS; if False, use ElevenLabs by adding your api to to utils/eleven_labs.py

# LLM configuration dictionary (used by stream_llm_chunks)
llm_config = {
    "USE_LOCAL_LLM": USE_LOCAL_LLM,
    "USE_STREAMING": USE_STREAMING,
    "LLM_API_URL": LLM_API_URL,
    "LLM_STREAM_URL": LLM_STREAM_URL,
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "max_chunk_length": 500,
    "flush_token_count": 10  
}

def flush_queue(q):
    try:
        while True:
            q.get_nowait()
    except Empty:
        pass

def main():
    initialize_directories()
    py_face = initialize_py_face()
    socket_connection = create_socket_connection()
    chat_history = load_chat_history()
    
    default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
    default_animation_thread.start()
    
    # Create queues:
    # 1. chunk_queue for text chunks to be processed by TTS.
    # 2. audio_queue for the resulting audio/facial-data pairs.
    chunk_queue = Queue()
    audio_queue = Queue()
    
    # Start the TTS worker (processes text chunks into audio)
    tts_worker_thread = Thread(target=tts_worker, args=(chunk_queue, audio_queue, USE_LOCAL_AUDIO, VOICE_NAME))
    tts_worker_thread.start()
    
    # Start the audio worker (plays audio sequentially)
    audio_worker_thread = Thread(target=audio_queue_worker, args=(audio_queue, py_face, socket_connection, default_animation_thread))
    audio_worker_thread.start()
    
    try:
        while True:
            user_input = input("Enter text (or 'q' to quit): ").strip()
            if user_input.lower() == 'q':
                break

            # Interrupt current playback:
            flush_queue(chunk_queue)
            flush_queue(audio_queue)
            # Stop any current audio playback. Adjust if you have a custom stop mechanism.
            if pygame.mixer.get_init():
                pygame.mixer.stop()

            
            # Stream the LLM response; text chunks are enqueued as they are detected.
            full_response = stream_llm_chunks(user_input, chat_history, chunk_queue, config=llm_config)
           # print(f"\nLLM Response (final): {full_response}")
            
            chat_history.append({"input": user_input, "response": full_response})
            save_chat_log(chat_history)

    finally:
        # Wait until all text chunks have been processed
        chunk_queue.join()
        # Signal the TTS worker to exit
        chunk_queue.put(None)
        tts_worker_thread.join()
        
        # Wait until all audio items have been played
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

import os
import time
import threading  # for Lock
from threading import Thread, Lock
from queue import Queue, Empty
import pygame
import warnings
warnings.filterwarnings(
    "ignore", 
    message="Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work"
)

import keyboard  
import time      

# === Original Imports and Functions ===
from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

from utils.tts.tts_bridge import tts_worker
from utils.files.file_utils import initialize_directories
from utils.llm.chat_utils import load_chat_history, save_chat_log
from utils.llm.llm_utils import stream_llm_chunks 
from utils.audio_face_workers import audio_face_queue_worker
from utils.stt.transcribe_whisper import transcribe_audio
from utils.audio.record_audio import record_audio_until_release

# Configuration for LLM and audio
USE_LOCAL_LLM = True     
USE_STREAMING = True   
LLM_API_URL = "http://127.0.0.1:5050/generate_llama"
LLM_STREAM_URL = "http://127.0.0.1:5050/generate_stream"
VOICE_NAME = 'Lily'
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  
USE_LOCAL_AUDIO = True 

llm_config = {
    "USE_LOCAL_LLM": USE_LOCAL_LLM,
    "USE_STREAMING": USE_STREAMING,
    "LLM_API_URL": LLM_API_URL,
    "LLM_STREAM_URL": LLM_STREAM_URL,
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "max_chunk_length": 500,
    "flush_token_count": 300  
}

def flush_queue(q):
    try:
        while True:
            q.get_nowait()
    except Empty:
        pass

# === YouTube Chat Worker Code (Replaces Twitch Integration) ===
# Make sure to install google-api-python-client: pip install google-api-python-client
try:
    from googleapiclient.discovery import build
except ImportError:
    print("google-api-python-client not found. Please install it using 'pip install google-api-python-client'")
    exit(1)

# YouTube configuration from environment variables
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
YOUTUBE_LIVE_CHAT_ID = os.getenv("YOUTUBE_LIVE_CHAT_ID", "")
# Optionally, if live chat ID isn't provided, provide your live video's ID:
YOUTUBE_VIDEO_ID = os.getenv("YOUTUBE_VIDEO_ID", "")

# --- NEW: Function to retrieve live chat ID from a live video ---
def get_live_chat_id(api_key, video_id):
    """
    Given a live broadcast video ID, retrieve its liveChatId.
    """
    youtube = build('youtube', 'v3', developerKey=api_key)
    response = youtube.videos().list(
        part="liveStreamingDetails",
        id=video_id
    ).execute()
    if response.get('items'):
        live_chat_id = response['items'][0]['liveStreamingDetails'].get('activeLiveChatId')
        return live_chat_id
    return None

def run_youtube_chat_fetcher(message_queue, api_key, live_chat_id):
    """
    Polls the YouTube Live Chat API for new messages and enqueues them.
    If an invalid page token error is encountered, resets the token.
    """
    youtube = build('youtube', 'v3', developerKey=api_key)
    next_page_token = None
    while True:
        try:
            params = {
                'liveChatId': live_chat_id,
                'part': "snippet,authorDetails"
            }
            if next_page_token:
                params['pageToken'] = next_page_token
            response = youtube.liveChatMessages().list(**params).execute()
        except Exception as e:
            error_str = str(e)
            if "page token is not valid" in error_str or "pageTokenInvalid" in error_str:
                print("Invalid page token detected; resetting token.")
                next_page_token = None
                time.sleep(2)  # short delay before retrying
                continue
            print(f"Error fetching YouTube chat messages: {e}")
            time.sleep(5)
            continue

        if 'items' in response:
            for item in response['items']:
                snippet = item.get('snippet', {})
                author = item.get('authorDetails', {})
                timestamp = snippet.get('publishedAt', '')
                message_text = snippet.get('displayMessage', '')
                formatted = f"[{timestamp}] {author.get('displayName', 'Unknown')}: {message_text}"
                message_queue.put(formatted)

        next_page_token = response.get('nextPageToken')
        polling_interval = response.get('pollingIntervalMillis', 1000) / 1000.0
        time.sleep(polling_interval)

def youtube_input_worker(youtube_queue, chat_history, chunk_queue, llm_lock):
    """
    Worker that checks the YouTube queue every 0.5 seconds.
    When a new chat message is found, it processes it with the LLM endpoint.
    """
    while True:
        try:
            youtube_message = youtube_queue.get(timeout=0.5)
            if youtube_message:
                print("\nYouTube chat input detected:")
                print(youtube_message)
                with llm_lock:
                    flush_queue(chunk_queue)
                    if pygame.mixer.get_init():
                        pygame.mixer.stop()
                    # Process the YouTube message via the LLM endpoint
                    full_response = stream_llm_chunks(youtube_message, chat_history, chunk_queue, config=llm_config)
                    chat_history.append({"input": youtube_message, "response": full_response})
                    save_chat_log(chat_history)
        except Empty:
            continue

# === Main Function (Original Functionality Remains) ===
def main():
    # Initialize directories and connections
    initialize_directories()
    py_face = initialize_py_face()
    socket_connection = create_socket_connection()
    chat_history = load_chat_history()
    
    # Start default face animation
    default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
    default_animation_thread.start()
    
    # Create queues for TTS and audio
    chunk_queue = Queue()
    audio_queue = Queue()
    tts_worker_thread = Thread(target=tts_worker, args=(chunk_queue, audio_queue, USE_LOCAL_AUDIO, VOICE_NAME))
    tts_worker_thread.start()
    audio_worker_thread = Thread(target=audio_face_queue_worker, args=(audio_queue, py_face, socket_connection, default_animation_thread))
    audio_worker_thread.start()
    
    # === Dynamically Retrieve YouTube Live Chat ID if Not Provided ===
    global YOUTUBE_LIVE_CHAT_ID
    if not YOUTUBE_LIVE_CHAT_ID:
        if not YOUTUBE_VIDEO_ID:
            print("Neither YOUTUBE_LIVE_CHAT_ID nor YOUTUBE_VIDEO_ID provided. Cannot fetch live chat.")
            exit(1)
        YOUTUBE_LIVE_CHAT_ID = get_live_chat_id(YOUTUBE_API_KEY, YOUTUBE_VIDEO_ID)
        if not YOUTUBE_LIVE_CHAT_ID:
            print("Could not retrieve a live chat id from the provided video id. Is the broadcast live?")
            exit(1)
        else:
            print("Dynamically retrieved YouTube Live Chat ID")
    
    # === Start YouTube Chat Worker Threads (Replaces Twitch Setup) ===
    youtube_queue = Queue()  # Queue for YouTube messages
    llm_lock = Lock()       # Lock to ensure only one LLM call is processed at a time
    
    youtube_fetcher_thread = Thread(target=run_youtube_chat_fetcher, args=(youtube_queue, YOUTUBE_API_KEY, YOUTUBE_LIVE_CHAT_ID))
    youtube_fetcher_thread.daemon = True
    youtube_fetcher_thread.start()
    
    youtube_worker_thread = Thread(target=youtube_input_worker, args=(youtube_queue, chat_history, chunk_queue, llm_lock))
    youtube_worker_thread.daemon = True
    youtube_worker_thread.start()
    
    # Ask for input mode once: 't' for text, 'r' for push-to-talk recording, 'q' to quit
    mode = ""
    while mode not in ['t', 'r']:
        mode = input("Choose input mode: type 't' for text input or 'r' for push-to-talk recording (or 'q' to quit): ").strip().lower()
        if mode == 'q':
            return

    try:
        while True:
            if mode == 'r':
                print("\n\nPush-to-talk mode: Press and hold the Right Ctrl key to record, then release to finish (or press 'q' to cancel).")
                while not keyboard.is_pressed('right ctrl'):
                    if keyboard.is_pressed('q'):
                        print("Recording cancelled. Exiting push-to-talk mode.")
                        return
                    time.sleep(0.01)
                audio_bytes = record_audio_until_release()
                transcription, _ = transcribe_audio(audio_bytes)
                if transcription:
                    user_input = transcription
                else:
                    print("Transcription failed. Please try again.")
                    continue
            else:
                user_input = input("Enter text (or 'q' to quit): ").strip()
                if user_input.lower() == 'q':
                    break

            with llm_lock:
                flush_queue(chunk_queue)
                flush_queue(audio_queue)
                if pygame.mixer.get_init():
                    pygame.mixer.stop()
                full_response = stream_llm_chunks(user_input, chat_history, chunk_queue, config=llm_config)
                chat_history.append({"input": user_input, "response": full_response})
                save_chat_log(chat_history)

    finally:
        chunk_queue.join()
        chunk_queue.put(None)
        tts_worker_thread.join()
        audio_queue.join()
        audio_queue.put(None)
        audio_worker_thread.join()
        stop_default_animation.set()
        default_animation_thread.join()
        pygame.quit()
        socket_connection.close()

if __name__ == "__main__":
    main()



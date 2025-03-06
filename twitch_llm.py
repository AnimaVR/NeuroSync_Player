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

# === New Twitch Chat Worker Code ===
# Make sure to install twitchio: pip install twitchio
try:
    from twitchio.ext import commands
except ImportError:
    print("twitchio library not found. Please install it using 'pip install twitchio'")
    exit(1)

# Twitch configuration (adjust or set these in your environment)
TWITCH_NICK = os.getenv("TWITCH_NICK", "")
TWITCH_TOKEN = os.getenv("TWITCH_TOKEN", "oauth:")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL", "")

class TwitchChatBot(commands.Bot):
    """
    TwitchChatBot connects to Twitch using twitchio and enqueues every incoming
    chat message into the provided message_queue.
    """
    def __init__(self, message_queue, nick, token, channel):
        # Use 'token' instead of 'irc_token'
        super().__init__(token=token, nick=nick, prefix="!", initial_channels=[channel])
        self.message_queue = message_queue


    async def event_ready(self):
        print(f"Connected to Twitch chat as {self.nick}")

    async def event_message(self, message):
        # Avoid processing messages sent by the bot itself.
        if message.echo:
            return
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        formatted = f"[{timestamp}] {message.author.name}: {message.content}"
        # Enqueue the formatted message.
        self.message_queue.put(formatted)

def run_twitch_bot(message_queue, nick, token, channel):
    import asyncio
    # Create and set a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot = TwitchChatBot(message_queue, nick, token, channel)
    bot.run()


def twitch_input_worker(twitch_queue, chat_history, chunk_queue, llm_lock):
    """
    Worker that checks the twitch_queue every 0.5 seconds.
    When a new chat message is found, it processes it with the LLM endpoint.
    """
    while True:
        try:
            twitch_message = twitch_queue.get(timeout=0.5)
            if twitch_message:
                print("\nTwitch chat input detected:")
                print(twitch_message)
                # Ensure only one LLM call happens at a time
                with llm_lock:
                    flush_queue(chunk_queue)  # flush chunk queue before processing
                    if pygame.mixer.get_init():
                        pygame.mixer.stop()
                    # Process the Twitch message via the LLM endpoint
                    full_response = stream_llm_chunks(twitch_message, chat_history, chunk_queue, config=llm_config)
                    chat_history.append({"input": twitch_message, "response": full_response})
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
    
    # === Start Twitch Chat Worker Threads ===
    # Create a queue for Twitch chat messages.
    twitch_queue = Queue()
    # Create a lock to ensure that only one LLM call is processed at a time.
    llm_lock = Lock()
    
    # Start the Twitch chat bot in a separate thread.
    twitch_bot_thread = Thread(target=run_twitch_bot, args=(twitch_queue, TWITCH_NICK, TWITCH_TOKEN, TWITCH_CHANNEL))
    twitch_bot_thread.daemon = True  # Daemonize so it doesn't block exit.
    twitch_bot_thread.start()
    
    # Start a worker thread that checks the Twitch queue every 0.5 seconds.
    twitch_worker_thread = Thread(target=twitch_input_worker, args=(twitch_queue, chat_history, chunk_queue, llm_lock))
    twitch_worker_thread.daemon = True
    twitch_worker_thread.start()
    # === End of Twitch Chat Worker Setup ===
    
    # Ask for input mode once: 't' for text, 'r' for push-to-talk recording, 'q' to quit
    mode = ""
    while mode not in ['t', 'r']:
        mode = input("Choose input mode: type 't' for text input or 'r' for push-to-talk recording (or 'q' to quit): ").strip().lower()
        if mode == 'q':
            return

    try:
        while True:
            if mode == 'r':
                # Push-to-talk mode (always record using Right Ctrl)
                print("\n\nPush-to-talk mode: Press and hold the Right Ctrl key to record, then release to finish (or press 'q' to cancel).")
                # Wait until the user presses Right Ctrl (with a small delay to avoid busy waiting)
                while not keyboard.is_pressed('right ctrl'):
                    if keyboard.is_pressed('q'):
                        print("Recording cancelled. Exiting push-to-talk mode.")
                        return  # Alternatively, you might break out or switch mode
                    time.sleep(0.01)
                # Record until Right Ctrl is released
                audio_bytes = record_audio_until_release()
                transcription, _ = transcribe_audio(audio_bytes)
                if transcription:
                    user_input = transcription
                else:
                    print("Transcription failed. Please try again.")
                    continue
            else:
                # Text input mode
                user_input = input("Enter text (or 'q' to quit): ").strip()
                if user_input.lower() == 'q':
                    break

            # Ensure only one LLM call happens at a time.
            with llm_lock:
                flush_queue(chunk_queue)
                flush_queue(audio_queue)
                if pygame.mixer.get_init():
                    pygame.mixer.stop()
                full_response = stream_llm_chunks(user_input, chat_history, chunk_queue, config=llm_config)
                chat_history.append({"input": user_input, "response": full_response})
                save_chat_log(chat_history)

    finally:
        # Clean up all threads and close connections
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

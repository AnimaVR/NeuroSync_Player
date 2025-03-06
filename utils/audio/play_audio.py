"""
play_audio.py
-----------------
This module provides functions to play audio using Pygame. It includes
helper functions for initializing the mixer and unified playback loops.
It also supports audio conversion on the fly (e.g. raw PCM to WAV) where needed.
"""

import io
import time
import pygame
from utils.audio.convert_audio import pcm_to_wav, convert_to_wav

# --- Helper Functions ---

def init_pygame_mixer():
    """
    Initialize the Pygame mixer only once.
    """
    if not pygame.mixer.get_init():
        pygame.mixer.init()


def sync_playback_loop():
    """
    A playback loop that synchronizes elapsed time with the music position.
    """
    start_time = time.perf_counter()
    clock = pygame.time.Clock()
    while pygame.mixer.music.get_busy():
        elapsed_time = time.perf_counter() - start_time
        current_pos = pygame.mixer.music.get_pos() / 1000.0  # convert ms to sec

        # If behind, sleep briefly; if ahead, let it catch up.
        if elapsed_time > current_pos:
            time.sleep(0.01)
        elif elapsed_time < current_pos:
            continue
        clock.tick(10)


def simple_playback_loop():
    """
    A simple playback loop that just ticks the clock until playback finishes.
    """
    clock = pygame.time.Clock()
    while pygame.mixer.music.get_busy():
        clock.tick(10)


# --- Playback Functions ---

def play_audio_bytes(audio_bytes, start_event, sync=True):
    """
    Play audio from raw bytes.
    
    Parameters:
      - audio_bytes: audio data as bytes.
      - start_event: threading.Event to wait for before starting playback.
      - sync: if True, uses time-syncing playback loop.
    """
    try:
        init_pygame_mixer()
        audio_file = io.BytesIO(audio_bytes)
        pygame.mixer.music.load(audio_file)
        start_event.wait()  # Wait for the signal to start
        pygame.mixer.music.play()
        if sync:
            sync_playback_loop()
        else:
            simple_playback_loop()
    except pygame.error as e:
        print(f"Error in play_audio_bytes: {e}")


def play_audio_from_memory_openai(audio_data, start_event, sync=True):
    """
    Play audio from memory with potential PCM-to-WAV conversion.
    
    If the audio data does not start with the WAV header ('RIFF'), assume
    it is raw PCM and convert it.
    """
    try:
        init_pygame_mixer()
        if not audio_data.startswith(b'RIFF'):
            # Convert raw PCM to WAV using default parameters.
            audio_file = pcm_to_wav(audio_data, sample_rate=22050, channels=1, sample_width=2)
        else:
            audio_file = io.BytesIO(audio_data)
        pygame.mixer.music.load(audio_file)
        start_event.wait()
        pygame.mixer.music.play()
        if sync:
            sync_playback_loop()
        else:
            simple_playback_loop()
    except pygame.error as e:
        print(f"Error in play_audio_from_memory_openai: {e}")


def play_audio_from_memory(audio_data, start_event, sync=False):
    """
    Play audio from memory (assumes valid WAV bytes).
    Uses a simple playback loop.
    """
    try:
        init_pygame_mixer()
        audio_file = io.BytesIO(audio_data)
        pygame.mixer.music.load(audio_file)
        start_event.wait()
        pygame.mixer.music.play()
        simple_playback_loop()
    except pygame.error as e:
        if "Unknown WAVE format" in str(e):
            print("Unknown WAVE format encountered. Skipping to the next item in the queue.")
        else:
            print(f"Error in play_audio_from_memory: {e}")
    except Exception as e:
        print(f"Error in play_audio_from_memory: {e}")


def play_audio_from_path(audio_path, start_event, sync=True):
    """
    Play audio from a file path. If the format is unsupported,
    automatically convert it to WAV.
    """
    try:
        init_pygame_mixer()
        try:
            pygame.mixer.music.load(audio_path)
        except pygame.error:
            print(f"Unsupported format for {audio_path}. Converting to WAV.")
            audio_path = convert_to_wav(audio_path)
            pygame.mixer.music.load(audio_path)
        start_event.wait()
        pygame.mixer.music.play()
        if sync:
            sync_playback_loop()
        else:
            simple_playback_loop()
    except pygame.error as e:
        print(f"Error in play_audio_from_path: {e}")


def read_audio_file_as_bytes(file_path):
    """
    Read a WAV audio file from disk as bytes.
    Only WAV files are supported.
    """
    if not file_path.lower().endswith('.wav'):
        print(f"Unsupported file format: {file_path}. Only WAV files are supported.")
        return None
    try:
        with open(file_path, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error reading audio file: {e}")
        return None

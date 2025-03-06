# This code is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
# For more details, visit: https://creativecommons.org/licenses/by-nc/4.0/

import io
import time
import pygame
import wave
import numpy as np
import soundfile as sf
from scipy.io.wavfile import write

def convert_to_wav(audio_path):
    """Convert any audio file to WAV format if it's not already WAV."""
    data, samplerate = sf.read(audio_path)
    data = (data * 32767).astype(np.int16)  # Ensure 16-bit PCM
    write(audio_path, samplerate, data)
    return audio_path

def play_audio_bytes(audio_bytes, start_event):
    try:
        pygame.mixer.init()
        audio_file = io.BytesIO(audio_bytes)
        pygame.mixer.music.load(audio_file)
        
        start_event.wait()  # Wait until start event is triggered
        pygame.mixer.music.play()
        
        start_time = time.perf_counter()
        
        # Playback loop
        while pygame.mixer.music.get_busy():
            current_time = time.perf_counter()
            elapsed_time = current_time - start_time
            
            # Sync to real-time elapsed
            if elapsed_time > pygame.mixer.music.get_pos() / 1000.0:
                time.sleep(0.01)  # Slight pause to stay in sync
            elif elapsed_time < pygame.mixer.music.get_pos() / 1000.0:
                continue  # Skip frame update if behind
            
            pygame.time.Clock().tick(10)  # Regular ticking for updates
    except pygame.error as e:
        print(f"Error in play_audio_bytes: {e}")


def pcm_to_wav(pcm_data, sample_rate=22050, channels=1, sample_width=2):
    """
    Helper function to wrap raw PCM data into a WAV container.
    This uses the wave module to write a proper WAV header.
    """
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    wav_io.seek(0)
    return wav_io


def play_audio_from_path(audio_path, start_event):
    pygame.mixer.init()
    try:
        pygame.mixer.music.load(audio_path)
    except pygame.error:
        print(f"Unsupported format detected for {audio_path}. Converting to WAV.")
        audio_path = convert_to_wav(audio_path)
        pygame.mixer.music.load(audio_path)
    
    start_event.wait()  # Wait until start event is triggered
    pygame.mixer.music.play()
    
    start_time = time.perf_counter()
    
    # Playback loop
    while pygame.mixer.music.get_busy():
        current_time = time.perf_counter()
        elapsed_time = current_time - start_time
        
        # Sync to real-time elapsed
        if elapsed_time > pygame.mixer.music.get_pos() / 1000.0:
            time.sleep(0.01)  # Slight pause to stay in sync
        elif elapsed_time < pygame.mixer.music.get_pos() / 1000.0:
            continue  # Skip frame update if behind
        
        pygame.time.Clock().tick(10)  # Regular ticking for updates


def play_audio_from_memory_openai(audio_data, start_event):
    try:
        # Initialize Pygame mixer
        pygame.mixer.init()
        
        # --- NEW CODE START ---
        # Check if the audio_data starts with a WAV header ('RIFF').
        # If not, assume it's raw PCM and convert it to a WAV container.
        if not audio_data.startswith(b'RIFF'):
            # Convert raw PCM to WAV using default values:
            # sample_rate=22050, channels=1, sample_width=2
            audio_file = pcm_to_wav(audio_data, sample_rate=22050, channels=1, sample_width=2)
        else:
            # If already a WAV file, load directly.
            audio_file = io.BytesIO(audio_data)
        # --- NEW CODE END ---
        
        # Load the (possibly converted) audio file into Pygame
        pygame.mixer.music.load(audio_file)
        
        start_event.wait()  # Wait until start event is triggered
        pygame.mixer.music.play()
        
        start_time = time.perf_counter()
        
        # Playback loop
        while pygame.mixer.music.get_busy():
            current_time = time.perf_counter()
            elapsed_time = current_time - start_time
            
            # Sync to real-time elapsed
            if elapsed_time > pygame.mixer.music.get_pos() / 1000.0:
                time.sleep(0.01)  # Slight pause to stay in sync
            elif elapsed_time < pygame.mixer.music.get_pos() / 1000.0:
                continue  # Skip frame update if behind
            
            pygame.time.Clock().tick(10)  # Regular ticking for updates
    except pygame.error as e:
        print(f"Error in play_audio_from_memory: {e}")


def play_audio_from_memory(audio_data, start_event):
    try:
        pygame.mixer.init()
        audio_file = io.BytesIO(audio_data)
        pygame.mixer.music.load(audio_file)
        
        start_event.wait()
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except pygame.error as e:
        if "Unknown WAVE format" in str(e):
            print("Unknown WAVE format encountered. Skipping to the next item in the queue.")
        else:
            print(f"Error in play_audio_from_memory: {e}")
    except Exception as e:
        print(f"Error in play_audio_from_memory: {e}")

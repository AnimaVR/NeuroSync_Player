# This code is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
# For more details, visit: https://creativecommons.org/licenses/by-nc/4.0/

import pygame
import time
import io
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

def play_audio_from_memory(audio_data, start_event):
    try:
        pygame.mixer.init()
        audio_file = io.BytesIO(audio_data)
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


# This code is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
# For more details, visit: https://creativecommons.org/licenses/by-nc/4.0/

import pygame 
import time
import io

import numpy as np
import soundfile as sf
from scipy.io.wavfile import write

def play_audio_bytes(audio_bytes, start_event):
    try:
        pygame.mixer.init()
        audio_file = io.BytesIO(audio_bytes)
        pygame.mixer.music.load(audio_file)
        
        start_event.wait()
        pygame.mixer.music.play()

        chunk_size = 100
        while pygame.mixer.music.get_busy():
            time.sleep(chunk_size / 1000.0)
            pygame.time.Clock().tick(10)
    except pygame.error as e:
        if "Unknown WAVE format" in str(e):
            print("Unknown WAVE format encountered. Skipping to the next item in the queue.")
        else:
            print(f"Error in play_audio: {e}")
    except Exception as e:
        print(f"Error in play_audio: {e}")
        
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
        


def convert_to_wav(audio_path):
    """Convert the audio file to a standard WAV format and overwrite the original file."""
    # Load the audio data using soundfile
    data, samplerate = sf.read(audio_path)
    
    # Normalize the audio to 16-bit PCM format
    data = (data * 32767).astype(np.int16)
    
    # Write the data back to the original path as a WAV file
    write(audio_path, samplerate, data)

def play_audio_from_path(audio_path, start_event):
    pygame.mixer.init()
    try:
        pygame.mixer.music.load(audio_path)
    except pygame.error:
        # If unsupported format, convert to WAV and overwrite the original file
        print(f"Unsupported format detected for {audio_path}. Converting to WAV.")
        convert_to_wav(audio_path)
        pygame.mixer.music.load(audio_path)
    
    start_event.wait()
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

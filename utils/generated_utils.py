# This code is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
# For more details, visit: https://creativecommons.org/licenses/by-nc/4.0/

# In generated_utils.py

import os
import pandas as pd
from threading import Thread, Event

from utils.audio.play_audio import play_audio_from_path, play_audio_from_memory
from livelink.send_to_unreal import pre_encode_facial_data, send_pre_encoded_data_to_unreal
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

GENERATED_DIR = 'generated'

def list_generated_files():
    """List all the generated audio and face blend shape CSV files in the generated directory."""
    directories = [d for d in os.listdir(GENERATED_DIR) if os.path.isdir(os.path.join(GENERATED_DIR, d))]
    generated_files = []
    for directory in directories:
        audio_path = os.path.join(GENERATED_DIR, directory, 'audio.wav')
        shapes_path = os.path.join(GENERATED_DIR, directory, 'shapes.csv')
        if os.path.exists(audio_path) and os.path.exists(shapes_path):
            generated_files.append((audio_path, shapes_path))
    return generated_files

def load_facial_data_from_csv(csv_path):
    """Load facial data from a CSV file, excluding 'Timecode' and 'BlendshapeCount' columns."""
    data = pd.read_csv(csv_path)
    data = data.drop(columns=['Timecode', 'BlendshapeCount'], errors='ignore')
    return data.values

def run_audio_animation(audio_path, generated_facial_data, py_face, socket_connection, default_animation_thread):
    # --- Pre-encode in its own thread and wait until it's done ---
    pre_encode_done = Event()
    encoded_holder = {}  # Use a dict to hold the encoded data

    def pre_encode_worker():
        encoded_holder['data'] = pre_encode_facial_data(generated_facial_data, py_face)
        pre_encode_done.set()

    pre_encode_thread = Thread(target=pre_encode_worker, name="PreEncodeThread")
    pre_encode_thread.start()
    pre_encode_done.wait()       # Wait for pre-encoding to finish
    pre_encode_thread.join()     # Ensure cleanup
    encoded_facial_data = encoded_holder['data']
    # ----------------------------------------------------------------

    # Stop the default animation before starting playback
    stop_default_animation.set()
    if default_animation_thread and default_animation_thread.is_alive():
        default_animation_thread.join()

    start_event = Event()

    # Start the audio playback thread
    audio_thread = Thread(target=play_audio_from_path, args=(audio_path, start_event))
    # Start the data sender thread (it creates its own timing thread internally)
    data_thread = Thread(target=send_pre_encoded_data_to_unreal,
                         args=(encoded_facial_data, start_event, 60, socket_connection))

    audio_thread.start()
    data_thread.start()
    
    # Signal both threads to start simultaneously.
    start_event.set()
    
    audio_thread.join()
    data_thread.join()

    # After playback, restart the default animation with a fresh socket and thread.
    stop_default_animation.clear()  # Clear the event for the next default animation cycle.
    default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
    default_animation_thread.start()


def run_audio_animation_from_bytes(audio_bytes, generated_facial_data, py_face, socket_connection, default_animation_thread):
    # --- Pre-encode in its own thread and wait until it's done ---
    pre_encode_done = Event()
    encoded_holder = {}

    def pre_encode_worker():
        encoded_holder['data'] = pre_encode_facial_data(generated_facial_data, py_face)
        pre_encode_done.set()

    pre_encode_thread = Thread(target=pre_encode_worker, name="PreEncodeThread")
    pre_encode_thread.start()
    pre_encode_done.wait()       # Wait for pre encoding to complete
    pre_encode_thread.join()     # Clean up the thread
    encoded_facial_data = encoded_holder['data']
    # ----------------------------------------------------------------

    # Stop the default animation before starting playback
    stop_default_animation.set()
    if default_animation_thread and default_animation_thread.is_alive():
        default_animation_thread.join()

    start_event = Event()

    audio_thread = Thread(target=play_audio_from_memory, args=(audio_bytes, start_event))
    data_thread = Thread(target=send_pre_encoded_data_to_unreal, args=(encoded_facial_data, start_event, 60, socket_connection))

    audio_thread.start()
    data_thread.start()
    
    start_event.set()
    
    audio_thread.join()
    data_thread.join()

    # Restart the default animation after playback is complete.
    stop_default_animation.clear()
    default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
    default_animation_thread.start()

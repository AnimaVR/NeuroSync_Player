# This code is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
# For more details, visit: https://creativecommons.org/licenses/by-nc/4.0/
import wave
import os
import uuid
import numpy as np
import soundfile as sf
from threading import Thread, Event, Lock
import shutil

from livelink.connect.livelink_init import create_socket_connection
from livelink.send_to_unreal import pre_encode_facial_data, send_pre_encoded_data_to_unreal
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

from utils.neurosync_api_connect import send_audio_to_audio2face
from utils.csv.save_csv import save_generated_data_as_csv
from utils.audio.play_audio import play_audio_bytes
from utils.audio.save_audio import save_audio_file

GENERATED_DIR = 'generated'
queue_lock = Lock()

def initialize_directories():
    if not os.path.exists(GENERATED_DIR):
        os.makedirs(GENERATED_DIR)

def run_audio_animation(audio_bytes, encoded_facial_data, py_face, socket_connection):
    start_event = Event()

    audio_thread = Thread(target=play_audio_bytes, args=(audio_bytes, start_event))
    data_thread = Thread(target=send_pre_encoded_data_to_unreal, args=(encoded_facial_data, start_event, 60, socket_connection))

    audio_thread.start()
    data_thread.start()

    start_event.set()
    audio_thread.join()
    data_thread.join()

def save_generated_data(audio_bytes, generated_facial_data):
    unique_id = str(uuid.uuid4())
    output_dir = os.path.join(GENERATED_DIR, unique_id)
    os.makedirs(output_dir, exist_ok=True)

    audio_path = os.path.join(output_dir, 'audio.wav')
    shapes_path = os.path.join(output_dir, 'shapes.csv')

    # Attempt to save the audio using the existing method
    save_audio_file(audio_bytes, audio_path)

    # Validate if the saved file is a valid WAV file
    try:
        with wave.open(audio_path, 'rb') as wav_file:
            wav_file.readframes(1)  # Try to read the first frame
    except (wave.Error, EOFError):
        # If the file is not valid, rewrite it using soundfile
        print(f"The file {audio_path} was not a valid WAV file. Rewriting it using soundfile.")
        with sf.SoundFile(audio_path, mode='w', samplerate=88200, channels=1, format='WAV', subtype='PCM_16') as f:
            f.write(np.frombuffer(audio_bytes, dtype=np.int16))

    # Save the generated facial data as a CSV file
    save_generated_data_as_csv(generated_facial_data, shapes_path)

    return unique_id, audio_path, shapes_path

def save_generated_data_from_wav(wav_file_path, generated_facial_data):
    # Create a unique ID for the output directory
    unique_id = str(uuid.uuid4())
    output_dir = os.path.join(GENERATED_DIR, unique_id)
    os.makedirs(output_dir, exist_ok=True)

    # Define paths for the audio and facial data
    audio_path = os.path.join(output_dir, 'audio.wav')
    shapes_path = os.path.join(output_dir, 'shapes.csv')

    try:
        shutil.copy(wav_file_path, audio_path)
    except shutil.SameFileError:
        print(f"Audio file '{wav_file_path}' is already in the correct location.")

    save_generated_data_as_csv(generated_facial_data, shapes_path)

    return unique_id, audio_path, shapes_path


def process_preprocessing_queue(request_queue, preprocessed_data_queue):
    """
    Process audio chunks in the request queue by sending them to the API for processing.
    """
    while True:
        audio_bytes = request_queue.get()
        if audio_bytes is None:
            break

        # Send the audio bytes to the API and get the facial blendshapes
        generated_facial_data = send_audio_to_audio2face(audio_bytes)

        if generated_facial_data is None:
            print("Failed to get facial data from the API.")
            continue

        save_generated_data(audio_bytes, generated_facial_data)
        preprocessed_data_queue.put((audio_bytes, generated_facial_data))
        request_queue.task_done()

def process_playback_queue(preprocessed_data_queue, py_face, default_animation_thread, request_queue):
    global stop_default_animation
    while True:
        audio_bytes, generated_facial_data = preprocessed_data_queue.get()
        if audio_bytes is None:
            break

        with queue_lock:
            stop_default_animation.set()
            if default_animation_thread and default_animation_thread.is_alive():
                default_animation_thread.join()

        # Pre-encode facial data before sending to Unreal Engine
        encoded_facial_data = pre_encode_facial_data(generated_facial_data, py_face, fps=60)
        run_audio_animation(audio_bytes, encoded_facial_data, py_face, create_socket_connection())

        preprocessed_data_queue.task_done()

        with queue_lock:
            if preprocessed_data_queue.empty() and request_queue.empty():
                stop_default_animation.clear()
                default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
                default_animation_thread.start()

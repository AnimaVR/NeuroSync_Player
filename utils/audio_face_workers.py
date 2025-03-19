# utils/audio_face_workers.py
# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.
# utils/audio_workers.py

import os
from threading import Lock

from utils.generated_runners import run_audio_animation_from_bytes, run_audio_animation
from utils.files.file_utils import save_generated_data_from_wav
from utils.neurosync.neurosync_api_connect import send_audio_to_neurosync
from utils.audio.play_audio import read_audio_file_as_bytes
from utils.audio.convert_audio import bytes_to_wav

queue_lock = Lock()

def audio_face_queue_worker(audio_face_queue, py_face, socket_connection, default_animation_thread):
    """
    Processes audio items from audio_queue sequentially.
    Each item is a tuple (audio_bytes, facial_data) that is played back,
    ensuring that the animations remain in sync.
    """
    while True:
        item = audio_face_queue.get()
        if item is None:
            break
        audio_bytes, facial_data = item
        run_audio_animation_from_bytes(audio_bytes, facial_data, py_face, socket_connection, default_animation_thread)
        audio_face_queue.task_done()

def process_wav_file(wav_file, py_face, socket_connection, default_animation_thread):
    """
    Processes the wav file by sending it to the API and running the animation.
    """
    # Inform the user that processing is starting
    print(f"Starting processing of WAV file: {wav_file}")  # << Added print

    # Check if the file exists
    if not os.path.exists(wav_file):
        print(f"File {wav_file} does not exist.")  # << Existing error print
        return

    # Inform the user that the file exists and we are reading it
    print("File exists. Reading audio file bytes...")  # << Added print

    # Read the wav file as bytes
    audio_bytes = read_audio_file_as_bytes(wav_file)

    if audio_bytes is None:
        print(f"Failed to read {wav_file}")  # << Existing error print
        return

    # Inform the user that the audio file was read successfully
    print("Audio file read successfully. Sending audio to the API for processing...")  # << Added print

    # Send the audio bytes to the API and get the blendshapes
    blendshapes = send_audio_to_neurosync(audio_bytes)

    if blendshapes is None:
        print("Failed to get blendshapes from the API.")  # << Existing error print
        return

    # Inform the user that the blendshapes were received
    print("Received blendshapes from the API. Running audio animation...")  # << Added print

    # Run the animation using the blendshapes data
    run_audio_animation(wav_file, blendshapes, py_face, socket_connection, default_animation_thread)

    # Inform the user that the animation is complete and data is being saved
    print("Animation finished. Saving generated blendshape data...")  # << Added print

    # Save the generated blendshape data
    save_generated_data_from_wav(wav_file, blendshapes)
    
    # Inform the user that all processing is complete
    print("Processing completed successfully.")  # << Added print



def log_timing_worker(log_queue):
    """
    Logs timing data in a separate thread to avoid interfering with animations.
    """
    while True:
        try:
            log_entry = log_queue.get()
            if log_entry is None:
                break  # Exit the thread
            print(log_entry)
        except Exception as e:
            print(f"Logging error: {e}")


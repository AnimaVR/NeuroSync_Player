# utils/audio_face_workers.py
# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.


import os
from threading import Lock

from utils.generated_runners import run_audio_animation
from utils.files.file_utils import save_generated_data_from_wav
from utils.neurosync.neurosync_api_connect import send_audio_to_neurosync
from utils.audio.play_audio import read_audio_file_as_bytes
from utils.emote_sender.send_emote import EmoteConnect

queue_lock = Lock()


def audio_face_queue_worker(audio_face_queue, py_face, socket_connection, default_animation_thread, enable_emote_calls=True):
    speaking = False
    while True:
        item = audio_face_queue.get()
        if item is None:
            audio_face_queue.task_done()
            break

        if not speaking and enable_emote_calls:
            EmoteConnect.send_emote("startspeaking")
            speaking = True

        audio_bytes, facial_data = item
        run_audio_animation(audio_bytes, facial_data, py_face, socket_connection, default_animation_thread)
        audio_face_queue.task_done()

        if speaking and audio_face_queue.empty() and enable_emote_calls:
            EmoteConnect.send_emote("stopspeaking")
            speaking = False
    
    
def log_timing_worker(log_queue):
    while True:
        try:
            log_entry = log_queue.get()
            if log_entry is None:
                break 
            print(log_entry)
        except Exception as e:
            print(f"Logging error: {e}")


def process_wav_file(wav_file, py_face, socket_connection, default_animation_thread):

    if not os.path.exists(wav_file):
        print(f"File {wav_file} does not exist.")  
        return
    
    audio_bytes = read_audio_file_as_bytes(wav_file)

    if audio_bytes is None:
        print(f"Failed to read {wav_file}") 
        return
    
    blendshapes = send_audio_to_neurosync(audio_bytes)

    if blendshapes is None:
        print("Failed to get blendshapes from the API.") 
        return

    run_audio_animation(wav_file, blendshapes, py_face, socket_connection, default_animation_thread)
    save_generated_data_from_wav(wav_file, blendshapes)

    print("Processing completed successfully.")  



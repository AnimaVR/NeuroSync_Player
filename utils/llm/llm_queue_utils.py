# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

from threading import Thread, Lock
from livelink.connect.livelink_init import create_socket_connection
from livelink.send_to_unreal import pre_encode_facial_data 
from livelink.animations.default_animation import default_animation_loop, stop_default_animation
from utils.generated_runners import run_encoded_audio_animation
from utils.neurosync.neurosync_api_connect import send_audio_to_neurosync
from utils.files.file_utils import save_generated_data

queue_lock = Lock()

def process_preprocessing_queue(request_queue, preprocessed_data_queue):
    """
    Process audio chunks in the request queue by sending them to the API for processing.
    """
    while True:
        audio_bytes = request_queue.get()
        if audio_bytes is None:
            break

        # Send the audio bytes to the API and get the facial blendshapes
        generated_facial_data = send_audio_to_neurosync(audio_bytes)

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

        encoded_facial_data = pre_encode_facial_data(generated_facial_data, py_face, fps=60)
        run_encoded_audio_animation(audio_bytes, encoded_facial_data, create_socket_connection())

        preprocessed_data_queue.task_done()

        with queue_lock:
            if preprocessed_data_queue.empty() and request_queue.empty():
                stop_default_animation.clear()
                default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
                default_animation_thread.start()

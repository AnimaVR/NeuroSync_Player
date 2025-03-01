# utils/audio_workers.py

import os
import time
from threading import Thread, Event, Lock
from queue import Queue

from utils.generated_runners import run_audio_animation_from_bytes, run_audio_animation
from livelink.animations.default_animation import default_animation_loop, stop_default_animation
from utils.llm.realtime_queue_utils import playback_loop, accumulate_data
from utils.files.file_utils import save_generated_data_from_wav
from utils.neurosync.neurosync_api_connect import send_audio_to_neurosync
from utils.audio.load_audio import read_audio_file_as_bytes

queue_lock = Lock()

def audio_face_queue_worker_realtime(audio_face_queue, py_face, socket_connection, default_animation_thread):
    """
    Streams (audio_bytes, facial_data) pairs in real-time.
    - Uses a separate thread to log timing data.
    """
    accumulated_audio = bytearray()
    accumulated_facial_data = []
    encoded_facial_data = []
    stop_worker = Event()
    start_event = Event()

    log_queue = Queue()  # Separate queue for logging
    log_thread = Thread(target=log_timing_worker, args=(log_queue,), daemon=True)
    log_thread.start()

    playback_thread = Thread(
        target=playback_loop,
        args=(
            stop_worker,
            start_event,
            accumulated_audio,
            encoded_facial_data,
            audio_face_queue,
            py_face,
            socket_connection,
            default_animation_thread,
            log_queue,  # Pass the log queue
        ),
        daemon=True
    )
    playback_thread.start()

    # Process each item in the queue.
    while True:
        item = audio_face_queue.get()
        if item is None:
            audio_face_queue.task_done()
            break

        received_time = time.time()  # Timestamp when data is received

        audio_bytes, facial_data = item
        audio_face_queue.task_done()

        # Changed: Determine if this is the only entry by checking if the queue is empty.
        single_entry = audio_face_queue.empty()
        accumulate_data(audio_bytes, facial_data, accumulated_audio, accumulated_facial_data, encoded_facial_data, py_face, single_entry)

        playback_start_time = time.time()
        log_queue.put(f"Time from queue reception to addition to encoded queue: {playback_start_time - received_time:.3f} seconds.")
    
    time.sleep(0.1)
    audio_face_queue.join()

    stop_worker.set()
    playback_thread.join()

    log_queue.put(None)  # Signal log thread to exit
    log_thread.join()

    time.sleep(0.01)
    with queue_lock:
        stop_default_animation.clear()
        new_default_thread = Thread(target=default_animation_loop, args=(py_face,))
        new_default_thread.start()

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
    # Check if the file exists
    if not os.path.exists(wav_file):
        print(f"File {wav_file} does not exist.")
        return

    # Read the wav file as bytes
    audio_bytes = read_audio_file_as_bytes(wav_file)

    if audio_bytes is None:
        print(f"Failed to read {wav_file}")
        return

    # Send the audio bytes to the API and get the blendshapes
    blendshapes = send_audio_to_neurosync(audio_bytes)

    if blendshapes is None:
        print("Failed to get blendshapes from the API.")
        return

    # Run the animation using the blendshapes data
    run_audio_animation(wav_file, blendshapes, py_face, socket_connection, default_animation_thread)

    # Save the generated blendshape data
    save_generated_data_from_wav(wav_file, blendshapes)



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

# utils/audio_workers.py


import time
from threading import Thread, Event, Lock
from queue import Queue, Empty

from utils.generated_utils import run_audio_animation_from_bytes
from utils.neurosync_api_connect import send_audio_to_neurosync
from utils.local_tts import call_local_tts 
from utils.eleven_labs import get_elevenlabs_audio
from utils.audio.play_audio import play_audio_from_memory
from livelink.send_to_unreal import pre_encode_facial_data_blend_in, send_pre_encoded_data_to_unreal, pre_encode_facial_data_without_blend, pre_encode_facial_data_blend_out, pre_encode_facial_data
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

# Global lock for shared data protection
queue_lock = Lock()

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

# Modified accumulate_data to accept a "single_entry" flag.
def accumulate_data(audio_bytes, facial_data, accumulated_audio, accumulated_facial_data, encoded_facial_data, py_face, single_entry=False):
    """
    Accumulates incoming audio and facial data while pre-encoding facial animation.
    
    If single_entry is True (i.e. only one entry is present),
    then we call pre_encode_facial_data (which blends in and out).
    Otherwise, the first entry uses pre_encode_facial_data_blend_in and subsequent entries use pre_encode_facial_data_blend_out.
    """
    with queue_lock:
        accumulated_audio.extend(audio_bytes)
        if len(accumulated_facial_data) == 0:
            if single_entry:
                # Changed: For a single entry, pre-encode with both blend in and out.
                encoded_facial_data.extend(pre_encode_facial_data(facial_data, py_face))
            else:
                encoded_facial_data.extend(pre_encode_facial_data_blend_in(facial_data, py_face))
        else:
            encoded_facial_data.extend(pre_encode_facial_data_blend_out(facial_data, py_face))
        accumulated_facial_data.extend(facial_data)

def play_audio_and_animation(playback_audio, playback_facial_data, start_event, socket_connection):
    """
    Plays audio and sends animation data using separate threads.
    """
    audio_thread = Thread(target=play_audio_from_memory, args=(playback_audio, start_event))
    data_thread = Thread(target=send_pre_encoded_data_to_unreal, args=(playback_facial_data, start_event, 60, socket_connection))

    audio_thread.start()
    data_thread.start()
    start_event.set()

    audio_thread.join()
    data_thread.join()

    time.sleep(0.1)  # Allow new data to accumulate

def check_and_restart_default_animation(accumulated_audio, encoded_facial_data, audio_face_queue, py_face):
    """
    Restarts default animation if no data is available.
    """
    with queue_lock:
        if not accumulated_audio and not encoded_facial_data and audio_face_queue.empty():
            stop_default_animation.clear()
            new_default_thread = Thread(target=default_animation_loop, args=(py_face,))
            new_default_thread.start()

def playback_loop(stop_worker, start_event, accumulated_audio, encoded_facial_data, audio_face_queue, py_face, socket_connection, default_animation_thread, log_queue):
    """
    Continuously plays accumulated audio and encoded facial data.
    """
    while not stop_worker.is_set():
        with queue_lock:
            if not accumulated_audio or not encoded_facial_data:
                time.sleep(0.01)
                continue

            playback_audio = accumulated_audio[:]
            playback_facial_data = encoded_facial_data[:]
            accumulated_audio.clear()
            encoded_facial_data.clear()

        stop_default_animation.set()
        if default_animation_thread and default_animation_thread.is_alive():
            default_animation_thread.join()

        playback_start_time = time.time()

        # Play audio and animation
        play_audio_and_animation(playback_audio, playback_facial_data, start_event, socket_connection)

        playback_end_time = time.time()
        log_queue.put(f"Playback duration: {playback_end_time - playback_start_time:.3f} seconds.")

        time.sleep(0.01)

        check_and_restart_default_animation(accumulated_audio, encoded_facial_data, audio_face_queue, py_face)

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

def tts_worker(chunk_queue, audio_queue, USE_LOCAL_AUDIO, VOICE_NAME):
    """
    Processes text chunks from chunk_queue by generating audio (using local TTS or ElevenLabs)
    and retrieving corresponding facial data, then enqueues the results into audio_queue.
    """
    while True:
        chunk = chunk_queue.get()
        if chunk is None:
            break
        if USE_LOCAL_AUDIO:
            audio_bytes = call_local_tts(chunk)
        else:
            audio_bytes = get_elevenlabs_audio(chunk, VOICE_NAME)
        if audio_bytes:
            facial_data = send_audio_to_neurosync(audio_bytes)
            if facial_data:
                audio_queue.put((audio_bytes, facial_data))
            else:
                print("Failed to get facial data for chunk:", chunk)
        else:
            print("Failed to generate audio for chunk:", chunk)
        chunk_queue.task_done()



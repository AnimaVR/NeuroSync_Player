# utils/audio_workers.py


import time
from threading import Thread, Event, Lock

from utils.generated_utils import run_audio_animation_from_bytes
from utils.neurosync_api_connect import send_audio_to_neurosync
from utils.local_tts import call_local_tts 
from utils.eleven_labs import get_elevenlabs_audio
from utils.audio.play_audio import play_audio_from_memory
from livelink.send_to_unreal import pre_encode_facial_data_blend_in, send_pre_encoded_data_to_unreal, pre_encode_facial_data_without_blend, pre_encode_facial_data_blend_out, pre_encode_facial_data
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

queue_lock = Lock()

def audio_face_queue_worker_realtime(audio_face_queue, py_face, socket_connection, default_animation_thread):
    """
    Streams (audio_bytes, facial_data) pairs in real-time.
    - Accumulates data continuously, encoding it as it arrives.
    - Plays audio and facial data immediately, without waiting for large batches.
    - Ensures smooth playback without abrupt cutoffs.
    """

    accumulated_audio = bytearray()
    accumulated_facial_data = []
    encoded_facial_data = []  # Pre-encoded data storage
    stop_worker = Event()
    start_event = Event()

    def playback_loop():
        """
        Plays accumulated audio and facial data in sync, streaming as new data arrives.
        """
        while not stop_worker.is_set():
            with queue_lock:
                if not accumulated_audio or not encoded_facial_data:
                    time.sleep(0.005)  # Wait for new chunks
                    continue

                playback_audio = accumulated_audio[:]
                playback_facial_data = encoded_facial_data[:]

                accumulated_audio.clear()
                encoded_facial_data.clear()

            # Stop default animation
            stop_default_animation.set()
            if default_animation_thread and default_animation_thread.is_alive():
                default_animation_thread.join()

            # Play audio and send animation data
            audio_thread = Thread(target=play_audio_from_memory, args=(playback_audio, start_event))
            data_thread = Thread(target=send_pre_encoded_data_to_unreal, args=(playback_facial_data, start_event, 60, socket_connection))

            audio_thread.start()
            data_thread.start()
            start_event.set()

            audio_thread.join()
            data_thread.join()

            time.sleep(0.005)  # Small delay to allow for new data

            # If the queue is empty and we have nothing left to play, restart the default animation
            with queue_lock:
                if not accumulated_audio and not encoded_facial_data and audio_face_queue.empty():
                    stop_default_animation.clear()
                    new_default_thread = Thread(target=default_animation_loop, args=(py_face,))
                    new_default_thread.start()

    # Start playback thread
    playback_thread = Thread(target=playback_loop, daemon=True)
    playback_thread.start()

    chunk_count = 0
    while True:
        item = audio_face_queue.get()
        if item is None:
            audio_face_queue.task_done()
            break

        audio_bytes, facial_data = item
        audio_face_queue.task_done()

        with queue_lock:
            accumulated_audio += audio_bytes

            # **Pre-encode as data arrives**
            if len(accumulated_facial_data) == 0:
                encoded_facial_data.extend(pre_encode_facial_data_blend_in(facial_data, py_face))
            else:
                encoded_facial_data.extend(pre_encode_facial_data_blend_out(facial_data, py_face))

            accumulated_facial_data.extend(facial_data)

        chunk_count += 1

    # Ensure any remaining data gets processed
    time.sleep(0.05)
    audio_face_queue.join()

    stop_worker.set()
    playback_thread.join()

    # Final animation transition
    time.sleep(0.05)
    with queue_lock:
        stop_default_animation.clear()
        new_default_thread = Thread(target=default_animation_loop, args=(py_face,))
        new_default_thread.start()

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

def audio_queue_worker(audio_queue, py_face, socket_connection, default_animation_thread):
    """
    Processes audio items from audio_queue sequentially.
    Each item is a tuple (audio_bytes, facial_data) that is played back,
    ensuring that the animations remain in sync.
    """
    while True:
        item = audio_queue.get()
        if item is None:
            break
        audio_bytes, facial_data = item
        run_audio_animation_from_bytes(audio_bytes, facial_data, py_face, socket_connection, default_animation_thread)
        audio_queue.task_done()

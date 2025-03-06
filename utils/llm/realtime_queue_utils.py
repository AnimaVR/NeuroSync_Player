# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.


import time
from threading import Thread, Lock

from livelink.animations.default_animation import default_animation_loop, stop_default_animation
from livelink.send_to_unreal import pre_encode_facial_data_blend_in, pre_encode_facial_data_blend_out, pre_encode_facial_data
from utils.generated_runners import play_audio_and_animation

queue_lock = Lock()


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

        play_audio_and_animation(playback_audio, playback_facial_data, start_event, socket_connection)

        playback_end_time = time.time()
        log_queue.put(f"Playback duration: {playback_end_time - playback_start_time:.3f} seconds.")

        time.sleep(0.01)

        check_and_restart_default_animation(accumulated_audio, encoded_facial_data, audio_face_queue, py_face)


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

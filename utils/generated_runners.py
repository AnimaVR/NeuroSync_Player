# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

from threading import Thread, Event, Lock

from utils.audio.play_audio import play_audio_from_path, play_audio_from_memory
from livelink.send_to_unreal import pre_encode_facial_data, send_pre_encoded_data_to_unreal
from livelink.animations.default_animation import default_animation_loop, stop_default_animation
from livelink.connect.livelink_init import initialize_py_face 
from utils.audio.play_audio import play_audio_bytes

queue_lock = Lock()

def run_encoded_audio_animation(audio_bytes, encoded_facial_data, socket_connection):
    start_event = Event()

    audio_thread = Thread(target=play_audio_bytes, args=(audio_bytes, start_event))
    data_thread = Thread(target=send_pre_encoded_data_to_unreal, args=(encoded_facial_data, start_event, 60, socket_connection))

    audio_thread.start()
    data_thread.start()

    start_event.set()
    audio_thread.join()
    data_thread.join()


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


def run_audio_animation_from_bytes(audio_bytes, generated_facial_data, py_face, socket_connection, default_animation_thread):
    # --------------------------------------------------------------------
    # Create a separate instance for encoding to include blend in/out data.
    # --------------------------------------------------------------------
    encoding_face = initialize_py_face()
    
    # Pre-encode the facial data with blend animations applied to the temporary instance.
    encoded_facial_data = pre_encode_facial_data(generated_facial_data, encoding_face)

    with queue_lock:
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

    with queue_lock:
        stop_default_animation.clear()
        default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
        default_animation_thread.start()




def run_audio_animation(audio_path, generated_facial_data, py_face, socket_connection, default_animation_thread):
    # --------------------------------------------------------------------
    # Create a temporary py_face instance for encoding, including blend in/out.
    # This separate instance is used solely for encoding the facial data.
    # --------------------------------------------------------------------
    encoding_face = initialize_py_face()
    
    # Pre-encode the facial data using the temporary (encoding) instance.
    # This will apply blend_in and blend_out on the temporary instance.
    encoded_facial_data = pre_encode_facial_data(generated_facial_data, encoding_face)

    # Now, stop the default animation running on the original py_face.
    with queue_lock:
        stop_default_animation.set()
        if default_animation_thread and default_animation_thread.is_alive():
            default_animation_thread.join()

    # Create an event to synchronize the start of playback.
    start_event = Event()

    # Create threads for audio playback and sending pre-encoded data.
    audio_thread = Thread(target=play_audio_from_path, args=(audio_path, start_event))
    data_thread = Thread(target=send_pre_encoded_data_to_unreal, args=(encoded_facial_data, start_event, 60, socket_connection))

    # Start both threads.
    audio_thread.start()
    data_thread.start()
    
    # Trigger the start event.
    start_event.set()
    
    # Wait for both threads to complete.
    audio_thread.join()
    data_thread.join()

    # Restart the default animation on the original py_face.
    with queue_lock:
        stop_default_animation.clear()
        default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
        default_animation_thread.start()





# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

from threading import Thread, Event, Lock
import numpy as np
import random
from utils.audio.play_audio import (
    play_audio_from_path, 
    play_audio_from_memory, 
    play_audio_bytes, 
    play_audio_from_memory_openai
)
from livelink.send_to_unreal import pre_encode_facial_data, send_pre_encoded_data_to_unreal
from livelink.animations.default_animation import default_animation_loop, stop_default_animation
from livelink.connect.livelink_init import initialize_py_face 

from livelink.animations.animation_emotion import (
    determine_highest_emotion, 
    merge_emotion_data_into_facial_data_wrapper
)

from livelink.animations.animation_loader import emotion_animations

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


def play_audio_and_animation_openai_realtime(playback_audio, playback_facial_data, start_event, socket_connection):
    """
    Plays audio and sends animation data using separate threads.
    """
    audio_thread = Thread(target=play_audio_from_memory_openai, args=(playback_audio, start_event))
    data_thread = Thread(target=send_pre_encoded_data_to_unreal, args=(playback_facial_data, start_event, 60, socket_connection))

    audio_thread.start()
    data_thread.start()
    start_event.set()

    audio_thread.join()
    data_thread.join()

def run_audio_animation_from_bytes(audio_bytes, generated_facial_data, py_face, socket_connection, default_animation_thread):
    # Check that generated_facial_data is not None, has at least one frame,
    # and that the first frame has more than 61 columns.
    if (generated_facial_data is not None and 
        len(generated_facial_data) > 0 and 
        len(generated_facial_data[0]) > 61):
        
        # Convert to mutable list-of-lists if necessary.
        if isinstance(generated_facial_data, np.ndarray):
            generated_facial_data = generated_facial_data.tolist()
        
        facial_data_array = np.array(generated_facial_data)
        dominant_emotion = determine_highest_emotion(facial_data_array)
     #   print(f"Dominant emotion: {dominant_emotion}")
        if dominant_emotion in emotion_animations and len(emotion_animations[dominant_emotion]) > 0:
            selected_animation = random.choice(emotion_animations[dominant_emotion])
            generated_facial_data = merge_emotion_data_into_facial_data_wrapper(
                generated_facial_data, selected_animation, alpha=0.7)
    
    # Create a separate instance for encoding (to include blend in/out data).
    encoding_face = initialize_py_face()
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
    # Check that generated_facial_data is not None, has at least one frame,
    # and that the first frame has more than 61 columns.
    if (generated_facial_data is not None and 
        len(generated_facial_data) > 0 and 
        len(generated_facial_data[0]) > 61):
        
        if isinstance(generated_facial_data, np.ndarray):
            generated_facial_data = generated_facial_data.tolist()
        
        facial_data_array = np.array(generated_facial_data)
        dominant_emotion = determine_highest_emotion(facial_data_array)
     #   print(f"Dominant emotion: {dominant_emotion}")
        if dominant_emotion in emotion_animations and len(emotion_animations[dominant_emotion]) > 0:
            selected_animation = random.choice(emotion_animations[dominant_emotion])
            generated_facial_data = merge_emotion_data_into_facial_data_wrapper(generated_facial_data, selected_animation, alpha=0.7)
    
    # Create a temporary encoding instance for blending.
    encoding_face = initialize_py_face()
    encoded_facial_data = pre_encode_facial_data(generated_facial_data, encoding_face)

    with queue_lock:
        stop_default_animation.set()
        if default_animation_thread and default_animation_thread.is_alive():
            default_animation_thread.join()

    start_event = Event()

    audio_thread = Thread(target=play_audio_from_path, args=(audio_path, start_event))
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





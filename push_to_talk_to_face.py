# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

import pygame
import warnings
warnings.filterwarnings(
    "ignore", 
    message="Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work"
)
import keyboard
from threading import Thread

from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

from utils.audio.record_audio import record_audio_until_release
from utils.generated_runners import run_audio_animation_from_bytes
from utils.files.file_utils import save_generated_data, initialize_directories
from utils.neurosync.neurosync_api_connect import send_audio_to_neurosync


if __name__ == "__main__":

    # Initialize directories and other resources
    initialize_directories()

    # Initialize py_face and the socket connection
    py_face = initialize_py_face()
    socket_connection = create_socket_connection()

    # Start the default animation thread
    default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
    default_animation_thread.start()

    try:
        while True:
            print("Press Right Ctrl to start recording (or 'q' to quit): ")
            while True:
                if keyboard.is_pressed('q'):
                    break
                elif keyboard.is_pressed('right ctrl'):
                    # Record the audio until the 'Right Ctrl' key is released
                    audio_bytes = record_audio_until_release()
                    
                    # Send the recorded audio to the API and get the blendshapes
                    generated_facial_data = send_audio_to_neurosync(audio_bytes)
                    
                    if generated_facial_data is None:
                        print("Failed to generate facial data from the API.")
                        continue

                    # Run the animation with the generated blendshapes
                    run_audio_animation_from_bytes(audio_bytes, generated_facial_data, py_face, socket_connection, default_animation_thread)
                    
                    # Save the generated data for later use
                    save_generated_data(audio_bytes, generated_facial_data)
                    
                    break

            if keyboard.is_pressed('q'):
                break

    finally:
        # Stop the default animation when quitting
        stop_default_animation.set()
        if default_animation_thread:
            default_animation_thread.join()
        pygame.quit()
        socket_connection.close()

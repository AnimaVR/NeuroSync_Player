import pygame
import keyboard
from threading import Thread

from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

from utils.audio.record_audio import record_audio_until_release
from utils.generated_utils import run_audio_animation_from_bytes
from utils.api_utils import save_generated_data, initialize_directories
from utils.api_connect import send_audio_to_audio2face


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
                    audio_bytes = record_audio_until_release(sr='88200')
                    
                    # Send the recorded audio to the API and get the blendshapes
                    generated_facial_data = send_audio_to_audio2face(audio_bytes)
                    
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

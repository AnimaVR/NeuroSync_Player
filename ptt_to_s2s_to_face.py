import pygame
import pyaudio
import keyboard

from threading import Thread

from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

from utils.eleven_labs import get_speech_to_speech_audio
from utils.audio.record_audio import record_audio_until_release
from utils.generated_utils import run_audio_animation_from_bytes
from utils.api_utils import save_generated_data, initialize_directories
from utils.neurosync_api_connect import send_audio_to_neurosync


voice_name = 'Chris1'

if __name__ == "__main__":

    # Initialize directories and resources
    initialize_directories()

    # Initialize py_face and socket connection
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
                    # Record audio when Right Ctrl is pressed
                    audio_bytes = record_audio_until_release(sr='88200')

                    # Convert the recorded audio to speech using Speech-to-Speech API
                    processed_audio_bytes = get_speech_to_speech_audio(audio_bytes, voice_name)
                    
                    if processed_audio_bytes is None:
                        print("Failed to get processed audio from Speech-to-Speech API.")
                        continue
                    
                    # Send the processed audio bytes to the API to get the facial blendshapes
                    generated_facial_data = send_audio_to_neurosync(processed_audio_bytes)
                    
                    if generated_facial_data is None:
                        print("Failed to get facial blendshapes from the API.")
                        continue

                    # Run the animation with the generated blendshapes
                    run_audio_animation_from_bytes(processed_audio_bytes, generated_facial_data, py_face, socket_connection, default_animation_thread)

                    # Save the generated blendshapes and audio
                    save_generated_data(processed_audio_bytes, generated_facial_data)
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

# This code is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
# For more details, visit: https://creativecommons.org/licenses/by-nc/4.0/

from threading import Thread
import pygame

from utils.eleven_labs import get_elevenlabs_audio

from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

from utils.api_utils import save_generated_data, initialize_directories
from utils.generated_utils import run_audio_animation_from_bytes
from utils.neurosync_api_connect import send_audio_to_neurosync

voice_name = 'Chris1'

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
            text_input = input("Enter the text to generate speech (or 'q' to quit): ").strip()
            if text_input.lower() == 'q':
                break
            elif text_input:
                # Get audio bytes from ElevenLabs using the provided text input
                audio_bytes = get_elevenlabs_audio(text_input, voice_name)
                
                if audio_bytes:
                    # Send the audio bytes to the API and get the blendshapes
                    generated_facial_data = send_audio_to_neurosync(audio_bytes)
                    
                    if generated_facial_data is not None:
                        # Run the animation using the blendshapes data
                        run_audio_animation_from_bytes(audio_bytes, generated_facial_data, py_face, socket_connection, default_animation_thread)
                        
                        # Save the generated blendshape data
                        save_generated_data(audio_bytes, generated_facial_data)
                    else:
                        print("Failed to get blendshapes from the API.")
                else:
                    print("Failed to generate audio.")
            else:
                print("No text provided.")
                
    finally:
        # Stop the default animation when quitting
        stop_default_animation.set()
        if default_animation_thread:
            default_animation_thread.join()
        pygame.quit()
        socket_connection.close()

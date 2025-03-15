# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.


from threading import Thread
import pygame
import warnings
import time  # <-- Added: Import the time module for the timer functionality

warnings.filterwarnings(
    "ignore", 
    message="Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work"
)

from utils.neurosync.multi_part_return import get_tts_with_blendshapes

from utils.neurosync.neurosync_api_connect import send_audio_to_neurosync
from utils.tts.eleven_labs import get_elevenlabs_audio
from utils.tts.local_tts import call_local_tts

from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation
from utils.files.file_utils import save_generated_data, initialize_directories
from utils.generated_runners import run_audio_animation_from_bytes

voice_name = 'Lily'
use_elevenlabs = False  # For old functionality: select ElevenLabs or Local TTS

use_combined_endpoint = False # only set this true if you have the combined realtime api with tts + blendshape in one call.

if __name__ == "__main__":
    initialize_directories()
    py_face = initialize_py_face()
    socket_connection = create_socket_connection()
    
    default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
    default_animation_thread.start()
    
    try:
        while True:
            text_input = input("Enter the text to generate speech (or 'q' to quit): ").strip()
            if text_input.lower() == 'q':
                break
            elif text_input:
                start_time = time.time()  # <-- Added: Start the timer before generation begins
                
                if use_combined_endpoint:
                    # Combined endpoint: one API call returns both audio and blendshapes.
                    audio_bytes, blendshapes = get_tts_with_blendshapes(text_input)
                    if audio_bytes and blendshapes:
                        generation_time = time.time() - start_time  # <-- Added: Calculate elapsed time
                        print(f"Generation took {generation_time:.2f} seconds.")  # <-- Added: Display the generation time
                        run_audio_animation_from_bytes(
                            audio_bytes, blendshapes, py_face, socket_connection, default_animation_thread
                        )
                        
                        save_generated_data(audio_bytes, blendshapes)
                    else:
                        print("❌ Failed to retrieve audio and blendshapes from the API.")
                else:
                    # Old functionality: generate audio using selected TTS engine,
                    # then retrieve blendshapes via a separate API call.
                    if use_elevenlabs:
                        audio_bytes = get_elevenlabs_audio(text_input, voice_name)
                    else:
                        audio_bytes = call_local_tts(text_input)
                        
                    if audio_bytes:
                        generated_facial_data = send_audio_to_neurosync(audio_bytes)
                        if generated_facial_data is not None:
                            generation_time = time.time() - start_time  # <-- Added: Calculate elapsed time
                            print(f"Generation took {generation_time:.2f} seconds.") 
                            run_audio_animation_from_bytes(
                                audio_bytes, generated_facial_data, py_face, socket_connection, default_animation_thread
                            )
                            save_generated_data(audio_bytes, generated_facial_data)
                        else:
                            print("❌ Failed to get blendshapes from the API.")
                    else:
                        print("❌ Failed to generate audio.")
            else:
                print("⚠️ No text provided.")
                
    finally:
        stop_default_animation.set()
        if default_animation_thread:
            default_animation_thread.join()
        pygame.quit()
        socket_connection.close()

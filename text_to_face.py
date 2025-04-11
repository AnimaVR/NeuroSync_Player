# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

from threading import Thread
import pygame
import warnings
import time
warnings.filterwarnings(
    "ignore", 
    message="Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work"
)
from utils.files.file_utils import save_generated_data, initialize_directories
from utils.generated_runners import run_audio_animation
from utils.neurosync.multi_part_return import get_tts_with_blendshapes
from utils.neurosync.neurosync_api_connect import send_audio_to_neurosync
from utils.tts.livepeer_tts import get_elevenlabs_audio
from utils.tts.local_tts import call_local_tts
from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation
from utils.tts.livepeer_tts import get_livepeer_audio

from utils.emote_sender.send_emote import EmoteConnect

voice_name = 'Sarah' # bf_isabella
use_elevenlabs = False  # ElevenLabs or Local TTS - if using elevenlabs then use_combined_endpoint must be false and you must use https://github.com/AnimaVR/NeuroSync_Local_API for the blendshapes
use_combined_endpoint = False  # Only set this true if you have the combined realtime API with TTS + blendshape in one call https://github.com/AnimaVR/NeuroSync_Real-Time_API
ENABLE_EMOTE_CALLS = False 
use_livepeer = True
livepeer_voice_description = "Jenna's voice is monotone yet slightly fast in delivery, with a very close recording that almost has no background noise."

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
                start_time = time.time() 
                if use_combined_endpoint:
                    audio_bytes, blendshapes = get_tts_with_blendshapes(text_input, voice_name)
                    if audio_bytes and blendshapes:
                        generation_time = time.time() - start_time  
                        print(f"Generation took {generation_time:.2f} seconds.")
                        if ENABLE_EMOTE_CALLS:
                            EmoteConnect.send_emote("startspeaking")
                        try:
                            run_audio_animation(audio_bytes, blendshapes, py_face, socket_connection, default_animation_thread)
                        finally:
                            if ENABLE_EMOTE_CALLS:
                                EmoteConnect.send_emote("stopspeaking")
                        save_generated_data(audio_bytes, blendshapes)
                    else:
                        print("❌ Failed to retrieve audio and blendshapes from the API.")
                else:
                    if use_elevenlabs:
                        audio_bytes = get_elevenlabs_audio(text_input, voice_name)
                    elif use_livepeer:
                        audio_bytes = get_livepeer_audio(text_input, livepeer_voice_description)
                    else:
                        audio_bytes = call_local_tts(text_input)                  
                    if audio_bytes:
                        generated_facial_data = send_audio_to_neurosync(audio_bytes)
                        if generated_facial_data is not None:
                            generation_time = time.time() - start_time  
                            print(f"Generation took {generation_time:.2f} seconds.")
                            if ENABLE_EMOTE_CALLS:
                                EmoteConnect.send_emote("startspeaking")
                            try:
                                run_audio_animation(audio_bytes, generated_facial_data, py_face, socket_connection, default_animation_thread)
                            finally:
                                if ENABLE_EMOTE_CALLS:
                                    EmoteConnect.send_emote("stopspeaking")
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
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
from utils.tts.eleven_labs import get_speech_to_speech_audio
from utils.audio.record_audio import record_audio_until_release
from utils.generated_runners import run_audio_animation_from_bytes
from utils.files.file_utils import save_generated_data, initialize_directories
from utils.neurosync.neurosync_api_connect import send_audio_to_neurosync
from utils.stt.transcribe_whisper import transcribe_audio 
from utils.tts.local_tts import call_local_tts 

from utils.emote_sender.send_emote import EmoteConnect

use_speech_to_speech_elevenlabs = False 
voice_name = 'Alice'

ENABLE_EMOTE_CALLS = False  # Set to False to disable emote calls if you dont have something to receive them (try this https://github.com/AnimaVR/Unreal_Glory_Hole ). 

if __name__ == "__main__":

    initialize_directories()
    py_face = initialize_py_face()
    socket_connection = create_socket_connection()

    default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
    default_animation_thread.start()
    try:
        while True:
            print("Press Right Ctrl to start recording (or 'q' to quit): ")
            while True:
                if keyboard.is_pressed('q'):
                    break
                elif keyboard.is_pressed('right ctrl'):
                    audio_bytes = record_audio_until_release()
                    if use_speech_to_speech_elevenlabs:
                        processed_audio_bytes = get_speech_to_speech_audio(audio_bytes, voice_name)
                        if processed_audio_bytes is None:
                            print("Failed to get processed audio from Speech-to-Speech API.")
                            continue
                    else:
                        transcribed_text, _ = transcribe_audio(audio_bytes)
                        if not transcribed_text:
                            print("Failed to transcribe audio.")
                            continue

                        print(f"Transcribed Text: {transcribed_text}")

                        processed_audio_bytes = call_local_tts(transcribed_text)
                        if processed_audio_bytes is None:
                            print("Failed to generate local TTS audio.")
                            continue

                    generated_facial_data = send_audio_to_neurosync(processed_audio_bytes)
                    if generated_facial_data is None:
                        print("Failed to get facial blendshapes from the API.")
                        continue

                    if ENABLE_EMOTE_CALLS:
                        EmoteConnect.send_emote("startspeaking")

                    try:
                        run_audio_animation_from_bytes(processed_audio_bytes, generated_facial_data, py_face, socket_connection, default_animation_thread)
                    finally:
                        if ENABLE_EMOTE_CALLS:
                            EmoteConnect.send_emote("stopspeaking")
                    
                    save_generated_data(processed_audio_bytes, generated_facial_data)
                    break

            if keyboard.is_pressed('q'):
                break
    finally:
        stop_default_animation.set()
        if default_animation_thread:
            default_animation_thread.join()
        pygame.quit()
        socket_connection.close()

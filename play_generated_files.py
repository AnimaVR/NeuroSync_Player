import pygame
import warnings
warnings.filterwarnings(
    "ignore", 
    message="Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work"
)
from threading import Thread
from livelink.animations.default_animation import default_animation_loop, stop_default_animation
from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from utils.files.file_utils import list_generated_files
from utils.generated_runners import run_audio_animation
from livelink.animations.animation_loader import load_animation

from utils.emote_sender.send_emote import EmoteConnect 

# Global variable to enable/disable emote calls.
ENABLE_EMOTE_CALLS = False  # Set to False to disable emote calls if you dont have something to receive them (try this https://github.com/AnimaVR/Unreal_Glory_Hole ). 

py_face = initialize_py_face()
socket_connection = create_socket_connection()
default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
default_animation_thread.start()

def main():
    generated_files = list_generated_files()
    if not generated_files:
        print("No generated files found.")
        return
    print("Available generated files:")
    for i, (audio_path, shapes_path) in enumerate(generated_files):
        print(f"{i + 1}: Audio: {audio_path}, Shapes: {shapes_path}")
        
    while True:
        user_input = input("Enter the number of the file to play, or 'q' to quit: ").strip().lower()       
        if user_input == 'q':
            break
        try:
            index = int(user_input) - 1
        except ValueError as e:
            print("Invalid input. Please enter a number.")
            print("ValueError:", e)
            continue 
        if 0 <= index < len(generated_files):
            audio_path, shapes_path = generated_files[index]
            try:
                generated_facial_data = load_animation(shapes_path)
            except Exception as e:
                print("Error loading facial data:", e)
                continue
            
            # Send "startspeaking" emote before running the animation (if enabled)
            if ENABLE_EMOTE_CALLS:
                EmoteConnect.send_emote("startspeaking")
            
            try:
                run_audio_animation(audio_path, generated_facial_data, py_face, socket_connection, default_animation_thread)
            except Exception as e:
                print("Error running audio animation:", e)
            finally:
                # Send "stopspeaking" emote after running the animation (if enabled)
                if ENABLE_EMOTE_CALLS:
                    EmoteConnect.send_emote("stopspeaking")
        else:
            print("Invalid selection. Please try again.")

if __name__ == '__main__':
    try:
        main()
    finally:
        stop_default_animation.set()
        if default_animation_thread:
            default_animation_thread.join()
        pygame.quit()
        socket_connection.close()


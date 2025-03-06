# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.


import pygame
import warnings
warnings.filterwarnings(
    "ignore", 
    message="Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work"
)
from threading import Thread

from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from utils.files.file_utils import list_generated_files, load_facial_data_from_csv
from utils.generated_runners import run_audio_animation
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

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
            if 0 <= index < len(generated_files):
                audio_path, shapes_path = generated_files[index]
                generated_facial_data = load_facial_data_from_csv(shapes_path)
                run_audio_animation(audio_path, generated_facial_data, py_face, socket_connection, default_animation_thread)
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

if __name__ == '__main__':
    try:
        main()
    finally:
        stop_default_animation.set()
        if default_animation_thread:
            default_animation_thread.join()
        pygame.quit()
        socket_connection.close()

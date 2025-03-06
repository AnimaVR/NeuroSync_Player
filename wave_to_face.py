# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.


import os
import pygame
from threading import Thread

from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation
from utils.audio_face_workers import process_wav_file
from utils.files.file_utils import  initialize_directories, ensure_wav_input_folder_exists, list_wav_files


if __name__ == "__main__":
    # Initialize directories and other resources
    initialize_directories()

    # Ensure wav_input folder exists
    wav_input_folder = os.path.join(os.getcwd(), 'wav_input')
    ensure_wav_input_folder_exists(wav_input_folder)

    # Initialize py_face and the socket connection
    py_face = initialize_py_face()
    socket_connection = create_socket_connection()

    # Start the default animation thread
    default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
    default_animation_thread.start()

    try:
        while True:
            # List .wav files in the folder
            wav_files = list_wav_files(wav_input_folder)

            if not wav_files:
                print("Please add some .wav files to the 'wav_input' folder.")
                break

            # Display available files with numbers
            print("\nAvailable .wav files:")
            for idx, file in enumerate(wav_files, start=1):
                print(f"{idx}: {file}")

            user_choice = input("\nEnter the number of the .wav file to process (or 'q' to quit): ").strip()

            if user_choice.lower() == 'q':
                break

            if user_choice.isdigit():
                file_index = int(user_choice) - 1
                if 0 <= file_index < len(wav_files):
                    selected_file = os.path.join(wav_input_folder, wav_files[file_index])
                    process_wav_file(selected_file, py_face, socket_connection, default_animation_thread)
                else:
                    print("Invalid selection. Please choose1 a valid number from the list.")
            else:
                print("Invalid input. Please enter a number or 'q' to quit.")

    finally:
        # Stop the default animation when quitting
        stop_default_animation.set()
        if default_animation_thread:
            default_animation_thread.join()
        pygame.quit()
        socket_connection.close()

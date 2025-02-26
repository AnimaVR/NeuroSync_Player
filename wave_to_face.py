# This code is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
# For more details, visit: https://creativecommons.org/licenses/by-nc/4.0/

import os
import pygame
from threading import Thread

from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

from utils.neurosync_api_connect import send_audio_to_neurosync, read_audio_file_as_bytes
from utils.api_utils import save_generated_data_from_wav, initialize_directories
from utils.generated_utils import run_audio_animation


def ensure_wav_input_folder_exists(folder_path):
    """
    Checks if the wav_input folder exists. If not, creates it.
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder: {folder_path}")


def list_wav_files(folder_path):
    """
    Lists all .wav files in the provided folder and returns them as a list.
    """
    files = [f for f in os.listdir(folder_path) if f.lower().endswith('.wav')]
    if not files:
        print("No .wav files found in the wav_input folder.")
    return files


def process_wav_file(wav_file, py_face, socket_connection, default_animation_thread):
    """
    Processes the wav file by sending it to the API and running the animation.
    """
    # Check if the file exists
    if not os.path.exists(wav_file):
        print(f"File {wav_file} does not exist.")
        return

    # Read the wav file as bytes
    audio_bytes = read_audio_file_as_bytes(wav_file)

    if audio_bytes is None:
        print(f"Failed to read {wav_file}")
        return

    # Send the audio bytes to the API and get the blendshapes
    blendshapes = send_audio_to_neurosync(audio_bytes)

    if blendshapes is None:
        print("Failed to get blendshapes from the API.")
        return

    # Run the animation using the blendshapes data
    run_audio_animation(wav_file, blendshapes, py_face, socket_connection, default_animation_thread)

    # Save the generated blendshape data
    save_generated_data_from_wav(wav_file, blendshapes)


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

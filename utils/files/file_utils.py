import os
import shutil
import pandas as pd
import wave
import uuid
import numpy as np
import soundfile as sf
from utils.csv.save_csv import save_generated_data_as_csv
from utils.audio.save_audio import save_audio_file

from utils.neurosync.neurosync_api_connect import send_audio_to_neurosync

GENERATED_DIR = 'generated'

def process_audio_files():
    """
    Processes the audio files in the 'generated' directory by sending them to the API and regenerating the facial blendshapes.
    """
    # Get all directories inside the GENERATED_DIR
    directories = [d for d in os.listdir(GENERATED_DIR) if os.path.isdir(os.path.join(GENERATED_DIR, d))]
    
    for directory in directories:
        dir_path = os.path.join(GENERATED_DIR, directory)
        audio_path = os.path.join(dir_path, 'audio.wav')
        shapes_path = os.path.join(dir_path, 'shapes.csv')
        
        if os.path.exists(audio_path):
            print(f"Processing: {audio_path}")
            
            # Read the audio file as bytes
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
            
            # Send audio to the API to generate facial blendshapes
            generated_facial_data = send_audio_to_neurosync(audio_bytes)
            
            if generated_facial_data is None:
                print(f"Failed to generate facial data for {audio_path}")
                continue

            # Move old shapes.csv to an 'old' folder and rename it with a unique identifier
            old_dir = os.path.join(dir_path, 'old')
            os.makedirs(old_dir, exist_ok=True)

            if os.path.exists(shapes_path):
                unique_old_name = f"shapes_{uuid.uuid4()}.csv"
                shutil.move(shapes_path, os.path.join(old_dir, unique_old_name))
            
            # Save the new blendshapes as a CSV
            save_generated_data_as_csv(generated_facial_data, shapes_path)
            
            print(f"New shapes.csv generated and old shapes.csv moved to {old_dir}")


def initialize_directories():
    if not os.path.exists(GENERATED_DIR):
        os.makedirs(GENERATED_DIR)


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


def list_generated_files():
    """List all the generated audio and face blend shape CSV files in the generated directory."""
    directories = [d for d in os.listdir(GENERATED_DIR) if os.path.isdir(os.path.join(GENERATED_DIR, d))]
    generated_files = []
    for directory in directories:
        audio_path = os.path.join(GENERATED_DIR, directory, 'audio.wav')
        shapes_path = os.path.join(GENERATED_DIR, directory, 'shapes.csv')
        if os.path.exists(audio_path) and os.path.exists(shapes_path):
            generated_files.append((audio_path, shapes_path))
    return generated_files

def load_facial_data_from_csv(csv_path):
    """Load facial data from a CSV file, excluding 'Timecode' and 'BlendshapeCount' columns."""
    data = pd.read_csv(csv_path)
    data = data.drop(columns=['Timecode', 'BlendshapeCount'], errors='ignore')
    return data.values


def save_generated_data(audio_bytes, generated_facial_data):
    unique_id = str(uuid.uuid4())
    output_dir = os.path.join(GENERATED_DIR, unique_id)
    os.makedirs(output_dir, exist_ok=True)

    audio_path = os.path.join(output_dir, 'audio.wav')
    shapes_path = os.path.join(output_dir, 'shapes.csv')

    # Attempt to save the audio using the existing method
    save_audio_file(audio_bytes, audio_path)

    # Validate if the saved file is a valid WAV file
    try:
        with wave.open(audio_path, 'rb') as wav_file:
            wav_file.readframes(1)  # Try to read the first frame
    except (wave.Error, EOFError):
        # If the file is not valid, rewrite it using soundfile
        print(f"The file {audio_path} was not a valid WAV file. Rewriting it using soundfile.")
        with sf.SoundFile(audio_path, mode='w', samplerate=88200, channels=1, format='WAV', subtype='PCM_16') as f:
            f.write(np.frombuffer(audio_bytes, dtype=np.int16))

    # Save the generated facial data as a CSV file
    save_generated_data_as_csv(generated_facial_data, shapes_path)

    return unique_id, audio_path, shapes_path

def save_generated_data_from_wav(wav_file_path, generated_facial_data):
    # Create a unique ID for the output directory
    unique_id = str(uuid.uuid4())
    output_dir = os.path.join(GENERATED_DIR, unique_id)
    os.makedirs(output_dir, exist_ok=True)

    # Define paths for the audio and facial data
    audio_path = os.path.join(output_dir, 'audio.wav')
    shapes_path = os.path.join(output_dir, 'shapes.csv')

    try:
        shutil.copy(wav_file_path, audio_path)
    except shutil.SameFileError:
        print(f"Audio file '{wav_file_path}' is already in the correct location.")

    save_generated_data_as_csv(generated_facial_data, shapes_path)

    return unique_id, audio_path, shapes_path

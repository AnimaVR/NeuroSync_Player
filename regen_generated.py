# This code is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
# For more details, visit: https://creativecommons.org/licenses/by-nc/4.0/

import os
import shutil
import uuid

from utils.neurosync_api_connect import send_audio_to_neurosync
from utils.csv.save_csv import save_generated_data_as_csv

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

if __name__ == '__main__':
    process_audio_files()

# This code is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
# For more details, visit: https://creativecommons.org/licenses/by-nc/4.0/

import librosa
import wave 
import io
import numpy as np


def save_audio_file(audio_bytes, output_path, target_sr=88200):

    y, sr = librosa.load(io.BytesIO(audio_bytes), sr=None)
    
    if sr != target_sr:
        y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
        sr = target_sr

    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(1)  # Mono audio
        wf.setsampwidth(2)  # Assuming 16-bit PCM audio
        wf.setframerate(sr)
        wf.writeframes((y * 32767).astype(np.int16))  # Convert float32 to int16 for WAV format
    print(f"Audio data saved to {output_path}")


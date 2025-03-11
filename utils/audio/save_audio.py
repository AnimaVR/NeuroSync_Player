import soundfile as sf       # Alternative to librosa for loading audio
import wave
import io
import numpy as np
import scipy.signal         # For high-quality resampling

def save_audio_file(audio_bytes, output_path, target_sr=88200):
    # Read the audio data and sampling rate from the bytes using soundfile
    data, sr = sf.read(io.BytesIO(audio_bytes))
    
    # If the audio has more than one channel, convert to mono by averaging channels
    if data.ndim > 1:
        data = np.mean(data, axis=1)
    
    # Resample the audio if the original sample rate doesn't match the target
    if sr != target_sr:
        # Using resample_poly for efficient and high-quality resampling.
        # It rescales the audio by treating target_sr as the "up" factor and sr as the "down" factor.
        data = scipy.signal.resample_poly(data, target_sr, sr)
        sr = target_sr

    # Write the processed audio data to a WAV file
    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(1)         # Output mono audio
        wf.setsampwidth(2)         # 16-bit PCM audio (2 bytes per sample)
        wf.setframerate(sr)
        # Scale float audio (typically in range [-1, 1]) to int16
        wf.writeframes((data * 32767).astype(np.int16).tobytes())
    
    print(f"Audio data saved to {output_path}")


''' # this can cause numpy/numba conflicts...
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
'''

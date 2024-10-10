import librosa
import io

from utils.audio.processing.audio_utils import bandpass_filter, loudness_normalization

def load_and_preprocess_audio(audio_path, sr=88200):
    y, sr = load_audio(audio_path, sr)
    if sr != 88200:
        y = librosa.resample(y, orig_sr=sr, target_sr=88200)
        sr = 88200
    
    # Apply bandpass filtering
 #   y = bandpass_filter(y, sr)

    # Apply loudness normalization
    y = loudness_normalization(y)

    return y, sr

def load_audio(audio_path, sr=88200):
    y, sr = librosa.load(audio_path, sr=sr)
    print(f"Loaded audio file '{audio_path}' with sample rate {sr}")
    return y, sr

def load_audio_from_bytes(audio_bytes, sr=88200):
    audio_file = io.BytesIO(audio_bytes)
    y, sr = librosa.load(audio_file, sr=sr)

    # Apply bandpass filtering
  #  y = bandpass_filter(y, sr)

    # Apply loudness normalization
    y = loudness_normalization(y)

    return y, sr

def load_audio_file_from_memory(audio_bytes, sr=88200):
    """Load audio from memory bytes."""
    y, sr = librosa.load(io.BytesIO(audio_bytes), sr=sr)
    print(f"Loaded audio data with sample rate {sr}")

    # Apply bandpass filtering
 #   y = bandpass_filter(y, sr)

    # Apply loudness normalization
    y = loudness_normalization(y)

    return y, sr
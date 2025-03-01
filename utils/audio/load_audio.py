import librosa
import io

from scipy.signal import butter, lfilter
import numpy as np


def bandpass_filter(y, sr, lowcut=300, highcut=3400, order=1):
    nyquist = 0.5 * sr
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    y_filtered = lfilter(b, a, y)
    return y_filtered

def loudness_normalization(y, target_peak_dB=-3.0, percentile=95):
    # Compute a robust peak by taking the percentile of the absolute values
    robust_peak = np.percentile(np.abs(y), percentile)
    
    # Convert the robust peak to dB
    current_peak_dB = 20 * np.log10(robust_peak)
    
    # Compute the gain required to match the target peak dB
    gain = 10**((target_peak_dB - current_peak_dB) / 20)
    
    # Apply the gain to normalize the audio signal
    y_normalized = y * gain
    
    return y_normalized

def load_and_preprocess_audio(audio_path, sr=88200):
    y, sr = load_audio(audio_path, sr)
    if sr != 88200:
        y = librosa.resample(y, orig_sr=sr, target_sr=88200)
        sr = 88200
    
    y = loudness_normalization(y)

    return y, sr

def load_audio(audio_path, sr=88200):
    y, sr = librosa.load(audio_path, sr=sr)
    print(f"Loaded audio file '{audio_path}' with sample rate {sr}")
    return y, sr

def load_audio_from_bytes(audio_bytes, sr=88200):
    audio_file = io.BytesIO(audio_bytes)
    y, sr = librosa.load(audio_file, sr=sr)
    
    y = loudness_normalization(y)
    
    return y, sr

def load_audio_file_from_memory(audio_bytes, sr=88200):
    """Load audio from memory bytes."""
    y, sr = librosa.load(io.BytesIO(audio_bytes), sr=sr)
    print(f"Loaded audio data with sample rate {sr}")
    
    y = loudness_normalization(y)
    
    return y, sr

"""
convert_audio.py
----------------
This module provides functions to convert and validate audio data.
It handles raw PCM wrapping, file conversion to WAV, and safe conversions
using pydub. The functionality is kept intact with improved readability.
"""

import io
import wave
import numpy as np
from pydub import AudioSegment
import soundfile as sf
from scipy.io.wavfile import write

# Optional: Import magic only when needed (inside the function) to avoid
# issues on systems where it's not installed.
# import magic  


def audio_to_bytes(audio_data, sr, channels=1):
    """
    Convert audio data (NumPy array with float values in [-1, 1]) to bytes
    in WAV format (16-bit PCM).
    """
    # Convert to int16 and scale
    audio_data_int16 = (audio_data * 32767).astype(np.int16)
    byte_io = io.BytesIO()
    with wave.open(byte_io, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(sr)
        wf.writeframes(audio_data_int16.tobytes())
    byte_io.seek(0)
    return byte_io.read()


def pcm_to_wav(pcm_data, sample_rate=22050, channels=1, sample_width=2):
    """
    Wrap raw PCM data into a WAV container using the wave module.
    Returns a BytesIO object positioned at the start.
    """
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    wav_io.seek(0)
    return wav_io


def convert_to_wav(audio_path, output_path=None):
    """
    Convert any audio file to WAV format using soundfile and scipy.
    If output_path is provided, the WAV file is written there.
    Otherwise, the input file is overwritten.
    """
    data, samplerate = sf.read(audio_path)
    # Ensure data is in 16-bit PCM format
    data_int16 = (data * 32767).astype(np.int16)
    if output_path is None:
        output_path = audio_path
    write(output_path, samplerate, data_int16)
    return output_path


def bytes_to_wav(audio_bytes, sample_rate, channels, sample_width):
    """
    Wrap raw audio bytes into a WAV container and return a BytesIO object.
    """
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_bytes)
    wav_io.seek(0)
    return wav_io


def safely_convert_audio(audio_bytes, input_format, target_sample_rate=88200):
    """
    Safely convert audio using pydub, changing its frame rate if needed.
    Returns WAV bytes on success or None on failure.
    """
    try:
        with io.BytesIO(audio_bytes) as input_buffer:
            audio = AudioSegment.from_file(input_buffer, format=input_format)
            audio = audio.set_frame_rate(target_sample_rate)
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            return wav_io.getvalue()
    except Exception as e:
        print(f"Audio conversion error: {e}")
        return None


def is_valid_audio(audio_bytes, allowed_types=None):
    """
    Check if the audio_bytes represent a valid WAV or MP3 file using MIME type.
    """
    if allowed_types is None:
        allowed_types = ['audio/mpeg', 'audio/wav']
    try:
        import magic  # Import magic here to avoid issues if it's not needed
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(audio_bytes)
        return file_type in allowed_types
    except Exception as e:
        print(f"Error checking audio MIME type: {e}")
        return False

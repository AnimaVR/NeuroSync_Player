import wave
import io
from pydub import AudioSegment
import magic 
import numpy as np

import numpy as np
import soundfile as sf
from scipy.io.wavfile import write


def audio_to_bytes(audio_data, sr):
    """Convert audio data to bytes suitable for WAV format."""
    audio_data = (audio_data * 32767).astype(np.int16)  # Convert float32 to int16
    byte_io = io.BytesIO()
    with wave.open(byte_io, 'wb') as wf:
        wf.setnchannels(1)  # Mono audio
        wf.setsampwidth(2)  # Assuming 16-bit PCM audio
        wf.setframerate(sr)
        wf.writeframes(audio_data.tobytes())
    byte_io.seek(0)
    return byte_io.read()


def pcm_to_wav(pcm_data, sample_rate=22050, channels=1, sample_width=2):
    """
    Helper function to wrap raw PCM data into a WAV container.
    This uses the wave module to write a proper WAV header.
    """
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    wav_io.seek(0)
    return wav_io


def convert_to_wav(audio_path):
    """Convert any audio file to WAV format if it's not already WAV."""
    data, samplerate = sf.read(audio_path)
    data = (data * 32767).astype(np.int16)  # Ensure 16-bit PCM
    write(audio_path, samplerate, data)
    return audio_path



def bytes_to_wav(audio_bytes, sample_rate, channels, sample_width):
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_bytes)
    wav_io.seek(0)
    return wav_io


def safely_convert_audio(audio_bytes, input_format):
    """Convert audio using pydub with basic sandboxing."""
    try:
        with io.BytesIO(audio_bytes) as input_buffer:
            audio = AudioSegment.from_file(input_buffer, format=input_format)
            audio = audio.set_frame_rate(88200)  
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            return wav_io.getvalue()
    except Exception as e:
        print(f"Audio conversion error: {e}")
        return None
    

   
def is_valid_audio(audio_bytes):
    """Check if the uploaded file is a valid WAV or MP3 based on MIME type."""
    mime = magic.Magic(mime=True)
    file_type = mime.from_buffer(audio_bytes)

    allowed_types = ['audio/mpeg', 'audio/wav']
    return file_type in allowed_types    

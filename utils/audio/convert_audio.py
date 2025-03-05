import wave
import io
from pydub import AudioSegment
import magic 


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

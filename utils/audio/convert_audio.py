import wave
import io


def bytes_to_wav(audio_bytes, sample_rate, channels, sample_width):
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_bytes)
    wav_io.seek(0)
    return wav_io

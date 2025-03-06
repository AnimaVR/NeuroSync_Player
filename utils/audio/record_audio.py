import io
import pyaudio
import numpy as np
import keyboard
import soundfile as sf

def record_audio_until_release(sr=22050):
    """Record audio from the default microphone until the right Ctrl key is released."""
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sr,
                    input=True,
                    frames_per_buffer=1024)

    print("Recording... Press and hold Right Ctrl to record, release to stop.")

    frames = []

    while keyboard.is_pressed('right ctrl'):
        data = stream.read(1024)
        frames.append(data)

    print("Finished recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    audio_bytes = b''.join(frames)
 
    audio_file = io.BytesIO()
    with sf.SoundFile(audio_file, mode='w', samplerate=sr, channels=1, format='WAV', subtype='PCM_16') as f:
        f.write(np.frombuffer(audio_bytes, dtype=np.int16))
    
    audio_file.seek(0)  
    return audio_file.read()

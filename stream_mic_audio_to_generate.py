# stream_mic_audio_to_generate.py

import sounddevice as sd
import numpy as np
import time

from concurrent.futures import ThreadPoolExecutor

from livelink.connect.livelink_init import initialize_py_face, create_socket_connection
from utils.mic_stream.mic_stream_utils import process_audio_chunk, buffer_lock

BUFFER_DURATION = 1  # seconds
SAMPLING_RATE = 88200  # Hz
CHANNELS = 1
FRAMES_PER_BUFFER = int(SAMPLING_RATE * BUFFER_DURATION)

py_face = initialize_py_face()
socket_connection = create_socket_connection()

audio_buffer = []
executor = ThreadPoolExecutor(max_workers=12)

def audio_callback(indata, frames, time, status):
    """Callback function to put audio data into the buffer."""
    if status:
        print(f"Audio status: {status}", flush=True)
    with buffer_lock:
        audio_buffer.extend(indata.copy())
        if len(audio_buffer) >= FRAMES_PER_BUFFER:
            audio_chunk = np.array(audio_buffer[:FRAMES_PER_BUFFER])
            del audio_buffer[:FRAMES_PER_BUFFER]
            print(f"Submitting {len(audio_chunk)} frames for processing.")
            process_audio_chunk(audio_chunk, SAMPLING_RATE, py_face, socket_connection, executor)

def main():
    stream = sd.InputStream(callback=audio_callback, channels=CHANNELS, samplerate=SAMPLING_RATE, blocksize=FRAMES_PER_BUFFER)
    stream.start()
    
    print("Recording and processing audio... Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop()
        stream.close()
        executor.shutdown(wait=True)
        print("Audio recording and processing stopped.")

if __name__ == '__main__':
    main()

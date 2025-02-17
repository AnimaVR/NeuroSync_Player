# utils/audio_workers.py
from utils.generated_utils import run_audio_animation_from_bytes
from utils.neurosync_api_connect import send_audio_to_neurosync
from utils.local_tts import call_local_tts 
from utils.eleven_labs import get_elevenlabs_audio

def tts_worker(chunk_queue, audio_queue, USE_LOCAL_AUDIO, VOICE_NAME):
    """
    Processes text chunks from chunk_queue by generating audio (using local TTS or ElevenLabs)
    and retrieving corresponding facial data, then enqueues the results into audio_queue.
    """
    while True:
        chunk = chunk_queue.get()
        if chunk is None:
            break
        if USE_LOCAL_AUDIO:
            audio_bytes = call_local_tts(chunk)
        else:
            audio_bytes = get_elevenlabs_audio(chunk, VOICE_NAME)
        if audio_bytes:
            facial_data = send_audio_to_neurosync(audio_bytes)
            if facial_data:
                audio_queue.put((audio_bytes, facial_data))
            else:
                print("Failed to get facial data for chunk:", chunk)
        else:
            print("Failed to generate audio for chunk:", chunk)
        chunk_queue.task_done()

def audio_queue_worker(audio_queue, py_face, socket_connection, default_animation_thread):
    """
    Processes audio items from audio_queue sequentially.
    Each item is a tuple (audio_bytes, facial_data) that is played back,
    ensuring that the animations remain in sync.
    """
    while True:
        item = audio_queue.get()
        if item is None:
            break
        audio_bytes, facial_data = item
        run_audio_animation_from_bytes(audio_bytes, facial_data, py_face, socket_connection, default_animation_thread)
        audio_queue.task_done()

from utils.neurosync.multi_part_return import get_tts_with_blendshapes
from utils.neurosync.neurosync_api_connect import send_audio_to_neurosync
from utils.tts.local_tts import call_local_tts 
from utils.tts.eleven_labs import get_elevenlabs_audio
import string

def tts_worker(chunk_queue, audio_queue, USE_LOCAL_AUDIO=True, VOICE_NAME='Lily', USE_COMBINED_ENDPOINT=False):
    """
    Processes text chunks from chunk_queue.
    
    When USE_COMBINED_ENDPOINT is True, a single API call retrieves both audio and blendshapes.
    Otherwise, the worker generates audio using either local TTS or ElevenLabs (based on USE_LOCAL_AUDIO)
    and then retrieves facial data separately.
    
    The results (audio_bytes, facial/blendshape data) are enqueued into audio_queue.
    
    Parameters:
      - chunk_queue: Queue holding text chunks.
      - audio_queue: Queue where the (audio_bytes, facial_data) tuple is enqueued.
      - USE_LOCAL_AUDIO (bool): If True, use local TTS. If False, use ElevenLabs.
      - VOICE_NAME (str): Voice name to use for ElevenLabs TTS.
      - USE_COMBINED_ENDPOINT (bool): If True, use the combined TTS+blendshapes endpoint.
    """
    while True:
        chunk = chunk_queue.get()
        if chunk is None:
            break

        # Skip if the chunk is empty or only punctuation/whitespace.
        if not chunk.strip() or all(c in string.punctuation or c.isspace() for c in chunk):
            chunk_queue.task_done()
            continue

        if USE_COMBINED_ENDPOINT:
            # Use the combined endpoint: one call returns both audio and blendshapes.
            audio_bytes, blendshapes = get_tts_with_blendshapes(chunk)
            if audio_bytes and blendshapes:
                audio_queue.put((audio_bytes, blendshapes))
            else:
                print("❌ Failed to retrieve audio and blendshapes for chunk:", chunk)
        else:
            # Generate audio using the chosen TTS engine.
            if USE_LOCAL_AUDIO:
                audio_bytes = call_local_tts(chunk)
            else:
                audio_bytes = get_elevenlabs_audio(chunk, VOICE_NAME)

            if audio_bytes:
                # Retrieve facial/blendshape data using the separate API.
                facial_data = send_audio_to_neurosync(audio_bytes)
                if facial_data:
                    audio_queue.put((audio_bytes, facial_data))
                else:
                    print("❌ Failed to get facial data for chunk:", chunk)
            else:
                print("❌ TTS generation failed for chunk:", chunk)

        chunk_queue.task_done()

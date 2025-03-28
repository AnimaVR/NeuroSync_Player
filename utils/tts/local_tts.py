# utils/local_tts.py
import requests

from config import LOCAL_TTS_URL

def call_local_tts(text, voice=None): 
    """
    Calls the local TTS Flask endpoint to generate speech for the given (already-cleaned) text.
    Optionally, a voice can be specified.
    Returns the audio bytes if successful, otherwise returns None.
    """
    payload = {"text": text}

    if voice is not None:
        payload["voice"] = voice

    try:
        response = requests.post(LOCAL_TTS_URL, json=payload)
        response.raise_for_status()
        return response.content
    except Exception as e:
        # Optionally log error here
        return None

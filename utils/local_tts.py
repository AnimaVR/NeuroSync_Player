# utils/local_tts.py
import requests

# Constants for the local TTS endpoint
LOCAL_TTS_URL = "http://192.168.1.1:8000/generate_speech_nk"  # Update if needed


def call_local_tts(text):
    """
    Calls the local TTS Flask endpoint to generate speech for the given text.
    Returns the audio bytes if successful, otherwise returns None.
    """
    payload = {"text": text}
    try:
        # Removed API key header
        response = requests.post(LOCAL_TTS_URL, json=payload)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error calling local TTS: {e}")
        return None
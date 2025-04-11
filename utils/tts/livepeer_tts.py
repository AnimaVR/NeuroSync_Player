import io
import json
import requests

LIVEPEER_GATEWAY_URL = "https://dream-gateway.livepeer.cloud/text-to-speech"



def get_livepeer_audio(text, voice_description):

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "model_id": "parler-tts/parler-tts-large-v1",
        "text": text,
        "description": voice_description
    }

    # First request to get the audio URL
    response = requests.post(LIVEPEER_GATEWAY_URL, headers=headers, json=payload)
    response.raise_for_status()
    
    # Parse the JSON response to get the audio URL
    response_data = response.json()
    audio_url = response_data['audio']['url']
    
    # Second request to download the actual audio file
    audio_response = requests.get(audio_url)
    audio_response.raise_for_status()
    
    return audio_response.content 
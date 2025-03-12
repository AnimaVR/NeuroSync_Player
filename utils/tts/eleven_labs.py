import io
import json
import requests

voices = {
    "Sarah": "EXAVITQu4vr4xnSDxMaL",
    "Laura": "FGY2WhTYpPnrIDTdsKH5",
    "Charlie": "IKne3meq5aSn9XLyUdCD",
    "George": "JBFqnCBsd6RMkjVDRZzb",
    "Callum": "N2lVS1w4EtoT3dr4eOWO",
    "Liam": "TX3LPaxmHKxFdv7VOQHJ",
    "Charlotte": "XB0fDUnXU5powFXDhCwa",
    "Alice": "Xb7hH8MSUJpSbSDYk0k2",
    "Matilda": "XrExE9yKIg1WjnnlVkGX",
    "Will": "bIHbv24MWmeRgasZH58o",
    "Jessica": "cgSgspJ2msm6clMCkdW9",
    "Eric": "cjVigY5qzO86Huf0OWal",
    "Brian": "nPczCjzI2devNBz1zQrb",
    "Daniel": "onwK4e9ZLuTAKqWW03F9",
    "Lily": "pFZP5JQG7iQjIQuC4Bku",
    "Bill": "pqHfZKP75CvOlQylNhV4",
}

XI_API_KEY = "YOUR-ELEVENLABS-API-KEY"  # Replace with your actual ElevenLabs API key

def get_voice_id_by_name(name):
    return voices.get(name)

def get_elevenlabs_audio(text, name):
    VOICE_ID = get_voice_id_by_name(name)
    if VOICE_ID is None:
        raise ValueError(f"Voice for {name} not found.")
    
    API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"
    
    headers = {
        "xi-api-key": XI_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.5,
            "use_speaker_boost": True
        }
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()

    audio_data = response.content
    return audio_data

def get_speech_to_speech_audio(audio_bytes, name):
    VOICE_ID = get_voice_id_by_name(name)
    if VOICE_ID is None:
        raise ValueError(f"Voice for {name} not found.")
    
    STS_API_URL = f"https://api.elevenlabs.io/v1/speech-to-speech/{VOICE_ID}/stream"
    
    headers = {
        "Accept": "application/json",
        "xi-api-key": XI_API_KEY
    }

    data = {
        "model_id": "eleven_english_sts_v2",
        "voice_settings": json.dumps({
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.5,
            "use_speaker_boost": True
        })
    }

    files = {
        "audio": ("audio.wav", io.BytesIO(audio_bytes), "audio/wav")
    }

    response = requests.post(STS_API_URL, headers=headers, data=data, files=files)
    response.raise_for_status()  # Raise an error for bad responses

    # Return the full response content as audio data
    audio_data = response.content
    return audio_data

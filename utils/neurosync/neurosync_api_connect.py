# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

import requests
import json

API_KEY = "YOUR-NEUROSYNC-API-KEY"  # Your API key
REMOTE_URL = "https://api.neurosync.info/audio_to_blendshapes"  # External API URL
LOCAL_URL = "http://127.0.0.1:5000/audio_to_blendshapes"  # Local URL

def send_audio_to_neurosync(audio_bytes, use_local=True):
    try:
        # Use the local or remote URL depending on the flag
        url = LOCAL_URL if use_local else REMOTE_URL
        headers = {}
        if not use_local:
            headers["API-Key"] = API_KEY

        response = post_audio_bytes(audio_bytes, url, headers)
        response.raise_for_status()  
        json_response = response.json()
        return parse_blendshapes_from_json(json_response)

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return None

def validate_audio_bytes(audio_bytes):
    return audio_bytes is not None and len(audio_bytes) > 0

def post_audio_bytes(audio_bytes, url, headers):
    headers["Content-Type"] = "application/octet-stream"
    response = requests.post(url, headers=headers, data=audio_bytes)
    return response

def parse_blendshapes_from_json(json_response):
    blendshapes = json_response.get("blendshapes", [])
    facial_data = []

    for frame in blendshapes:
        frame_data = [float(value) for value in frame]
        facial_data.append(frame_data)

    return facial_data

import requests
import json

API_KEY = "YOUR-NEUROSYNC-API-KEY"  # Your API key
REMOTE_URL = "https://api.neurosync.info/audio_to_blendshapes"  # External API URL
LOCAL_URL = "http://127.0.0.1:5000/audio_to_blendshapes"  # Local URL

def send_audio_to_audio2face(audio_bytes, use_local=False):
    """
    Sends audio bytes to the Audio-to-Face API and returns blendshapes.

    :param audio_bytes: Binary data (audio)
    :param use_local: Boolean flag to switch between local and remote APIs
    :return: List of blendshapes or None on failure
    """
    if not validate_audio_bytes(audio_bytes):
        print("Audio bytes are null or empty, skipping send.")
        return None

    try:
        # Use the local or remote URL depending on the flag
        url = LOCAL_URL if use_local else REMOTE_URL

        # Only send API key if not using local
        headers = {}
        if not use_local:
            headers["API-Key"] = API_KEY

        response = post_audio_bytes(audio_bytes, url, headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        json_response = response.json()
        return parse_blendshapes_from_json(json_response)

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return None

def read_audio_file_as_bytes(file_path):
    """
    Reads a file (like a .wav file) and returns its content as bytes.

    :param file_path: Path to the audio file
    :return: Audio bytes
    """
    try:
        with open(file_path, 'rb') as audio_file:
            return audio_file.read()  # Read the file in binary mode and return bytes
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error reading audio file: {e}")
        return None

def validate_audio_bytes(audio_bytes):
    """
    Validates if audio bytes are non-empty.

    :param audio_bytes: Binary data (audio)
    :return: True if valid, False otherwise
    """
    return audio_bytes is not None and len(audio_bytes) > 0

def post_audio_bytes(audio_bytes, url, headers):
    """
    Sends audio bytes to the API (local or remote).

    :param audio_bytes: Binary data (audio)
    :param url: Target API URL (local or remote)
    :param headers: HTTP headers, including API key if needed
    :return: Response object
    """
    headers["Content-Type"] = "application/octet-stream"
    response = requests.post(url, headers=headers, data=audio_bytes)
    return response

def parse_blendshapes_from_json(json_response):
    """
    Parses the blendshapes from the API's JSON response.

    :param json_response: JSON response containing blendshapes
    :return: List of blendshapes
    """
    blendshapes = json_response.get("blendshapes", [])
    facial_data = []

    for frame in blendshapes:
        frame_data = [float(value) for value in frame]
        facial_data.append(frame_data)

    return facial_data

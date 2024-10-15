import requests
import json
import wave
import io

API_KEY = "YOUR-NEUROSYNC-API-KEY"  # Your API key
REMOTE_URL = "https://api.neurosync.info/audio_to_blendshapes"  # External API URL
LOCAL_URL = "http://127.0.0.1:5000/audio_to_blendshapes"  # Local URL


def is_wav_audio(audio_bytes):
    """
    Validates if the given bytes are a valid WAV audio file.
    
    :param audio_bytes: Binary data (audio)
    :return: True if it's a valid WAV file, False otherwise
    """
    try:
        # Wrap the audio bytes in a BytesIO object to simulate a file
        with wave.open(io.BytesIO(audio_bytes), 'rb') as wav_file:
            # Ensure the file contains audio frames
            if wav_file.getnframes() > 0 and wav_file.getnchannels() > 0:
                return True
    except wave.Error:
        print("Error: The file is not a valid WAV audio file.")
        return False
    except Exception as e:
        print(f"Unexpected error while validating WAV file: {e}")
        return False
    return False

def send_audio_to_neurosync(audio_bytes, use_local=False):
    """
    Sends audio bytes to the Audio-to-Face API and returns blendshapes.

    :param audio_bytes: Binary data (audio)
    :param use_local: Boolean flag to switch between local and remote APIs
    :return: List of blendshapes or None on failure
    """
    # Check if the bytes represent valid WAV audio
    if not is_wav_audio(audio_bytes):
        print("The provided audio bytes are not valid WAV audio.")
        return None

    try:
        # Use the local or remote URL depending on the flag
        url = LOCAL_URL if use_local else REMOTE_URL

        # Only send API key if not using local
        headers = {}
        if not use_local:
            headers["API-Key"] = API_KEY

        # Send the audio bytes to the API
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
    Reads a WAV file and returns its content as bytes.
    Skips unsupported formats and ensures the file is WAV.
    
    :param file_path: Path to the audio file
    :return: Audio bytes if the file is a valid WAV file, None otherwise
    """
    # Ensure the file has a .wav extension
    if not file_path.lower().endswith('.wav'):
        print(f"Unsupported file format: {file_path}. Only WAV files are supported.")
        return None

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

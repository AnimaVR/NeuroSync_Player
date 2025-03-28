# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.
import json
import requests
from config import TTS_WITH_BLENDSHAPES_REALTIME_API 

def parse_multipart_response(response):
    """
    Parses a multipart/mixed response to extract the audio bytes and blendshapes.
    Assumes the endpoint returns two parts:
      Part 1: Content-Type: audio/wav (raw WAV bytes)
      Part 2: Content-Type: application/json (blendshapes data)
    """
    content_type = response.headers.get("Content-Type")
    if not content_type or "boundary=" not in content_type:
        raise ValueError("Missing or invalid Content-Type header with boundary")
    
    boundary = content_type.split("boundary=")[-1].strip()
    raw_parts = response.content.split(("--" + boundary).encode())
    
    audio_bytes = None
    blendshapes = None
    
    for part in raw_parts:
        part = part.strip()
        if not part or part == b"--":
            continue
        if b"\r\n\r\n" not in part:
            continue
        headers_raw, body = part.split(b"\r\n\r\n", 1)
        headers = {}
        for header_line in headers_raw.split(b"\r\n"):
            try:
                line = header_line.decode("utf-8")
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip()] = value.strip()
            except Exception:
                continue
        content_type_part = headers.get("Content-Type")
        if content_type_part == "audio/wav":
            audio_bytes = body.rstrip(b"\r\n")
        elif content_type_part == "application/json":
            blendshapes = json.loads(body.decode("utf-8").strip())
    
    if audio_bytes is None:
        print("❌ Audio bytes not found in response.")
    if blendshapes is None:
        print("❌ Blendshapes data not found in response.")
    
    return audio_bytes, blendshapes

def get_tts_with_blendshapes(text, voice=None):
    """
    Calls the new TTS endpoint with the given text and optional voice.
    Returns a tuple: (audio_bytes, blendshapes) if successful, else (None, None).
    """
    payload = {"text": text}
    if voice is not None:
        payload["voice"] = voice

    try:
        response = requests.post(TTS_WITH_BLENDSHAPES_REALTIME_API , json=payload)
        response.raise_for_status()
        return parse_multipart_response(response)
    except Exception as e:
        print(f"❌ Error calling new TTS endpoint: {e}")
        return None, None

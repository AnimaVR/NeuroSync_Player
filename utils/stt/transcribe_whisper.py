import requests
import base64
import os

TRANSCRIPTION_SERVER_URL = 'http://127.0.0.1:6969/transcribe'

def transcribe_audio(audio_bytes, return_timestamps=False):
    """Transcribe audio with optional timestamps."""
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    try:
        response = requests.post(
            TRANSCRIPTION_SERVER_URL,
            json={
                'audio_base64': audio_base64,
                'return_timestamps': return_timestamps
            }
        )

        # Debugging output
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")

        if response.status_code == 200:
            response_data = response.json()
            transcription = response_data.get('transcription', '').strip()
            timestamps = response_data.get('timestamps', [])
            return transcription, timestamps if return_timestamps else None

        print("Error: Server returned non-200 status code.")
    except requests.exceptions.RequestException as e:
        print(f"Request failed with exception: {e}")

    return None, None

def transcribe_and_save_audio(audio_path, long_form=False):
    """Save transcription and optionally timestamps."""
    transcription_path = audio_path.replace('.wav', '.txt')

    if os.path.exists(transcription_path):
        return '' 

    with open(audio_path, 'rb') as audio_file:
        audio_bytes = audio_file.read()

    transcription, timestamps = transcribe_audio(audio_bytes, return_timestamps=long_form)
    print(f"audio as text : {transcription}") 

    if transcription:
        with open(transcription_path, 'w') as transcription_file:
            transcription_file.write(transcription)

        # Optionally, save timestamps to a separate file
        if long_form and timestamps:
            timestamp_path = audio_path.replace('.wav', '_timestamps.txt')
            with open(timestamp_path, 'w') as timestamp_file:
                for segment in timestamps:
                    timestamp_file.write(f"[{segment['start']}s - {segment['end']}s]: {segment['text']}\n")

    return transcription

import os
import json
from threading import Thread
import pygame
import requests
import openai

from utils.eleven_labs import get_elevenlabs_audio
from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation
from utils.api_utils import save_generated_data, initialize_directories
from utils.generated_utils import run_audio_animation_from_bytes
from utils.neurosync_api_connect import send_audio_to_neurosync

# Constants
USE_LOCAL_LLM = True  # Set to False to use OpenAI API
LLM_API_URL = "http://192.168.1.1:5050/generate_llama"
CHAT_LOGS_DIR = "chat_logs"
VOICE_NAME = 'Lily'
MAX_CONTEXT_LENGTH = 5000
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Set your OpenAI API key in environment variables

# Ensure chat_logs directory exists
os.makedirs(CHAT_LOGS_DIR, exist_ok=True)

def load_chat_history():
    """Loads chat history from the log file."""
    log_file = os.path.join(CHAT_LOGS_DIR, "chat_history.json")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_chat_log(chat_history):
    """Saves the chat history, ensuring it stays within context length."""
    log_file = os.path.join(CHAT_LOGS_DIR, "chat_history.json")
    total_length = sum(len(json.dumps(entry)) for entry in chat_history)
    while total_length > MAX_CONTEXT_LENGTH and chat_history:
        chat_history.pop(0)  # Remove oldest log
        total_length = sum(len(json.dumps(entry)) for entry in chat_history)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, indent=4)

def call_llm(user_input, chat_history):
    """Calls either the local LLM or OpenAI API and returns the response."""
    messages = [{"role": "system", "content": "You are an AI assistant responding concisely."}]
    
    # Add previous chat history
    for entry in chat_history:
        messages.append({"role": "user", "content": entry["input"]})
        messages.append({"role": "assistant", "content": entry["response"]})
    
    # Add current input
    messages.append({"role": "user", "content": user_input})
    
    if USE_LOCAL_LLM:
        try:
            response = requests.post(LLM_API_URL, json={
                "messages": messages,
                "max_new_tokens": 4000,
                "temperature": 1,
                "top_p": 0.9
            })
            
            if response.ok:
                result = response.json()
                return result.get('assistant', {}).get('content', "Error: No response.")
            else:
                print(f"LLM call failed: HTTP {response.status_code}")
                return "Error: LLM call failed."
        except Exception as e:
            print(f"Error calling local LLM: {e}")
            return "Error: Exception occurred."
    else:
        try:
            openai.api_key = OPENAI_API_KEY
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                max_tokens=4000,
                temperature=1,
                top_p=0.9
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return "Error: OpenAI API call failed."

def main():
    initialize_directories()
    py_face = initialize_py_face()
    socket_connection = create_socket_connection()
    chat_history = load_chat_history()
    
    default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
    default_animation_thread.start()
    
    try:
        while True:
            user_input = input("Enter text (or 'q' to quit): ").strip()
            if user_input.lower() == 'q':
                break
            
            llm_response = call_llm(user_input, chat_history)
            print(f"LLM Response: {llm_response}")
            
            chat_history.append({"input": user_input, "response": llm_response})
            save_chat_log(chat_history)
            
            audio_bytes = get_elevenlabs_audio(llm_response, VOICE_NAME) # use a local option for the fastest bestests resultses
            if audio_bytes:
                generated_facial_data = send_audio_to_neurosync(audio_bytes)
                if generated_facial_data:
                    run_audio_animation_from_bytes(audio_bytes, generated_facial_data, py_face, socket_connection, default_animation_thread)
                  #  save_generated_data(audio_bytes, generated_facial_data)
                else:
                    print("Failed to get blendshapes from API.")
            else:
                print("Failed to generate audio.")
    
    finally:
        stop_default_animation.set()
        default_animation_thread.join()
        pygame.quit()
        socket_connection.close()

if __name__ == "__main__":
    main()

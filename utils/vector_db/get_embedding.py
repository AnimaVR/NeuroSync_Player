# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

import os
import requests
from config import USE_OPENAI_EMBEDDING, EMBEDDING_LOCAL_SERVER_URL, EMBEDDING_OPENAI_MODEL, LOCAL_EMBEDDING_SIZE, OPENAI_EMBEDDING_SIZE

def get_embedding(text: str, use_openai: bool = USE_OPENAI_EMBEDDING, openai_api_key: str = None, local_server_url: str = EMBEDDING_LOCAL_SERVER_URL) -> list:
    if use_openai:
        return get_openai_embedding(text, openai_api_key)
    else:
        return get_local_embedding(text, local_server_url)

def get_local_embedding(text: str, local_server_url: str) -> list:
    try:
        payload = {"text": text}
        response = requests.post(local_server_url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        embedding = data.get("embedding")
        if embedding is None:
            raise ValueError("No 'embedding' key in the response.")
        return embedding
    except Exception as e:
        print(f"Error in local embedding provider: {e}")
        return [0.0] * LOCAL_EMBEDDING_SIZE

def get_openai_embedding(text: str, openai_api_key: str = None) -> list:
    try:
        if openai_api_key is None:
            openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key is None:
            raise ValueError("OpenAI API key not provided.")
        
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json"
        }
        payload = {"input": text, "model": EMBEDDING_OPENAI_MODEL}
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            embedding = data["data"][0].get("embedding")
            if embedding is None:
                raise ValueError("No 'embedding' key in the OpenAI response data.")
            return embedding
        else:
            raise ValueError("Invalid response structure from OpenAI embeddings API.")
    except Exception as e:
        print(f"Error in OpenAI embedding provider: {e}")
        return [0.0] * OPENAI_EMBEDDING_SIZE



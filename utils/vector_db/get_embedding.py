# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

import os
import requests

# Global flag to choose the embeddings provider.
# Set to True to use OpenAI embeddings, or False to use local embeddings.
USE_OPENAI = False # If you set this to true, you need to change the embedding length to match openAI 1536 instead of 768 of the local version (or whatever you have as an embedding size)

def get_embedding(text: str, use_openai: bool = USE_OPENAI, openai_api_key: str = None, local_server_url: str = "http://127.0.0.1:7070/get_embedding") -> list:
    """
    Returns the embedding for the given text by choosing either the OpenAI or local embeddings provider.
    
    Args:
        text (str): The input text to embed.
        use_openai (bool, optional): If True, use OpenAI embeddings; otherwise use local embeddings.
                                     Defaults to the global USE_OPENAI flag.
        openai_api_key (str, optional): Your OpenAI API key. If not provided, the environment variable 
                                        OPENAI_API_KEY will be used.
        local_server_url (str, optional): URL for the local embeddings endpoint.
    
    Returns:
        list: The embedding as a list of floats.
              On error, returns a zero vector (length 1536 for OpenAI; 768 for local).
    """
    if use_openai:
        return get_openai_embedding(text, openai_api_key)
    else:
        return get_local_embedding(text, local_server_url)

def get_local_embedding(text: str, local_server_url: str) -> list:
    """
    Uses the local embeddings provider.
    Sends a POST request to the local server with the text payload.
    
    Args:
        text (str): The input text.
        local_server_url (str): The URL endpoint for the local embeddings provider.
    
    Returns:
        list: The embedding as a list of floats.
              On error, returns a zero vector of length 768.
    """
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
        # Return a zero vector of length 768 as a fallback (adjust dimension if needed)
        return [0.0] * 768

def get_openai_embedding(text: str, openai_api_key: str = None) -> list:
    """
    Uses the OpenAI embeddings provider.
    Sends a POST request to OpenAI's embeddings API with the text payload.
    
    Args:
        text (str): The input text.
        openai_api_key (str, optional): Your OpenAI API key. If not provided, the environment variable 
                                        OPENAI_API_KEY will be used.
    
    Returns:
        list: The embedding as a list of floats.
              On error, returns a zero vector of length 1536.
    """
    try:
        # Use the provided API key or get it from the environment.
        if openai_api_key is None:
            openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key is None:
            raise ValueError("OpenAI API key not provided.")
        
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json"
        }
        # Using the model from your C# example.
        payload = {"input": text, "model": "text-embedding-3-small"}
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Expecting a response with a "data" key containing a list of embeddings.
        if "data" in data and len(data["data"]) > 0:
            embedding = data["data"][0].get("embedding")
            if embedding is None:
                raise ValueError("No 'embedding' key in the OpenAI response data.")
            return embedding
        else:
            raise ValueError("Invalid response structure from OpenAI embeddings API.")
    except Exception as e:
        print(f"Error in OpenAI embedding provider: {e}")
        # Return a zero vector of length 1536 as a fallback (adjust dimension if needed)
        return [0.0] * 1536


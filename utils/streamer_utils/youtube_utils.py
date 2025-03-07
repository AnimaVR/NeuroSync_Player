# utils/youtube_utils.py
import time
from googleapiclient.discovery import build

def get_live_chat_id(api_key, video_id):
    """
    Given a live broadcast video ID, retrieve its liveChatId.
    """
    youtube = build('youtube', 'v3', developerKey=api_key)
    response = youtube.videos().list(
        part="liveStreamingDetails",
        id=video_id
    ).execute()
    if response.get('items'):
        live_chat_id = response['items'][0]['liveStreamingDetails'].get('activeLiveChatId')
        return live_chat_id
    return None

def run_youtube_chat_fetcher(message_queue, api_key, live_chat_id):
    """
    Polls the YouTube Live Chat API for new messages and enqueues them.
    If an invalid page token error is encountered, resets the token.
    """
    youtube = build('youtube', 'v3', developerKey=api_key)
    next_page_token = None
    while True:
        try:
            params = {
                'liveChatId': live_chat_id,
                'part': "snippet,authorDetails"
            }
            if next_page_token:
                params['pageToken'] = next_page_token
            response = youtube.liveChatMessages().list(**params).execute()
        except Exception as e:
            error_str = str(e)
            if "page token is not valid" in error_str or "pageTokenInvalid" in error_str:
                print("Invalid page token detected; resetting token.")
                next_page_token = None
                time.sleep(2)  # short delay before retrying
                continue
            print(f"Error fetching YouTube chat messages: {e}")
            time.sleep(5)
            continue

        if 'items' in response:
            for item in response['items']:
                snippet = item.get('snippet', {})
                author = item.get('authorDetails', {})
                timestamp = snippet.get('publishedAt', '')
                message_text = snippet.get('displayMessage', '')
                formatted = f"[{timestamp}] {author.get('displayName', 'Unknown')}: {message_text}"
                message_queue.put(formatted)

        next_page_token = response.get('nextPageToken')
        polling_interval = response.get('pollingIntervalMillis', 1000) / 1000.0
        time.sleep(polling_interval)

def youtube_input_worker(youtube_queue, chat_history, chunk_queue, llm_lock):
    """
    Worker that checks the YouTube queue every 0.5 seconds.
    When a new chat message is found, it processes it with the LLM endpoint.
    """
    # These imports are placed here to avoid circular dependency issues.
    from utils.llm.llm_utils import stream_llm_chunks
    from utils.llm.chat_utils import save_chat_log
    from queue import Empty
    import pygame

    def flush_queue(q):
        try:
            while True:
                q.get_nowait()
        except Empty:
            pass

    while True:
        try:
            youtube_message = youtube_queue.get(timeout=0.5)
            if youtube_message:
                print("\nYouTube chat input detected:")
                print(youtube_message)
                with llm_lock:
                    flush_queue(chunk_queue)
                    if pygame.mixer.get_init():
                        pygame.mixer.stop()
                    full_response = stream_llm_chunks(youtube_message, chat_history, chunk_queue)
                    chat_history.append({"input": youtube_message, "response": full_response})
                    save_chat_log(chat_history)
        except Empty:
            continue

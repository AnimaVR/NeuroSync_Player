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
    Pauses polling if there are already items in the queue to reduce load.
    Enforces a minimum polling interval of 1.5 seconds.
    """
    youtube = build('youtube', 'v3', developerKey=api_key)
    next_page_token = None
    MIN_POLLING_INTERVAL = 1.5  # seconds

    while True:
        # Check if the queue already has messages waiting.
        # If so, delay polling to avoid extra API calls.
        if not message_queue.empty():
            time.sleep(MIN_POLLING_INTERVAL)
            continue

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

        # Enqueue each new message
        if 'items' in response:
            for item in response['items']:
                snippet = item.get('snippet', {})
                author = item.get('authorDetails', {})
                timestamp = snippet.get('publishedAt', '')
                message_text = snippet.get('displayMessage', '')
                formatted = f"[{timestamp}] {author.get('displayName', 'Unknown')}: {message_text}"
                message_queue.put(formatted)

        next_page_token = response.get('nextPageToken')
        # Respect the polling interval from the API, but ensure a minimum interval
        polling_interval = response.get('pollingIntervalMillis', MIN_POLLING_INTERVAL * 1000) / 1000.0
        time.sleep(max(polling_interval, MIN_POLLING_INTERVAL))

def youtube_input_worker(youtube_queue, chat_history, chunk_queue, llm_lock, config):  # <-- Added 'config'
    """
    Worker that checks the YouTube queue every 0.5 seconds.
    When new chat messages are detected, it batches them into a single input
    for the AI to process at once. New messages are simply added to the processing queue.
    """
    from utils.llm.llm_utils import stream_llm_chunks
    from utils.llm.chat_utils import save_chat_log
    from queue import Empty
    import pygame

    while True:
        try:
            # Wait for at least one message (blocking for up to 0.5 seconds)
            first_message = youtube_queue.get(timeout=0.5)
            batch_messages = [first_message]

            # Drain any additional messages in the queue without waiting.
            while True:
                try:
                    next_message = youtube_queue.get_nowait()
                    batch_messages.append(next_message)
                except Empty:
                    break

            # Combine all messages into a single input string.
            combined_message = "\n".join(batch_messages)
            print("\nYouTube chat batch input detected:")
            print(combined_message)

            with llm_lock:
                # Instead of flushing the chunk_queue, we let new messages add to it.
                if pygame.mixer.get_init():
                    pygame.mixer.stop()
                # Process the combined message through the AI.
                # Updated call: passing the 'config' parameter.
                full_response = stream_llm_chunks(combined_message, chat_history, chunk_queue, config=config)
                # Append the combined input and its response to the chat history.
                chat_history.append({"input": combined_message, "response": full_response})
                save_chat_log(chat_history)
        except Empty:
            continue


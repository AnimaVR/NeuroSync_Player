# utils/llm/turn_processing.py

import time
import pygame
from datetime import datetime, timezone
from queue import Empty

from utils.llm.llm_utils import stream_llm_chunks

from utils.llm.chat_utils import (
    save_full_chat_history,
    build_rolling_history,
    save_rolling_history,
    save_full_chat_history_ai,
    build_rolling_history_ai,
    save_rolling_history_ai,
)
from utils.vector_db.vector_db_utils import update_system_message_with_context, add_exchange_to_vector_db


def flush_queue(q):
    """
    Flush all items in the given queue.
    """
    try:
        while True:
            q.get_nowait()
    except Empty:
        pass


def wait_until_idle(chunk_queue, audio_queue, check_interval=0.05):
    """
    Wait until:
      - Both the TTS chunk queue and the audio queue are empty, AND
      - pygame is not currently playing any audio.
    """
    while (
        not chunk_queue.empty()
        or not audio_queue.empty()
        or (pygame.mixer.get_init() and pygame.mixer.get_busy())
    ):
        time.sleep(check_interval)


def process_turn(
    user_input,
    chat_history,
    full_history,
    llm_config,
    chunk_queue,
    audio_queue,
    vector_db,
    base_system_message,
    flush=True,
    top_n=4,
    ai_id=None,
):
    """
    Process a conversation turn by:
      - Updating the LLM config’s system message (using context from vector DB if enabled).
      - Flushing the queues or waiting until the system is idle.
      - Streaming the LLM response and updating the conversation history.
      - Saving the updated conversation history (using AI‑specific functions if ai_id is provided).

    Args:
      user_input (str): The user’s message.
      chat_history (list): The rolling chat history.
      full_history (list): The full conversation history.
      llm_config (dict): The LLM configuration dictionary.
      chunk_queue (Queue): The queue used for sending TTS chunks.
      audio_queue (Queue): The audio queue.
      vector_db: The vector database instance.
      base_system_message (str): The base system message to use for this turn.
      flush (bool): If True, flush the queues; if False, wait until idle.
      top_n (int): The number of related context items to pull from the vector DB (if enabled).
      ai_id (optional): If provided, use AI‑specific conversation logging.

    Returns:
      list: The updated chat history.
    """
    if llm_config.get("USE_VECTOR_DB"):
        llm_config["system_message"] = update_system_message_with_context(
            user_input, base_system_message, vector_db, top_n=top_n
        )
    else:
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S GMT")
        llm_config["system_message"] = (
            base_system_message + "\nThe current time and date is: " + current_time
        )

    if flush:
        flush_queue(chunk_queue)
        flush_queue(audio_queue)
    else:
        wait_until_idle(chunk_queue, audio_queue)

    if pygame.mixer.get_init():
        pygame.mixer.stop()

    full_response = stream_llm_chunks(user_input, chat_history, chunk_queue, config=llm_config)

    new_turn = {"input": user_input, "response": full_response}
    chat_history.append(new_turn)
    full_history.append(new_turn)

    if ai_id is None:
        save_full_chat_history(full_history)
        updated_chat_history = build_rolling_history(full_history)
        save_rolling_history(updated_chat_history)
    else:
        save_full_chat_history_ai(ai_id, full_history)
        updated_chat_history = build_rolling_history_ai(ai_id, full_history)
        save_rolling_history_ai(ai_id, updated_chat_history)

    if llm_config.get("USE_VECTOR_DB"):
        add_exchange_to_vector_db(user_input, full_response, vector_db)

    return updated_chat_history

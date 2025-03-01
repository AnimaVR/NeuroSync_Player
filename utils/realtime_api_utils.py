# realtime_api_utils.py

import asyncio
import base64
from openai import AsyncOpenAI

# -------------------------------
# Helper Functions and Utilities
# -------------------------------

def compute_min_buffer_size(realtime_config):
    """
    Compute the minimum buffer size based on realtime configuration parameters.
    """
    # Retrieve configuration values with defaults
    sample_rate = realtime_config.get("sample_rate", 22050)
    channels = realtime_config.get("channels", 1)
    sample_width = realtime_config.get("sample_width", 2)
    min_buffer_duration = realtime_config.get("min_buffer_duration", 5)
    # Compute and return the minimum buffer size needed
    return int(min_buffer_duration * sample_rate * channels * sample_width)


# -------------------------------
# Connection and Session Methods
# -------------------------------

async def initialize_connection(connection, realtime_config):
    """
    Initialize the realtime connection by updating the session and computing min_buffer_size.
    """
    # Update session with required modalities
    await connection.session.update(session={'modalities': ['audio', 'text']})
    print("Persistent realtime connection established. (See)")
    # Compute and return the minimum buffer size for audio processing
    return compute_min_buffer_size(realtime_config)

# -------------------------------
# Audio Input and Message Handling
# -------------------------------

async def get_audio_from_queue(audio_input_queue):
    """
    Retrieve audio bytes from the blocking audio input queue asynchronously.
    """
    loop = asyncio.get_event_loop()
    # Use run_in_executor to handle the blocking get() call
    return await loop.run_in_executor(None, audio_input_queue.get)

async def send_audio_message(connection, audio_bytes):
    """
    Encode and send the audio message to the realtime API.
    """
    # Encode the audio in base64
    encoded_audio = base64.b64encode(audio_bytes).decode('utf-8')
    # Create a conversation item with the encoded audio
    await connection.conversation.item.create(
        item={
            "type": "message",
            "role": "user",
            "content": [{"type": "input_audio", "audio": encoded_audio}],
        }
    )
    # Initiate the response creation on the connection
    await connection.response.create()
    print("Sent audio input to realtime API.")

# -------------------------------
# Event Processing Methods
# -------------------------------

async def process_events(connection, conversion_queue, min_buffer_size):
    """
    Process events received from the realtime API connection.
    Handles both audio and text events.
    """
    audio_buffer = bytearray()
    while True:
        try:
            event = await connection.recv()
        except Exception as e:
            print("Error while receiving event:", e)
            break

        if event is None:
            print("No event received, breaking out of inner loop.")
            break

        # Handle error events
        if event.type == 'error':
            print("Realtime API error:", event.error.message)
            continue

        # Process audio delta events
        if event.type == 'response.audio.delta':
            chunk = event.delta
            if isinstance(chunk, str):
                try:
                    chunk = base64.b64decode(chunk)
                except Exception as e:
                    print("Failed to decode audio chunk:", e)
                    continue
            audio_buffer.extend(chunk)
            # If the audio buffer is large enough, send it to the conversion queue
            if len(audio_buffer) >= min_buffer_size:
                current_audio = bytes(audio_buffer)
                audio_buffer.clear()
                conversion_queue.put(current_audio)

        # Finalize audio processing when done
        elif event.type == 'response.audio.done':
            if audio_buffer:
                current_audio = bytes(audio_buffer)
                audio_buffer.clear()
                conversion_queue.put(current_audio)
            break

        # Process text delta events
        elif event.type == 'response.text.delta':
            print(event.delta, end='', flush=True)

        # End of text response
        elif event.type == 'response.text.done':
            print()
    return

async def process_conversation_item(connection, audio_input_queue, conversion_queue, min_buffer_size):
    """
    Process a single conversation item:
      - Retrieve audio input.
      - Send the audio message.
      - Process the incoming events.
    Returns False if shutdown is requested, True otherwise.
    """
    audio_bytes = await get_audio_from_queue(audio_input_queue)
    if audio_bytes is None:
        print("Shutting down persistent realtime handler.")
        return False  # Signal to stop processing further items
    await send_audio_message(connection, audio_bytes)
    await process_events(connection, conversion_queue, min_buffer_size)
    print("Finished processing one conversation item.")
    return True

# -------------------------------
# Main Realtime Handler
# -------------------------------

async def persistent_realtime_handler(audio_input_queue, conversion_queue, realtime_config, api_key):
    """
    Main handler that establishes a persistent realtime connection and processes conversation items.
    It reconnects automatically upon errors.
    """
    client = AsyncOpenAI(api_key=api_key)
    while True:
        try:
            async with client.beta.realtime.connect(model="gpt-4o-mini-realtime-preview-2024-12-17") as connection:
                # Initialize connection and calculate the minimum buffer size for audio processing
                min_buffer_size = await initialize_connection(connection, realtime_config)
                # Continuously process conversation items
                while True:
                    should_continue = await process_conversation_item(connection, audio_input_queue, conversion_queue, min_buffer_size)
                    if not should_continue:
                        return
        except TimeoutError as te:
            print(
                "Connection timed out during handshake, retrying in 5 seconds...\n"
                "For some reason the first time we connect, this happens every time - don't worry about it, "
                "if you have an api key added it should start in a sec..... ",
                te
            )
            await asyncio.sleep(5)
        except Exception as e:
            print("Error in persistent realtime handler:", e)
            await asyncio.sleep(5)

def run_async_realtime(audio_input_queue, conversion_queue, realtime_config, api_key):
    """
    Entry point to run the realtime handler asynchronously.
    """
    asyncio.run(persistent_realtime_handler(audio_input_queue, conversion_queue, realtime_config, api_key))

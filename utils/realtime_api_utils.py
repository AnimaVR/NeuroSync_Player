# realtime_api_utils.py

import asyncio
import base64
from queue import Empty
from openai import AsyncOpenAI

from utils.neurosync_api_connect import send_audio_to_neurosync  
from utils.audio.convert_audio import bytes_to_wav


def run_async_realtime(audio_input_queue, conversion_queue, realtime_config, api_key):
    asyncio.run(persistent_realtime_handler(audio_input_queue, conversion_queue, realtime_config, api_key))

async def persistent_realtime_handler(audio_input_queue, conversion_queue, realtime_config, api_key):
    client = AsyncOpenAI(api_key=api_key)
    while True:
        try:
            async with client.beta.realtime.connect(model="gpt-4o-realtime-preview-2024-12-17") as connection:
                await connection.session.update(session={'modalities': ['audio', 'text']})
               
                print("Persistent realtime connection established. (See ;))")
                
                sample_rate = realtime_config.get("sample_rate", 22050)
                channels = realtime_config.get("channels", 1)
                sample_width = realtime_config.get("sample_width", 2)
                min_buffer_duration = realtime_config.get("min_buffer_duration", 5)
                min_buffer_size = int(min_buffer_duration * sample_rate * channels * sample_width)
                
                while True:
                    audio_bytes = await asyncio.get_event_loop().run_in_executor(None, audio_input_queue.get)
                    if audio_bytes is None:
                        print("Shutting down persistent realtime handler.")
                        return
                    encoded_audio = base64.b64encode(audio_bytes).decode('utf-8')
                    await connection.conversation.item.create(
                        item={
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_audio", "audio": encoded_audio}],
                        }
                    )
                    await connection.response.create()
                    print("Sent audio input to realtime API.")
                    
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
                        if event.type == 'error':
                            print("Realtime API error:", event.error.message)
                            continue
                        if event.type == 'response.audio.delta':
                            chunk = event.delta
                            if isinstance(chunk, str):
                                try:
                                    chunk = base64.b64decode(chunk)
                                except Exception as e:
                                    print("Failed to decode audio chunk:", e)
                                    continue
                            audio_buffer.extend(chunk)
                            if len(audio_buffer) >= min_buffer_size:
                                current_audio = bytes(audio_buffer)
                                audio_buffer.clear()
                                conversion_queue.put(current_audio)
                        elif event.type == 'response.audio.done':
                            if len(audio_buffer) > 0:
                                current_audio = bytes(audio_buffer)
                                audio_buffer.clear()
                                conversion_queue.put(current_audio)
                            break
                        elif event.type == 'response.text.delta':
                            print(event.delta, end='', flush=True)
                        elif event.type == 'response.text.done':
                            print()
                    print("Finished processing one conversation item.")
        except TimeoutError as te:
            print("Connection timed out during handshake, retrying in 5 seconds...\nFor some reason the first time we connect, this happens every time - don't worry about it, if you have an api key added it should start in a sec..... ", te)
            await asyncio.sleep(5)
        except Exception as e:
            print("Error in persistent realtime handler:", e)
            await asyncio.sleep(5)

def flush_queue(q):
    try:
        while True:
            q.get_nowait()
    except Empty:
        pass



def conversion_worker(conversion_queue, audio_queue, sample_rate, channels, sample_width):
    while True:
        audio_chunk = conversion_queue.get()
        if audio_chunk is None:  
            conversion_queue.task_done()
            break

        wav_audio = bytes_to_wav(audio_chunk, sample_rate, channels, sample_width)
        facial_data = send_audio_to_neurosync(wav_audio.getvalue())

        audio_queue.put((audio_chunk, facial_data))
        conversion_queue.task_done()
        

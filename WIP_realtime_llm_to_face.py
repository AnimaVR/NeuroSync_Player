# realtime_llm_to_face.py

import threading
from queue import Queue
import pygame
import keyboard
import time
from queue import Empty
from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

from utils.audio_workers import audio_face_queue_worker_realtime
from utils.audio.record_audio import record_audio_until_release
from utils.neurosync_api_connect import send_audio_to_neurosync  
from utils.audio.convert_audio import bytes_to_wav
from utils.realtime_api_utils import run_async_realtime


OPENAI_API_KEY = "YOUR_API_KEY"

# Global configuration for real-time processing
realtime_config = {
    "min_buffer_duration": 6, # this is how much time in bytes, not how much time to wait before response - lower = faster but worse skips, depends a lot on your network/hardware.
    "sample_rate": 22050, 
    "channels": 1, 
    "sample_width": 2
}

def flush_queue(q):
    """
    Utility function to flush (empty) a queue.
    """
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

def main():
    py_face = initialize_py_face()
    socket_connection = create_socket_connection()
    
    default_animation_thread = threading.Thread(target=default_animation_loop, args=(py_face,))
    default_animation_thread.start()
    
    audio_face_queue = Queue()
    conversion_queue = Queue()

    conversion_worker_thread = threading.Thread(
        target=conversion_worker,
        args=(conversion_queue, audio_face_queue, realtime_config["sample_rate"], realtime_config["channels"], realtime_config["sample_width"]),
        daemon=True
    )

    conversion_worker_thread.start()
    
    audio_worker_thread = threading.Thread(
        target=audio_face_queue_worker_realtime,
        args=(audio_face_queue, py_face, socket_connection, default_animation_thread)
    )
    audio_worker_thread.start()
    
    audio_input_queue = Queue()

    realtime_thread = threading.Thread(
        target=run_async_realtime,
        args=(audio_input_queue, conversion_queue, realtime_config, OPENAI_API_KEY),
        daemon=True
    )

    realtime_thread.start()
    
    try:
        while True:
            print("Wait for connection to the realtime API, then press Right Ctrl to record (or 'q' to quit): ")

            while True:
                if keyboard.is_pressed('q'):
                    break
                elif keyboard.is_pressed('right ctrl'):
                    start_record_time = time.time()  # Start timing from audio input
                    print(f"Recording started.")
                    
                    audio_input = record_audio_until_release()
                    end_record_time = time.time()
                    print(f"Recording ended. Duration: {end_record_time - start_record_time:.3f} seconds.")

                    break
            
            if keyboard.is_pressed('q'):
                break
                
            flush_queue(audio_face_queue)
            if pygame.mixer.get_init():
                pygame.mixer.stop()

            audio_input_queue.put(audio_input)
            print("Audio input sent to processing queue.")       
       
    finally:
        audio_input_queue.put(None)  
        realtime_thread.join()
        audio_face_queue.join()
        conversion_queue.put(None) 
        conversion_worker_thread.join()
        audio_face_queue.put(None)
        audio_worker_thread.join()
        stop_default_animation.set()
        default_animation_thread.join()
        pygame.quit()
        socket_connection.close()

if __name__ == "__main__":
    main()

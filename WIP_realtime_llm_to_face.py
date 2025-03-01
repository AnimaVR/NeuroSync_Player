import threading
from queue import Queue
import pygame
import keyboard
import time
from queue import Empty

from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

from utils.audio_face_workers import audio_face_queue_worker_realtime, conversion_worker
from utils.audio.record_audio import record_audio_until_release
from utils.llm.realtime_api_utils import run_async_realtime

OPENAI_API_KEY = ""  

realtime_config = {
    "min_buffer_duration": 6, 
    "sample_rate": 22050, 
    "channels": 1, 
    "sample_width": 2
}

def flush_queue(q):
    try:
        while True:
            q.get_nowait()
    except Empty:
        pass



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

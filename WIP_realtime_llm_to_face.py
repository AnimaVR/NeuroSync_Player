# realtime_llm_to_face.py

import threading
from queue import Queue
import pygame
import keyboard

from utils.realtime_api_utils import flush_queue, conversion_worker, run_async_realtime

from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation


from utils.audio_workers import audio_face_queue_worker_realtime
from utils.audio.record_audio import record_audio_until_release

OPENAI_API_KEY = "YOUR-OPENAI-API-KEY" 

def main():
    py_face = initialize_py_face()
    socket_connection = create_socket_connection()
    
    default_animation_thread = threading.Thread(target=default_animation_loop, args=(py_face,))
    default_animation_thread.start()
    
    audio_face_queue = Queue()
    conversion_queue = Queue()

    conversion_worker_thread = threading.Thread(target=conversion_worker,args=(conversion_queue,audio_face_queue,22050,1,2), daemon=True)

    conversion_worker_thread.start()
    audio_worker_thread = threading.Thread(target=audio_face_queue_worker_realtime,args=(audio_face_queue, py_face, socket_connection, default_animation_thread))
    audio_worker_thread.start()
    
    realtime_config = {"min_buffer_duration": 3, "sample_rate": 22050, "channels": 1, "sample_width": 2 }
    
    audio_input_queue = Queue()

    realtime_thread = threading.Thread(target=run_async_realtime,args=(audio_input_queue, conversion_queue, realtime_config, OPENAI_API_KEY), daemon=True)

    realtime_thread.start()
    
    try:
        while True:
            print("Wait for connection to the realtime API, once connected, press Right Ctrl to record your message (or 'q' to quit): ")
            while True:
                if keyboard.is_pressed('q'):
                    break
                elif keyboard.is_pressed('right ctrl'):
                    
                    audio_input = record_audio_until_release()
                    break
            
            if keyboard.is_pressed('q'):
                break
            flush_queue(audio_face_queue)
            if pygame.mixer.get_init():
                pygame.mixer.stop()

            audio_input_queue.put(audio_input)
    
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

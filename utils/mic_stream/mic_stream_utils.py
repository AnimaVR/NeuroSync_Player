import queue
import threading
import numpy as np
import time

from livelink.connect.faceblendshapes import FaceBlendShape
from utils.neurosync_api_connect import send_audio_to_audio2face
from utils.audio.save_audio import audio_to_bytes

FPS = 60
FRAMES_PER_CHUNK = FPS  # Number of frames to send to Unreal at a time (1 second at 60 FPS)

sending_complete_event = threading.Event()
sending_complete_event.set()  # Initially set to True

generated_data_queue = queue.Queue()
buffer_lock = threading.Lock()
sending_lock = threading.Lock()

def process_audio_chunk(audio_chunk, sr, py_face, socket_connection, executor):
    """Process a single audio chunk and generate facial data."""
    audio_bytes = audio_to_bytes(audio_chunk, sr)
    
    start_time = time.time()
    
    # Use the API to generate facial blendshapes from the audio bytes
    generated_facial_data = send_audio_to_audio2face(audio_bytes)
    
    end_time = time.time()
    
    if generated_facial_data is None:
        print("Failed to get facial data from the API.")
        return
    
    print(f"Generated facial data from {len(audio_chunk)} frames in {end_time - start_time:.2f} seconds")
    
    # Add the generated data to the queue
    generated_data_queue.put(generated_facial_data)
    print(f"Generated data queue size: {generated_data_queue.qsize()}")

    # If no sending process is running, start one
    if sending_complete_event.is_set():
        print("Starting sending process.")
        sending_complete_event.clear()
        executor.submit(send_facial_data, py_face, socket_connection)

def send_facial_data(py_face, socket_connection):
    """Send facial data to Unreal Engine in chunks."""
    print("send_facial_data: Entering function")
    
    while not generated_data_queue.empty():
        facial_data_chunk = []
        
        # Collect data until we have a full chunk or the queue is empty
        while len(facial_data_chunk) < FRAMES_PER_CHUNK and not generated_data_queue.empty():
            data = generated_data_queue.get()
            facial_data_chunk.extend(data)
            generated_data_queue.task_done()
        
        if len(facial_data_chunk) >= FRAMES_PER_CHUNK:
            facial_data_chunk = np.array(facial_data_chunk[:FRAMES_PER_CHUNK])
            print(f"Sending {len(facial_data_chunk)} frames to Unreal Engine.")
            play_facial_animation(facial_data_chunk, py_face, socket_connection)
    
    print("send_facial_data: Exiting function")
    sending_complete_event.set()

def play_facial_animation(facial_data, py_face, socket_connection):
    """Play the facial animation using the given facial data."""
    with sending_lock:
        def apply_blendshapes(frame_data):
            for i in range(51):
                py_face.set_blendshape(FaceBlendShape(i), float(frame_data[i]))
            socket_connection.sendall(py_face.encode())

        for blend_shape_data in facial_data:
            apply_blendshapes(blend_shape_data)
            time.sleep(1 / FPS)

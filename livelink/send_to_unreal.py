# send_to_unreal.py
import time
import numpy as np
from typing import List

from livelink.connect.livelink_init import create_socket_connection, FaceBlendShape

from livelink.animations.blending_anims import blend_in, blend_out  

def pre_encode_facial_data(facial_data: List[np.ndarray], py_face, fps: int = 60) -> List[bytes]:

    encoded_data = []

    blend_in_frames = int(0.05 * fps)
    blend_out_frames = int(0.3 * fps)

    blend_in(facial_data, fps, py_face, encoded_data, blend_in_frames)

    for frame_data in facial_data[blend_in_frames:-blend_out_frames]:
        for i in range(min(len(frame_data), 51)):  
            py_face.set_blendshape(FaceBlendShape(i), frame_data[i])
        encoded_data.append(py_face.encode())

    blend_out(facial_data, fps, py_face, encoded_data, blend_out_frames)

    return encoded_data

def send_pre_encoded_data_to_unreal(encoded_facial_data: List[bytes], start_event, fps: int, socket_connection=None):
    try:
        own_socket = False
        if socket_connection is None:
            socket_connection = create_socket_connection()
            own_socket = True

        start_event.wait()  # Wait until the event signals to start

        frame_duration = 1 / fps  # Time per frame in seconds
        start_time = time.time()  # Get the initial start time

        for frame_index, frame_data in enumerate(encoded_facial_data):
            current_time = time.time()
            elapsed_time = current_time - start_time

            expected_time = frame_index * frame_duration 
            if elapsed_time < expected_time:
                time.sleep(expected_time - elapsed_time) 
            elif elapsed_time > expected_time + frame_duration:
                continue

            socket_connection.sendall(frame_data)  # Send the frame

    except KeyboardInterrupt:
        pass
    finally:
        if own_socket:
            socket_connection.close()

# send_to_unreal.py

import time
import numpy as np
from typing import List
from threading import Thread
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
    """
    Creates a dedicated sender thread that sends frames at precisely calculated intervals.
    It uses a combination of sleep (for low CPU load) and a brief busy-wait for high accuracy.
    All frames are sent (even if behind schedule) to ensure synchronization with the audio.
    """
    def sender():
        # Create a socket if none is provided.
        own_socket = False
        if socket_connection is None:
            sock = create_socket_connection()
            own_socket = True
        else:
            sock = socket_connection

        # Wait for the start signal.
        start_event.wait()

        frame_duration = 1.0 / fps  # seconds per frame
        total_frames = len(encoded_facial_data)
        start_time = time.perf_counter()

        i = 0
        while i < total_frames:
            scheduled_time = start_time + i * frame_duration
            now = time.perf_counter()
            delta = scheduled_time - now

            if delta > 0:
                # Sleep most of the remaining time if it is sufficiently long.
                if delta > 0.005:  # if more than 5 ms remain
                    time.sleep(delta - 0.002)  # sleep leaving ~2ms remaining
                # Busy-wait for the final few milliseconds.
                while time.perf_counter() < scheduled_time:
                    pass

            try:
                # Use send() instead of sendall() for UDP datagrams.
                sent_bytes = sock.send(encoded_facial_data[i])
                if sent_bytes != len(encoded_facial_data[i]):
                    print(f"Warning: Incomplete send on frame {i}: sent {sent_bytes} of {len(encoded_facial_data[i])} bytes.")
            except Exception as e:
                print(f"Error sending frame {i}: {e}")
            i += 1

        if own_socket:
            sock.close()

    sender_thread = Thread(target=sender, name="FrameSenderThread")
    sender_thread.daemon = True
    sender_thread.start()
    return sender_thread

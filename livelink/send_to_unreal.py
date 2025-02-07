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
    This function creates a dedicated sender thread which sends frames at precisely
    calculated intervals. If the sender is too late for a frame (i.e. due to CPU stutter),
    it will skip that frame to try and catch up.
    
    The basic logic is:
      - Wait for the start signal.
      - Calculate the scheduled time for each frame.
      - Sleep until that time if possible.
      - If already too late (more than one frame duration behind), skip the frame.
      - Otherwise, send the frame.
    
    The sender thread is created and started inside this function.
    """
    def sender():
        # Create a socket if one wasn't provided.
        own_socket = False
        if socket_connection is None:
            sock = create_socket_connection()
            own_socket = True
        else:
            sock = socket_connection

        # Wait for the signal to start sending frames.
        start_event.wait()

        frame_duration = 1.0 / fps  # seconds per frame
        total_frames = len(encoded_facial_data)
        start_time = time.perf_counter()

        i = 0
        while i < total_frames:
            # Calculate the ideal send time for the current frame.
            scheduled_time = start_time + i * frame_duration
            now = time.perf_counter()

            # If we are early, sleep until it is time.
            if now < scheduled_time:
                time.sleep(scheduled_time - now)
                now = time.perf_counter()

            # If we're too late for this frame, skip it.
            # (Here the threshold is one full frame; adjust if you want a more or less aggressive skip.)
            if now - scheduled_time > frame_duration:
                # Optionally, log or count skipped frames here.
                i += 1
                continue

            try:
                sock.sendall(encoded_facial_data[i])
            except Exception as e:
                print(f"Error sending frame {i}: {e}")
            i += 1

        if own_socket:
            sock.close()

    # Create and start the sender thread.
    sender_thread = Thread(target=sender, name="FrameSenderThread")
    sender_thread.daemon = True  
    sender_thread.start()

    return sender_thread 

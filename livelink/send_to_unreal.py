# send_to_unreal.py
# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

import time
from typing import List

from livelink.connect.livelink_init import create_socket_connection, FaceBlendShape
from livelink.animations.default_animation import default_animation_data
from livelink.animations.blending_anims import blend_in, blend_out, DEFAULT_BLEND_DURATION 


def apply_blink_to_facial_data(facial_data: List, default_animation_data: List[List[float]]):
    """
    Updates each frame in facial_data in-place by setting the blink indices (EyeBlinkLeft, EyeBlinkRight)
    to the values from default_animation_data. This ensures that the blink values are present before any blending.
    """
    blink_indices = {FaceBlendShape.EyeBlinkLeft.value, FaceBlendShape.EyeBlinkRight.value}
    default_len = len(default_animation_data)
    for idx, frame in enumerate(facial_data):
        default_idx = idx % default_len
        for blink_idx in blink_indices:
            if blink_idx < len(frame):
                frame[blink_idx] = default_animation_data[default_idx][blink_idx]


def smooth_facial_data(facial_data: list) -> list:
    if len(facial_data) < 2:
        return facial_data.copy()  

    smoothed_data = [facial_data[0]]
    for i in range(1, len(facial_data)):
        previous_frame = facial_data[i - 1]
        current_frame = facial_data[i]
        averaged_frame = [(a + b) / 2 for a, b in zip(previous_frame, current_frame)]
        smoothed_data.append(averaged_frame)
    
    return smoothed_data

# smoothing shouldnt be needed, its just there if you scale too much and want to dial it back without losing scale.

def pre_encode_facial_data(facial_data: list, py_face, fps: int = 60, smooth: bool = False) -> list:
    apply_blink_to_facial_data(facial_data, default_animation_data)
    
    # If smoothing is enabled, apply smoothing to the facial data
    if smooth:
        facial_data = smooth_facial_data(facial_data)  

    encoded_data = []
    blend_in(facial_data, py_face, encoded_data, fps, default_animation_data)

    for frame_index, frame_data in enumerate(facial_data[int(DEFAULT_BLEND_DURATION * fps):-int(DEFAULT_BLEND_DURATION * fps)]):
        for i in range(min(len(frame_data), 51)):
            py_face.set_blendshape(FaceBlendShape(i), frame_data[i])
        encoded_data.append(py_face.encode())

    blend_out(facial_data, py_face, encoded_data, fps, default_animation_data)
    return encoded_data

def send_pre_encoded_data_to_unreal(encoded_facial_data: List[bytes], start_event, fps: int, socket_connection=None):
    try:
        own_socket = False
        if socket_connection is None:
            socket_connection = create_socket_connection()
            own_socket = True

        start_event.wait()  
        frame_duration = 1 / fps  
        start_time = time.time()  

        for frame_index, frame_data in enumerate(encoded_facial_data):
            current_time = time.time()
            elapsed_time = current_time - start_time
            expected_time = frame_index * frame_duration 
            if elapsed_time < expected_time:
                time.sleep(expected_time - elapsed_time)
            elif elapsed_time > expected_time + frame_duration:
                continue

            socket_connection.sendall(frame_data)  

    except KeyboardInterrupt:
        pass
    finally:
        if own_socket:
            socket_connection.close()

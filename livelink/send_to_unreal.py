# send_to_unreal.py

import time
import numpy as np
from typing import List

from livelink.connect.livelink_init import create_socket_connection, FaceBlendShape
from livelink.animations.default_animation import default_animation_data
from livelink.animations.blending_anims import blend_in, blend_out  


def pre_encode_facial_data_without_blend(facial_data: List[np.ndarray], py_face, fps: int = 60) -> List[bytes]:
    encoded_data = []

    blend_in_frames = int(0.1 * fps)
    blend_out_frames = int(0.3 * fps)

    eye_replacement_indices = [
        FaceBlendShape.EyeBlinkLeft.value, FaceBlendShape.EyeBlinkRight.value #, FaceBlendShape.EyeWideLeft.value, FaceBlendShape.EyeWideRight.value, FaceBlendShape.EyeSquintLeft.value, FaceBlendShape.EyeSquintRight.value
    ]
    for frame_index, frame_data in enumerate(facial_data[blend_in_frames:-blend_out_frames]):
        default_loop_index = frame_index % len(default_animation_data)

        for i in range(min(len(frame_data), 51)):  
            if i in eye_replacement_indices:
                py_face.set_blendshape(FaceBlendShape(i), default_animation_data[default_loop_index][i])
            else:
                py_face.set_blendshape(FaceBlendShape(i), frame_data[i])
        
        encoded_data.append(py_face.encode())

    return encoded_data


def pre_encode_facial_data_blend_out(facial_data: List[np.ndarray], py_face, fps: int = 60) -> List[bytes]:
    encoded_data = []

    blend_in_frames = int(0.1 * fps)
    blend_out_frames = int(0.3 * fps)
    
    # Use a set for fast membership testing
    eye_replacement_set = {FaceBlendShape.EyeBlinkLeft.value, FaceBlendShape.EyeBlinkRight.value}
    # Cache length of default_animation_data to avoid repeated global lookups
    default_animation_data_len = len(default_animation_data)
    # Cache the py_face.set_blendshape method to reduce attribute lookups
    set_blend = py_face.set_blendshape

    for frame_index, frame_data in enumerate(facial_data[blend_in_frames:-blend_out_frames]):
        default_loop_index = frame_index % default_animation_data_len
        default_frame = default_animation_data[default_loop_index]
        # Iterate over the first 51 blendshapes using enumerate on a slice
        for i, value in enumerate(frame_data[:51]):
            if i in eye_replacement_set:
                set_blend(FaceBlendShape(i), default_frame[i])
            else:
                set_blend(FaceBlendShape(i), value)
        
        encoded_data.append(py_face.encode())
    
    blend_out(facial_data, fps, py_face, encoded_data, blend_out_frames, default_animation_data)
    return encoded_data


def pre_encode_facial_data_blend_in(facial_data: List[np.ndarray], py_face, fps: int = 60) -> List[bytes]:
    encoded_data = []

    blend_in_frames = int(0.1 * fps)
    blend_out_frames = int(0.3 * fps)
    
    eye_replacement_set = {FaceBlendShape.EyeBlinkLeft.value, FaceBlendShape.EyeBlinkRight.value}
    default_animation_data_len = len(default_animation_data)
    set_blend = py_face.set_blendshape

    blend_in(facial_data, fps, py_face, encoded_data, blend_in_frames, default_animation_data)

    for frame_index, frame_data in enumerate(facial_data[blend_in_frames:-blend_out_frames]):
        default_loop_index = frame_index % default_animation_data_len
        default_frame = default_animation_data[default_loop_index]
        for i, value in enumerate(frame_data[:51]):
            if i in eye_replacement_set:
                set_blend(FaceBlendShape(i), default_frame[i])
            else:
                set_blend(FaceBlendShape(i), value)
        
        encoded_data.append(py_face.encode())

    return encoded_data

def pre_encode_facial_data(facial_data: List[np.ndarray], py_face, fps: int = 60) -> List[bytes]:
    encoded_data = []

    blend_in_frames = int(0.1 * fps)
    blend_out_frames = int(0.3 * fps)
    eye_replacement_indices = [
        FaceBlendShape.EyeBlinkLeft.value, FaceBlendShape.EyeBlinkRight.value #, FaceBlendShape.EyeWideLeft.value, FaceBlendShape.EyeWideRight.value, FaceBlendShape.EyeSquintLeft.value, FaceBlendShape.EyeSquintRight.value
    ]

    blend_in(facial_data, fps, py_face, encoded_data, blend_in_frames, default_animation_data)

    for frame_index, frame_data in enumerate(facial_data[blend_in_frames:-blend_out_frames]):
        default_loop_index = frame_index % len(default_animation_data)

        for i in range(min(len(frame_data), 51)):
            if i in eye_replacement_indices:
                py_face.set_blendshape(FaceBlendShape(i), default_animation_data[default_loop_index][i])
            else:
                py_face.set_blendshape(FaceBlendShape(i), frame_data[i])
        
        encoded_data.append(py_face.encode())
    
    blend_out(facial_data, fps, py_face, encoded_data, blend_out_frames, default_animation_data)

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

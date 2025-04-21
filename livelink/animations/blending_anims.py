# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

# blending_anims.py


import time
import numpy as np

from livelink.animations.default_animation import FaceBlendShape


def play_full_animation(facial_data, fps, py_face, socket_connection, blend_in_frames, blend_out_frames):
    for blend_shape_data in facial_data[blend_in_frames:-blend_out_frames]:
        apply_blendshapes(blend_shape_data, 1.0, py_face)
        socket_connection.sendall(py_face.encode())
        time.sleep(1 / fps)

def apply_blendshapes(frame_data: np.ndarray, weight: float, py_face, default_animation_data):
    for i in range(51):  # Apply the first 51 blendshapes (no neck at the moment)
        default_value = default_animation_data[0][i]
        facial_value = frame_data[i]
        blended_value = (1 - weight) * default_value + weight * facial_value
        py_face.set_blendshape(FaceBlendShape(i), float(blended_value))

def blend_in(facial_data, fps, py_face, encoded_data, blend_in_frames, default_animation_data):
    for frame_index in range(blend_in_frames):
        weight = frame_index / blend_in_frames
        apply_blendshapes(facial_data[frame_index], weight, py_face, default_animation_data)
        encoded_data.append(py_face.encode())

def blend_out(facial_data, fps, py_face, encoded_data, blend_out_frames, default_animation_data):
    for frame_index in range(blend_out_frames):
        weight = frame_index / blend_out_frames
        reverse_index = len(facial_data) - blend_out_frames + frame_index
        apply_blendshapes(facial_data[reverse_index], 1.0 - weight, py_face, default_animation_data)
        encoded_data.append(py_face.encode())

def blend_animation_start_end(data, blend_frames=16):
    last_frames = data[-blend_frames:]
    first_frames = data[:blend_frames]
    blended_frames = np.zeros_like(last_frames)
    for i in range(blend_frames):
        alpha = i / blend_frames  # Linear blending factor
        blended_frames[i] = (1 - alpha) * last_frames[i] + alpha * first_frames[i]

    blended_data = np.vstack([data[:-blend_frames], blended_frames])
    return blended_data

def blend_animation_data_to_loop_by_dimension(animation_data, dimensions, blend_frame_count=16):

    num_frames = len(animation_data)

    blend_frame_count = min(blend_frame_count, num_frames)
    
    for dim in dimensions:
        for i in range(blend_frame_count):
            blend_alpha = i / blend_frame_count
            start_value = animation_data[i][dim]  
            end_index = num_frames - blend_frame_count + i
            end_value = animation_data[end_index][dim]
            blended_value = (1 - blend_alpha) * end_value + blend_alpha * start_value
            animation_data[end_index][dim] = blended_value
    return animation_data


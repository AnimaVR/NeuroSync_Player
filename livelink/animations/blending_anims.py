# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

# blending_anims.py

import time
import numpy as np

from livelink.animations.default_animation import default_animation_data, FaceBlendShape


def play_full_animation(facial_data, fps, py_face, socket_connection, blend_in_frames, blend_out_frames):
    for blend_shape_data in facial_data[blend_in_frames:-blend_out_frames]:
        apply_blendshapes(blend_shape_data, 1.0, py_face)
        socket_connection.sendall(py_face.encode())
        time.sleep(1 / fps)

def apply_blendshapes(frame_data: np.ndarray, weight: float, py_face):
    for i in range(51):  # Apply the first 51 blendshapes (no neck at the moment)
        default_value = default_animation_data[0][i]
        facial_value = frame_data[i]
        blended_value = (1 - weight) * default_value + weight * facial_value
        py_face.set_blendshape(FaceBlendShape(i), float(blended_value))
'''
    # Handle new emotion dimensions (61 to 67)
    additional_values = frame_data[61:68]
    values_str = " ".join([f"{i+61}: {value:.2f}" for i, value in enumerate(additional_values)])
    print(f"Frame Values: {values_str}")

    # Determine the emotion with the highest value
    max_emotion_index = np.argmax(additional_values)
    emotions = ["Angry", "Disgusted", "Fearful", "Happy", "Neutral", "Sad", "Surprised"]
    print(f"Highest emotion: {emotions[max_emotion_index]} with value: {additional_values[max_emotion_index]:.2f}")'''

def blend_in(facial_data, fps, py_face, encoded_data, blend_in_frames):
    for frame_index in range(blend_in_frames):
        weight = frame_index / blend_in_frames
        apply_blendshapes(facial_data[frame_index], weight, py_face)
        encoded_data.append(py_face.encode())
        time.sleep(1 / fps)

def blend_out(facial_data, fps, py_face, encoded_data, blend_out_frames):
    for frame_index in range(blend_out_frames):
        weight = frame_index / blend_out_frames
        reverse_index = len(facial_data) - blend_out_frames + frame_index
        apply_blendshapes(facial_data[reverse_index], 1.0 - weight, py_face)
        encoded_data.append(py_face.encode())
        time.sleep(1 / fps)


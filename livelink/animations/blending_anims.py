# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

# blending_anims.py

import time
import numpy as np
from typing import List, Set

from livelink.animations.default_animation import FaceBlendShape
default_animation_state = { 'current_index': 0 }

# These indices will get fast blend durations
FAST_BLENDSHAPES = {
    FaceBlendShape.JawOpen.value,
    FaceBlendShape.MouthClose.value
}
def generate_blend_frames(
    facial_data: List[np.ndarray],
    total_frames: int,
    default_animation_data: List[np.ndarray],
    fps: int,
    only_indices: Set[int],
    mode: str = 'in',
    active_duration_sec: float = None,
    default_start_index: int = None  # CHANGED: accept start index override
) -> List[np.ndarray]:
    """
    Generate a list of blended frames for given indices only.
    active_duration_sec limits actual blending duration; the rest is pass-through.
    If default_start_index is not provided, uses the current playing index from state (for blend-in) or 0 (for blend-out).
    """
    blended = []

    # determine number of active frames for blending
    if active_duration_sec is None:
        active_frames = total_frames
    else:
        active_frames = int(active_duration_sec * fps)

    # determine starting index for default animation
    if default_start_index is None:
        if mode == 'in':
            default_start_index = default_animation_state['current_index']
        else:
            default_start_index = 0   # CHANGED: restart default animation for blend-out

    for frame_index in range(total_frames):
        # compute blending weight
        if frame_index < active_frames:
            weight = (frame_index / active_frames) if mode == 'in' else 1.0 - (frame_index / active_frames)
        else:
            weight = 1.0 if mode == 'in' else 0.0

        # determine target frame_data for blending
        if mode == 'in':
            frame_data = facial_data[frame_index]
        else:
            frame_data = facial_data[-total_frames + frame_index]

        # compute correct base index, wrapping if needed
        idx = (default_start_index + frame_index) % len(default_animation_data)
        if mode == 'in':
            base = np.array(default_animation_data[idx][:51])
        else:
            base = np.copy(frame_data)

        blended_frame = np.copy(base)
        # perform per-index blending
        for i in only_indices:
            default_val = default_animation_data[idx][i]
            target_val = frame_data[i]
            blended_val = (1 - weight) * default_val + weight * target_val
            blended_frame[i] = blended_val

        blended.append(blended_frame)

    return blended

def combine_frame_streams(base_frames: List[np.ndarray], overlay_frames: List[np.ndarray], override_indices: set) -> List[np.ndarray]:
    """
    Merges two frame lists by applying `overlay_frames` values only at `override_indices`.
    """
    combined = []
    for base, overlay in zip(base_frames, overlay_frames):
        combined_frame = np.copy(base)
        for i in override_indices:
            combined_frame[i] = overlay[i]
        combined.append(combined_frame)
    return combined

def blend_in(facial_data, py_face, encoded_data, fps, default_animation_data):
    total_blend_frames = int(DEFAULT_BLEND_DURATION * fps)

    for frame_index in range(total_blend_frames):
        # Progress through total blend window (0 to 1)
        global_weight = frame_index / total_blend_frames
        apply_blendshapes(facial_data[frame_index], global_weight, py_face, default_animation_data, fps)
        encoded_data.append(py_face.encode())


def blend_out(facial_data, py_face, encoded_data, fps, default_animation_data):
    total_blend_frames = int(DEFAULT_BLEND_DURATION * fps)

    for frame_index in range(total_blend_frames):
        global_weight = frame_index / total_blend_frames
        reverse_index = len(facial_data) - total_blend_frames + frame_index
        apply_blendshapes(facial_data[reverse_index], 1.0 - global_weight, py_face, default_animation_data, fps)
        encoded_data.append(py_face.encode())


def apply_blendshapes(frame_data, global_weight: float, py_face, default_animation_data, fps: int):
    for i in range(51):  # Only the first 51 blendshapes
        shape = FaceBlendShape(i)
        shape_duration = get_blend_duration(i)
        shape_weight = min(global_weight / (shape_duration / DEFAULT_BLEND_DURATION), 1.0)

        default_val = default_animation_data[0][i]
        facial_val = frame_data[i]
        blended_val = (1 - shape_weight) * default_val + shape_weight * facial_val

        py_face.set_blendshape(shape, float(blended_val))

def play_full_animation(facial_data, fps, py_face, socket_connection, blend_in_frames, blend_out_frames):
    for blend_shape_data in facial_data[blend_in_frames:-blend_out_frames]:
        apply_blendshapes(blend_shape_data, 1.0, py_face)
        socket_connection.sendall(py_face.encode())
        time.sleep(1 / fps)

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


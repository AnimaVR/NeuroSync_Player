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
    default_start_index: int = None          # accepts override for idle-loop offset
) -> List[np.ndarray]:
    """
    Generate a list of blended frames.
    * For 'in' we fade from the idle pose into the recorded facial_data.
    * For 'out' we fade back from facial_data into the idle pose,
      **always starting at frame 0 of the idle animation** (unless
      default_start_index is explicitly overridden).

    Parameters
    ----------
    ...
    default_start_index : int
        Starting frame of the default animation to blend toward/away from.
        If None:
           - 'in'  → current live frame
           - 'out' → 0  (so the first idle frame is the blend target)  # <<< CHANGED
    """
    blended = []

    # ---------------- active blend duration ----------------
    active_frames = int(active_duration_sec * fps) if active_duration_sec else total_frames

    # ---------------- default-animation start index ----------------
    if default_start_index is None:
        default_start_index = (
            default_animation_state['current_index'] if mode == 'in' else 0  # <<< CHANGED
        )

    # ---------------- frame-by-frame blend ----------------
    for frame_index in range(total_frames):
        # weight ramps 0→1 for 'in', 1→0 for 'out'
        if frame_index < active_frames:
            weight = (frame_index / active_frames) if mode == 'in' else 1.0 - (frame_index / active_frames)
        else:
            weight = 1.0 if mode == 'in' else 0.0

        # target facial frame
        frame_data = (
            facial_data[frame_index] if mode == 'in'
            else facial_data[-total_frames + frame_index]
        )

        # idle-loop frame (wraps around)
        idx = (default_start_index + frame_index) % len(default_animation_data)

        # -------- base pose --------
        # Always start from the idle animation, even for 'out'.            # <<< CHANGED
        base = np.array(default_animation_data[idx][:51])

        # -------- blend only selected indices --------
        blended_frame = np.copy(base)
        for i in only_indices:
            default_val = default_animation_data[idx][i]
            target_val  = frame_data[i]
            blended_frame[i] = (1 - weight) * default_val + weight * target_val

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






def apply_blendshapes(frame_data: np.ndarray, weight: float, py_face, default_animation_data):
    for i in range(51):  # Apply the first 51 blendshapes (no neck at the moment)
        default_value = default_animation_data[0][i]
        facial_value = frame_data[i]
        blended_value = (1 - weight) * default_value + weight * facial_value
        py_face.set_blendshape(FaceBlendShape(i), float(blended_value))


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


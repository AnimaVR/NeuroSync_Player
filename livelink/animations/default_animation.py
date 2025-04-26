# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

import time
import socket
import pandas as pd
from threading import Event

from livelink.connect.livelink_init import FaceBlendShape, UDP_IP, UDP_PORT
from livelink.animations.blending_anims import blend_animation_start_end
from livelink.animations.blending_anims import default_animation_state, blend_animation_start_end

def load_animation(csv_path):
    data = pd.read_csv(csv_path)

    data = data.drop(columns=['Timecode', 'BlendshapeCount'])
    # zero'ing eyes so they match the generation position, do some eye control from Unreal or manually.
    cols_to_zero = [1, 2, 3, 4, 8, 9, 10, 11]
    cols_to_zero = [i for i in cols_to_zero if i < data.shape[1]] 
    data.iloc[:, cols_to_zero] = 0.0

    return data.values
# ==================== DEFAULT ANIMATION SETUP ====================

# Path to the default animation CSV file
ground_truth_path = r"livelink/animations/default_anim/default.csv"

# Load the default animation data
default_animation_data = load_animation(ground_truth_path)

# Create the blended default animation data
default_animation_data = blend_animation_start_end(default_animation_data, blend_frames=16)

# Event to signal stopping of the default animation loop
stop_default_animation = Event()

def default_animation_loop(py_face):
    """
    Loops through the default animation and updates global index state.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect((UDP_IP, UDP_PORT))
        while not stop_default_animation.is_set():
            for idx, frame in enumerate(default_animation_data):
                if stop_default_animation.is_set():
                    break
                # update shared state
                default_animation_state['current_index'] = idx

                for i, value in enumerate(frame):
                    py_face.set_blendshape(FaceBlendShape(i), float(value))
                try:
                    s.sendall(py_face.encode())
                except Exception as e:
                    print(f"Error in default animation sending: {e}")

                # maintain 60fps
                total_sleep = 1 / 60
                sleep_interval = 0.005
                while total_sleep > 0 and not stop_default_animation.is_set():
                    time.sleep(min(sleep_interval, total_sleep))
                    total_sleep -= sleep_interval




# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

import time
import socket
import numpy as np
import pandas as pd
from threading import Event

from livelink.connect.livelink_init import FaceBlendShape, UDP_IP, UDP_PORT

import os
from pathlib import Path

mod_path = Path(__file__).parent
ground_truth_path = os.path.join(mod_path, "default_anim/default.csv")

# ground_truth_path = r"livelink/animations/default_anim/default.csv"
columns_to_drop = [
    "TongueOut",
    "HeadYaw",
    "HeadPitch",
    "HeadRoll",
    "LeftEyeYaw",
    "LeftEyePitch",
    "LeftEyeRoll",
    "RightEyeYaw",
    "RightEyePitch",
    "RightEyeRoll",
]


def load_default_animation(csv_path):
    data = pd.read_csv(csv_path)
    data = data.drop(columns=["Timecode", "BlendshapeCount"] + columns_to_drop)
    return data.values


default_animation_data = load_default_animation(ground_truth_path)


def blend_animation(data, blend_frames=30):
    last_frames = data[-blend_frames:]
    first_frames = data[:blend_frames]

    blended_frames = np.zeros_like(last_frames)
    for i in range(blend_frames):
        alpha = i / blend_frames  # Linear blending factor
        blended_frames[i] = (1 - alpha) * last_frames[i] + alpha * first_frames[i]

    blended_data = np.vstack([data[:-blend_frames], blended_frames])
    return blended_data


blended_animation_data = blend_animation(default_animation_data, blend_frames=30)

stop_default_animation = Event()


def default_animation_loop(py_face):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect((UDP_IP, UDP_PORT))
        while not stop_default_animation.is_set():
            for frame in blended_animation_data:
                # Check before processing each frame
                if stop_default_animation.is_set():
                    break

                # Apply the frame blendshapes
                for i, value in enumerate(frame):
                    py_face.set_blendshape(FaceBlendShape(i), float(value))

                # Send the frame
                try:
                    s.sendall(py_face.encode())
                except Exception as e:
                    print(f"Error in default animation sending: {e}")

                # Instead of one long sleep, break it into short chunks
                total_sleep = 1 / 60
                sleep_interval = 0.005  # check every 5ms
                while total_sleep > 0 and not stop_default_animation.is_set():
                    time.sleep(min(sleep_interval, total_sleep))
                    total_sleep -= sleep_interval

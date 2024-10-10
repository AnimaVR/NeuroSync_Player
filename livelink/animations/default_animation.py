# This code is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
# For more details, visit: https://creativecommons.org/licenses/by-nc/4.0/

import time
import socket
import numpy as np
import pandas as pd
from threading import Event

from livelink.connect.livelink_init import FaceBlendShape, UDP_IP, UDP_PORT

ground_truth_path = r"livelink/animations/default_anim/default.csv"
columns_to_drop = [
    'TongueOut', 'HeadYaw', 'HeadPitch', 'HeadRoll',
    'LeftEyeYaw', 'LeftEyePitch', 'LeftEyeRoll',
    'RightEyeYaw', 'RightEyePitch', 'RightEyeRoll'
]

def load_default_animation(csv_path):
    data = pd.read_csv(csv_path)
    data = data.drop(columns=['Timecode', 'BlendshapeCount'] + columns_to_drop)
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
                if stop_default_animation.is_set():
                    break
                for i, value in enumerate(frame):
                    py_face.set_blendshape(FaceBlendShape(i), float(value))
                s.sendall(py_face.encode())
                time.sleep(1 / 60)

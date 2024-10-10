# This code is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
# For more details, visit: https://creativecommons.org/licenses/by-nc/4.0/
# pylivelinkface.py
# Hard work here done by https://github.com/JimWest/PyLiveLinkFace | 

from __future__ import annotations

from collections import deque
from timecode import Timecode
from statistics import mean
from typing import List

import datetime
import struct
import random
import uuid

from livelink.connect.faceblendshapes import FaceBlendShape

def scale_blendshapes(blendshapes: List[float], scale_factor: float, threshold: float = 0.0) -> List[float]:
    scaled_blendshapes = []
    for value in blendshapes:
        if value > threshold:
            scaled_value = value * scale_factor
            if scaled_value > 1.0:
                scaled_value = 1.0
            scaled_blendshapes.append(max(scaled_value, 0.0))  # Ensure non-negative
        else:
            scaled_blendshapes.append(max(value, 0.0))  # Ensure non-negative
    return scaled_blendshapes

class PyLiveLinkFace:
    def __init__(self, name: str = "Python_LiveLinkFace", uuid: str = str(uuid.uuid1()), fps=60, filter_size: int = 0) -> None:
        self.uuid = f"${uuid}" if not uuid.startswith("$") else uuid
        self.name = name
        self.fps = fps
        self._filter_size = filter_size
        self._version = 6
        
        self._scaling_factor = 1.0

        now = datetime.datetime.now()
        timcode = Timecode(self.fps, f'{now.hour}:{now.minute}:{now.second}:{now.microsecond * 0.001}')
        self._frames = timcode.frames
        self._sub_frame = 1056060032
        self._denominator = int(self.fps / 60)
        self._blend_shapes = [0.0] * 61
        self._old_blend_shapes = [deque([0.0], maxlen=filter_size) for _ in range(61)]

    def encode(self) -> bytes:
        version_packed = struct.pack('<I', self._version)
        uuid_packed = self.uuid.encode('utf-8')
        name_packed = self.name.encode('utf-8')
        name_length_packed = struct.pack('!i', len(self.name))
        now = datetime.datetime.now()
        timcode = Timecode(self.fps, f'{now.hour}:{now.minute}:{now.second}:{now.microsecond * 0.001}')
        frames_packed = struct.pack("!II", timcode.frames, self._sub_frame)
        frame_rate_packed = struct.pack("!II", self.fps, self._denominator)
    
        scaled_blend_shapes = scale_blendshapes(self._blend_shapes, self._scaling_factor)
    
        data_packed = struct.pack('!B61f', 61, *scaled_blend_shapes)
        return version_packed + uuid_packed + name_length_packed + name_packed + frames_packed + frame_rate_packed + data_packed

    def set_blendshape(self, index: FaceBlendShape, value: float, no_filter: bool = True) -> None:        
        if index in [FaceBlendShape.HeadYaw, FaceBlendShape.HeadPitch, FaceBlendShape.HeadRoll]:
            value = max(min(value, 0.00), -0.00) 
        
        if no_filter:
            self._blend_shapes[index.value] = value
        else:
            self._old_blend_shapes[index.value].append(value)
            self._blend_shapes[index.value] = mean(self._old_blend_shapes[index.value])

    def set_scaling_factor(self, scaling_factor: float) -> None:
        self._scaling_factor = scaling_factor   

    def random_blink_intervals(self, duration=60, min_interval=1.0, max_interval=5.0):
        intervals = []
        current_time = 0.0
        while current_time < duration:
            blink_interval = random.uniform(min_interval, max_interval)
            intervals.append(current_time + blink_interval)
            current_time += blink_interval
        return intervals

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

# Grouping the FaceBlendShape indices into sections
MOUTH_BLENDSHAPES = [
    FaceBlendShape.JawForward, FaceBlendShape.JawLeft, FaceBlendShape.JawRight, FaceBlendShape.JawOpen,
    FaceBlendShape.MouthClose, FaceBlendShape.MouthFunnel, FaceBlendShape.MouthPucker,
    FaceBlendShape.MouthLeft, FaceBlendShape.MouthRight, FaceBlendShape.MouthSmileLeft,
    FaceBlendShape.MouthSmileRight, FaceBlendShape.MouthFrownLeft, FaceBlendShape.MouthFrownRight,
    FaceBlendShape.MouthDimpleLeft, FaceBlendShape.MouthDimpleRight, FaceBlendShape.MouthStretchLeft,
    FaceBlendShape.MouthStretchRight, FaceBlendShape.MouthRollLower, FaceBlendShape.MouthRollUpper,
    FaceBlendShape.MouthShrugLower, FaceBlendShape.MouthShrugUpper, FaceBlendShape.MouthPressLeft,
    FaceBlendShape.MouthPressRight, FaceBlendShape.MouthLowerDownLeft, FaceBlendShape.MouthLowerDownRight,
    FaceBlendShape.MouthUpperUpLeft, FaceBlendShape.MouthUpperUpRight
]

EYE_BLENDSHAPES = [
    FaceBlendShape.EyeBlinkLeft, FaceBlendShape.EyeLookDownLeft, FaceBlendShape.EyeLookInLeft,
    FaceBlendShape.EyeLookOutLeft, FaceBlendShape.EyeLookUpLeft, FaceBlendShape.EyeSquintLeft,
    FaceBlendShape.EyeWideLeft, FaceBlendShape.EyeBlinkRight, FaceBlendShape.EyeLookDownRight,
    FaceBlendShape.EyeLookInRight, FaceBlendShape.EyeLookOutRight, FaceBlendShape.EyeLookUpRight,
    FaceBlendShape.EyeSquintRight, FaceBlendShape.EyeWideRight
]

EYEBROW_BLENDSHAPES = [
    FaceBlendShape.BrowDownLeft, FaceBlendShape.BrowDownRight, FaceBlendShape.BrowInnerUp,
    FaceBlendShape.BrowOuterUpLeft, FaceBlendShape.BrowOuterUpRight
]

def scale_blendshapes_by_section(blendshapes: List[float], mouth_scale: float, eye_scale: float, eyebrow_scale: float, threshold: float = 0.0) -> List[float]:
        scaled_blendshapes = []
        
        for i, value in enumerate(blendshapes):
            if value > threshold:
                if i in [bs.value for bs in MOUTH_BLENDSHAPES]:
                    scaled_value = value * mouth_scale
                elif i in [bs.value for bs in EYE_BLENDSHAPES]:
                    scaled_value = value * eye_scale
                elif i in [bs.value for bs in EYEBROW_BLENDSHAPES]:
                    scaled_value = value * eyebrow_scale
                else:
                    scaled_value = value  # No scaling for unclassified blendshapes
                
                # Ensure scaling stays within valid range (0.0 to 1.0)
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
        
        self._scaling_factor_mouth = 1.0
        self._scaling_factor_eyes = 0.4
        self._scaling_factor_eyebrows = 0.4

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
    
        # Apply different scaling factors for sections
        scaled_blend_shapes = scale_blendshapes_by_section(self._blend_shapes, self._scaling_factor_mouth, self._scaling_factor_eyes, self._scaling_factor_eyebrows)
    
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

    
    def set_scaling_factor_mouth(self, scaling_factor: float) -> None:
        self._scaling_factor_mouth = scaling_factor

    def set_scaling_factor_eyes(self, scaling_factor: float) -> None:
        self._scaling_factor_eyes = scaling_factor

    def set_scaling_factor_eyebrows(self, scaling_factor: float) -> None:
        self._scaling_factor_eyebrows = scaling_factor

    def random_blink_intervals(self, duration=60, min_interval=1.0, max_interval=5.0):
        intervals = []
        current_time = 0.0
        while current_time < duration:
            blink_interval = random.uniform(min_interval, max_interval)
            intervals.append(current_time + blink_interval)
            current_time += blink_interval
        return intervals

# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.
# pylivelinkface.py
# Hard work here done by https://github.com/JimWest/PyLiveLinkFace | 

from __future__ import annotations

from collections import deque
from timecode import Timecode
from statistics import mean
import datetime
import struct
import uuid

from livelink.connect.dimension_scalars import scale_blendshapes_by_section 
from livelink.connect.faceblendshapes import FaceBlendShape

class PyLiveLinkFace:
    def __init__(self, name: str = "face1", uuid: str = str(uuid.uuid1()), fps=60, filter_size: int = 0) -> None:
        self.uuid = f"${uuid}" if not uuid.startswith("$") else uuid
        self.name = name
        self.fps = fps
        self._filter_size = filter_size
        self._version = 6

        self._scaling_factor_mouth = 1.0
        self._scaling_factor_eyes = 1.0
        self._scaling_factor_eyebrows = 0.6
        self._scaling_factor_eyewide_left = 0.4
        self._scaling_factor_eyewide_right = 0.4
        self._scaling_factor_eyesquint_left = 1.0
        self._scaling_factor_eyesquint_right = 1.0

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
    
        scaled_blend_shapes = scale_blendshapes_by_section(
            self._blend_shapes, 
            self._scaling_factor_mouth, 
            self._scaling_factor_eyes, 
            self._scaling_factor_eyebrows, 
            eyewide_left_scale=self._scaling_factor_eyewide_left, 
            eyewide_right_scale=self._scaling_factor_eyewide_right, 
            eyesquint_left_scale=self._scaling_factor_eyesquint_left, 
            eyesquint_right_scale=self._scaling_factor_eyesquint_right
        )
    
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



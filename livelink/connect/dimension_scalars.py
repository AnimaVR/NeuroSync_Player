# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

from typing import List
from livelink.connect.faceblendshapes import FaceBlendShape

# Define blendshape groups for each facial feature.
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
    FaceBlendShape.EyeWideLeft,  # Specific: EyeWideLeft
    FaceBlendShape.EyeBlinkRight, FaceBlendShape.EyeLookDownRight,
    FaceBlendShape.EyeLookInRight, FaceBlendShape.EyeLookOutRight, FaceBlendShape.EyeLookUpRight,
    FaceBlendShape.EyeSquintRight,  # Specific: EyeSquintRight
    FaceBlendShape.EyeWideRight   # Specific: EyeWideRight
]

EYEBROW_BLENDSHAPES = [
    FaceBlendShape.BrowDownLeft, FaceBlendShape.BrowDownRight, FaceBlendShape.BrowInnerUp,
    FaceBlendShape.BrowOuterUpLeft, FaceBlendShape.BrowOuterUpRight
]

def scale_blendshapes_by_section(
    blendshapes: List[float],
    mouth_scale: float,
    eye_scale: float,
    eyebrow_scale: float,
    threshold: float = 0.0,
    eyewide_left_scale: float = 1.0,
    eyewide_right_scale: float = 1.0,
    eyesquint_left_scale: float = 1.0,
    eyesquint_right_scale: float = 1.0
) -> List[float]:
    """
    Scale blendshapes based on facial regions.
    """
    scaled_blendshapes = []
    
    for i, value in enumerate(blendshapes):
        if value > threshold:
            if i in [bs.value for bs in MOUTH_BLENDSHAPES]:
                scaled_value = value * mouth_scale
            elif i in [bs.value for bs in EYE_BLENDSHAPES]:
                if i == FaceBlendShape.EyeWideLeft.value:
                    scaled_value = value * eyewide_left_scale
                elif i == FaceBlendShape.EyeWideRight.value:
                    scaled_value = value * eyewide_right_scale
                elif i == FaceBlendShape.EyeSquintLeft.value:
                    scaled_value = value * eyesquint_left_scale
                elif i == FaceBlendShape.EyeSquintRight.value:
                    scaled_value = value * eyesquint_right_scale
                else:
                    scaled_value = value * eye_scale  
            elif i in [bs.value for bs in EYEBROW_BLENDSHAPES]:
                scaled_value = value * eyebrow_scale
            else:
                scaled_value = value
            
            if scaled_value > 1.0:
                scaled_value = 1.0
            scaled_blendshapes.append(max(scaled_value, 0.0))
        else:
            scaled_blendshapes.append(max(value, 0.0))
    
    return scaled_blendshapes

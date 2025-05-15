# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

from livelink.connect.faceblendshapes import FaceBlendShape
import numpy as np

def determine_highest_emotion(facial_data, perform_calculation=True):
    if not perform_calculation or facial_data.shape[1] != 68:
        return "Neutral"
    
    emotion_data = facial_data[:, -7:]
    emotion_averages = np.sum(emotion_data, axis=0) / facial_data.shape[0]
    neutral_weight = 0.4
    emotion_averages[4] *= neutral_weight
    
    emotion_labels = ["Angry", "Disgusted", "Fearful", "Happy", "Neutral", "Sad", "Surprised"]
    highest_idx = int(np.argmax(emotion_averages))
    return emotion_labels[highest_idx]


def adjust_animation_data_length(facial_data, animation_data):
    facial_length = len(facial_data)
    animation_length = len(animation_data)
    if animation_length >= facial_length:
        return animation_data[:facial_length]
    else:
        extended = list(animation_data)
        for i in range(facial_length - animation_length):
            extended.append(animation_data[i % animation_length])
        return extended

def merge_animation_data_into_facial_data(facial_data, animation_data, dimensions, alpha=1.0):
    animation_data = adjust_animation_data_length(facial_data, animation_data)
    num_frames = len(facial_data)

    for i in range(num_frames):
        for dim in dimensions:
            delta = animation_data[i][dim]

            if delta <= 0.0:
                continue  # skip non-positive changes

            scaled_delta = alpha * delta
            candidate_value = facial_data[i][dim] + scaled_delta

            if candidate_value > facial_data[i][dim]:
                facial_data[i][dim] = min(candidate_value, 1.0)  # clamp to 1.0

    return facial_data




def merge_emotion_data_into_facial_data_wrapper(facial_data, emotion_animation_data):
    from neurosync.api.animations.face_blend_shapes import FaceBlendShape
    dimensions = [
      #  FaceBlendShape.JawForward.value,
      #  FaceBlendShape.JawLeft.value,
      #  FaceBlendShape.JawRight.value,
       # FaceBlendShape.JawOpen.value,

       # FaceBlendShape.MouthClose.value,
     #   FaceBlendShape.MouthFunnel.value,       # Added .value
      #  FaceBlendShape.MouthPucker.value,        # Added .value
        FaceBlendShape.MouthLeft.value,
        FaceBlendShape.MouthRight.value,         # Added .value
        FaceBlendShape.MouthSmileLeft.value,     # Added .value
        FaceBlendShape.MouthSmileRight.value,
        FaceBlendShape.MouthFrownLeft.value,     # Added .value
        FaceBlendShape.MouthFrownRight.value,    # Added .value
        FaceBlendShape.MouthDimpleLeft.value,
        FaceBlendShape.MouthDimpleRight.value,   # Added .value
        FaceBlendShape.MouthStretchLeft.value,   # Added .value
        FaceBlendShape.MouthStretchRight.value,
     #   FaceBlendShape.MouthRollLower.value,     # Added .value
     #   FaceBlendShape.MouthRollUpper.value,     # Added .value
    #    FaceBlendShape.MouthShrugLower.value,      # Added .value
        FaceBlendShape.MouthShrugUpper.value,      # Added .value
        FaceBlendShape.MouthPressLeft.value,       # Added .value
        FaceBlendShape.MouthPressRight.value,      # Added .value
     #   FaceBlendShape.MouthLowerDownLeft.value,   # Added .value
    #    FaceBlendShape.MouthLowerDownRight.value,  # Added .value
        FaceBlendShape.MouthUpperUpLeft.value,     # Added .value
        FaceBlendShape.MouthUpperUpRight.value,    # Added .value

      #  FaceBlendShape.EyeBlinkLeft.value,         # Added .value
     #   FaceBlendShape.EyeLookDownLeft.value,        # Added .value
      #  FaceBlendShape.EyeLookInLeft.value,          # Added .value
      #  FaceBlendShape.EyeLookOutLeft.value,         # Added .value
     #   FaceBlendShape.EyeLookUpLeft.value,          # Added .value
        FaceBlendShape.EyeSquintLeft.value,          # Added .value
    #    FaceBlendShape.EyeWideLeft.value,            # Added .value

      #  FaceBlendShape.EyeBlinkRight.value,          # Added .value
    #    FaceBlendShape.EyeLookDownRight.value,         # Added .value
     #   FaceBlendShape.EyeLookInRight.value,         # Added .value
     #   FaceBlendShape.EyeLookOutRight.value,         # Added .value
    #    FaceBlendShape.EyeLookUpRight.value,         # Added .value
        FaceBlendShape.EyeSquintRight.value,         # Added .value
      #  FaceBlendShape.EyeWideRight.value,           # Added .value

        FaceBlendShape.BrowDownLeft.value,           # Added .value
        FaceBlendShape.BrowDownRight.value,          # Added .value
        FaceBlendShape.BrowInnerUp.value,            # Added .value
        FaceBlendShape.BrowOuterUpLeft.value,        # Added .value
        FaceBlendShape.BrowOuterUpRight.value        # Added .value
    ]



    facial_data = merge_animation_data_into_facial_data(facial_data, emotion_animation_data, dimensions)
    
    return facial_data


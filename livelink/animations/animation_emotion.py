from livelink.connect.faceblendshapes import FaceBlendShape
import numpy as np

from livelink.animations.blending_anims import blend_animation_data_to_loop_by_dimension

def determine_highest_emotion(facial_data, perform_calculation=True):
    if not perform_calculation or facial_data.shape[1] != 68:
        return "Neutral"
    
    emotion_data = facial_data[:, -7:]
    emotion_averages = np.sum(emotion_data, axis=0) / facial_data.shape[0]
    neutral_weight = 0.6
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

def merge_animation_data_into_facial_data(facial_data, animation_data, dimensions, alpha=0.6, blend_frame_count=32):
    animation_data = adjust_animation_data_length(facial_data, animation_data)
    animation_data = blend_animation_data_to_loop_by_dimension(animation_data, dimensions, blend_frame_count)
    
    num_frames = len(facial_data)

    for i in range(num_frames):
        for dim in dimensions:
            delta = animation_data[i][dim]
            new_value = facial_data[i][dim] + alpha * delta
            new_value = min(max(new_value, 0.0), 1.0)
            facial_data[i][dim] = new_value
            
    return facial_data

def merge_emotion_data_into_facial_data_wrapper(facial_data, emotion_animation_data, alpha=0.5, blend_frame_count=32):

    dimensions = [
        FaceBlendShape.BrowDownLeft.value,
        FaceBlendShape.BrowDownRight.value,
        FaceBlendShape.BrowInnerUp.value,
        FaceBlendShape.BrowOuterUpLeft.value,
        FaceBlendShape.BrowOuterUpRight.value,
        FaceBlendShape.CheekPuff.value,
        FaceBlendShape.CheekSquintLeft.value,
        FaceBlendShape.CheekSquintRight.value,
        FaceBlendShape.NoseSneerLeft.value,
        FaceBlendShape.NoseSneerRight.value,
        FaceBlendShape.MouthSmileLeft.value,
        FaceBlendShape.MouthSmileRight.value,
        FaceBlendShape.MouthFrownLeft.value,
        FaceBlendShape.MouthFrownRight.value,
        FaceBlendShape.MouthDimpleLeft.value,
        FaceBlendShape.MouthDimpleRight.value,
    ]
    facial_data = merge_animation_data_into_facial_data(
        facial_data,
        emotion_animation_data,
        dimensions,
        alpha,
        blend_frame_count
    )
    
    return facial_data

from livelink.connect.faceblendshapes import FaceBlendShape
import numpy as np

# -------------------- Emotion Detection --------------------
def determine_highest_emotion(facial_data, perform_calculation=True):
    """
    Determines the dominant emotion from facial data.
    
    Parameters:
      facial_data (np.ndarray): 2D array with shape (num_frames, dims). Expected dims=68 for emotion calculation.
      perform_calculation (bool): If False, returns "Neutral".
      
    Returns:
      str: Dominant emotion label.
    """
    if not perform_calculation or facial_data.shape[1] != 68:
        return "Neutral"
    
    # Extract the last 7 columns (assumed to be emotion values)
    emotion_data = facial_data[:, -7:]
    # Compute average for each emotion dimension
    emotion_averages = np.sum(emotion_data, axis=0) / facial_data.shape[0]
    # Apply a weight to "Neutral" (assumed index 4)
    neutral_weight = 0.4
    emotion_averages[4] *= neutral_weight
    
    emotion_labels = ["Angry", "Disgusted", "Fearful", "Happy", "Neutral", "Sad", "Surprised"]
    highest_idx = int(np.argmax(emotion_averages))
    return emotion_labels[highest_idx]


# -------------------- Helper Functions --------------------
def adjust_animation_data_length(facial_data, animation_data):
    """
    Adjusts the length of animation_data to match facial_data.
    If animation_data is too short, it is repeated cyclically.
    """
    facial_length = len(facial_data)
    animation_length = len(animation_data)
    if animation_length >= facial_length:
        return animation_data[:facial_length]
    else:
        extended = list(animation_data)
        for i in range(facial_length - animation_length):
            extended.append(animation_data[i % animation_length])
        return extended

def blend_data_dimensions_to_loop(facial_data, dimensions, blend_frame_count):
    """
    Smooths the transition between the last and first blend_frame_count frames for the given dimensions.
    """
    num_frames = len(facial_data)
    for dim in dimensions:
        for i in range(blend_frame_count):
            alpha = i / blend_frame_count
            start_value = facial_data[i][dim]
            end_value = facial_data[num_frames - blend_frame_count + i][dim]
            blended_value = (1 - alpha) * end_value + alpha * start_value
            facial_data[num_frames - blend_frame_count + i][dim] = blended_value

def merge_animation_data_into_facial_data(facial_data, animation_data, dimensions, alpha=0.7):
    """
    Merges animation_data into facial_data for specified dimensions using additive blending.
    The blending formula is:
        final_value = base_value + alpha * animation_delta
    The result is clamped between 0.0 and 1.0.
    """
    # Ensure the animation data matches the length of facial_data.
    animation_data = adjust_animation_data_length(facial_data, animation_data)
    num_frames = len(facial_data)
    
    # Copy the original facial data to avoid modifying it in place.
    blended_facial_data = [frame.copy() for frame in facial_data]
    
    # Apply additive blending for each frame and specified dimension.
    for i in range(num_frames):
        for dim in dimensions:
            base_value = blended_facial_data[i][dim]
            animation_delta = animation_data[i][dim]
            blended_value = base_value + alpha * animation_delta
            # Clamp the value to [0.0, 1.0]
            blended_value = min(max(blended_value, 0.0), 1.0)
            blended_facial_data[i][dim] = blended_value
            
    return blended_facial_data


# -------------------- Emotion Merging --------------------
def merge_emotion_data_into_facial_data_wrapper(facial_data, emotion_animation_data, alpha=0.7):
    """
    Merges preloaded emotion animation data into facial_data.
    It blends the specified dimensions additively and then smooths the loop.
    
    Parameters:
      facial_data (list of lists): Generated facial data.
      emotion_animation_data (list of lists): Preloaded emotion animation data.
      alpha (float): Blending weight.
      blend_frame_count (int): Number of frames over which to smooth the loop.
    
    Returns:
      list of lists: Blended facial data.
    """
    dimensions = [
        # Eye-related blend shapes
      
        FaceBlendShape.EyeSquintLeft.value,

        FaceBlendShape.EyeSquintRight.value,

        # Brow-related blend shapes
        FaceBlendShape.BrowDownLeft.value,
        FaceBlendShape.BrowDownRight.value,
        FaceBlendShape.BrowInnerUp.value,
        FaceBlendShape.BrowOuterUpLeft.value,
        FaceBlendShape.BrowOuterUpRight.value,
        
        # Cheek-related blend shapes
        FaceBlendShape.CheekPuff.value,
        FaceBlendShape.CheekSquintLeft.value,
        FaceBlendShape.CheekSquintRight.value,

        # Nose-related blend shapes
        FaceBlendShape.NoseSneerLeft.value,
        FaceBlendShape.NoseSneerRight.value,
        FaceBlendShape.MouthLeft.value,
        FaceBlendShape.MouthRight.value,
        FaceBlendShape.MouthSmileLeft.value,
        FaceBlendShape.MouthSmileRight.value,
        FaceBlendShape.MouthFrownLeft.value,
        FaceBlendShape.MouthFrownRight.value,
        FaceBlendShape.MouthDimpleLeft.value,
        FaceBlendShape.MouthDimpleRight.value,
        FaceBlendShape.MouthStretchLeft.value,
        FaceBlendShape.MouthStretchRight.value,
        FaceBlendShape.MouthRollLower.value,
        FaceBlendShape.MouthRollUpper.value,
        FaceBlendShape.MouthShrugLower.value,
        FaceBlendShape.MouthShrugUpper.value,
        FaceBlendShape.MouthPressLeft.value,
        FaceBlendShape.MouthPressRight.value,
        FaceBlendShape.MouthLowerDownLeft.value,
        FaceBlendShape.MouthLowerDownRight.value,
        FaceBlendShape.MouthUpperUpLeft.value,
        FaceBlendShape.MouthUpperUpRight.value,

    ]
    
    # Ensure emotion_animation_data matches the length of facial_data.
    emotion_animation_data = adjust_animation_data_length(facial_data, emotion_animation_data)
    
    # Merge using additive blending.
    facial_data = merge_animation_data_into_facial_data(facial_data, emotion_animation_data, dimensions, alpha)
    
    # -------------------- Added Print Statement --------------------
    print("Successfully merged emotion data!")  # This print indicates successful merging of emotion data.
       
    return facial_data

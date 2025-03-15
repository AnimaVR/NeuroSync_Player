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
    neutral_weight = 0.6
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


def blend_animation_data_to_loop(animation_data, dimensions, blend_frame_count):
    """
    Smooths the transition at the loop boundary in the animation data for the specified dimensions.
    
    For each dimension, the last blend_frame_count frames are linearly blended with the first
    blend_frame_count frames so that the repeated (cyclic) animation data transitions smoothly.
    
    Parameters:
      animation_data (list of lists): Animation data to be blended.
      dimensions (list): Indices of dimensions to blend.
      blend_frame_count (int): Number of frames over which to blend the loop.
      
    Returns:
      list of lists: Animation data with blended loop for specified dimensions.
    """
    num_frames = len(animation_data)
    for dim in dimensions:
        for i in range(blend_frame_count):
            blend_alpha = i / blend_frame_count
            start_value = animation_data[i][dim]
            end_value = animation_data[num_frames - blend_frame_count + i][dim]
            blended_value = (1 - blend_alpha) * end_value + blend_alpha * start_value
            animation_data[num_frames - blend_frame_count + i][dim] = blended_value
    return animation_data


def merge_animation_data_into_facial_data(facial_data, animation_data, dimensions, alpha=0.6, blend_frame_count=32):
    """
    Merges the (loop-blended) animation data into the facial data for the specified dimensions.
    
    The steps are:
      1. Adjust the animation data length to match facial data (using cyclic repetition if needed).
      2. Blend the animation data at the loop boundary for the specified dimensions.
      3. For each frame and dimension, add (α * blended animation delta) to the facial data.
         (Neutral pose is assumed to be all zeros, so the delta is the animation value.)
      4. Clamp the result in the facial data between 0.0 and 1.0.
      
    Note: The facial_data remains unchanged except for having the blended animation delta merged in.
    
    Parameters:
      facial_data (list of lists): Base facial data.
      animation_data (list of lists): Animation data (e.g., emotion data) to be merged.
      dimensions (list): Indices of dimensions to merge.
      alpha (float): Blending weight.
      blend_frame_count (int): Number of frames for loop blending in the animation data.
    
    Returns:
      list of lists: Facial data with merged animation deltas.
    """
    # Adjust the animation data length.
    animation_data = adjust_animation_data_length(facial_data, animation_data)
    
    # Blend the loop in the animation data for the specified dimensions.
    animation_data = blend_animation_data_to_loop(animation_data, dimensions, blend_frame_count)
    
    num_frames = len(facial_data)
    
    # Merge the (blended) animation data into the facial data.
    for i in range(num_frames):
        for dim in dimensions:
            # Delta is simply the animation data value (relative to a neutral pose of zeros).
            delta = animation_data[i][dim]
            new_value = facial_data[i][dim] + alpha * delta
            # Clamp the merged value.
            new_value = min(max(new_value, 0.0), 1.0)
            facial_data[i][dim] = new_value
            
    return facial_data


# -------------------- Emotion Merging --------------------
def merge_emotion_data_into_facial_data_wrapper(facial_data, emotion_animation_data, alpha=0.5, blend_frame_count=32):
    """
    Merges preloaded emotion animation data into facial_data.
    The specified dimensions in the animation data are loop-blended first, and then
    the corresponding deltas are merged into the facial data.
    
    Parameters:
      facial_data (list of lists): Generated facial data.
      emotion_animation_data (list of lists): Preloaded emotion animation data.
      alpha (float): Blending weight.
      blend_frame_count (int): Number of frames over which to smooth the loop in the animation data.
    
    Returns:
      list of lists: Facial data with merged emotion data.
    """
    dimensions = [
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
        
        # Mouth-related blend shapes
        FaceBlendShape.MouthSmileLeft.value,
        FaceBlendShape.MouthSmileRight.value,
        FaceBlendShape.MouthFrownLeft.value,
        FaceBlendShape.MouthFrownRight.value,
        FaceBlendShape.MouthDimpleLeft.value,
        FaceBlendShape.MouthDimpleRight.value,
    ]
    
    # Adjust and blend the emotion animation data, then merge into facial data.
    facial_data = merge_animation_data_into_facial_data(
        facial_data,
        emotion_animation_data,
        dimensions,
        alpha,
        blend_frame_count
    )
    
    return facial_data

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

def merge_animation_data_into_facial_data(facial_data, animation_data, dimensions, alpha=1.0):
    """
    Merges animation_data into facial_data for specified dimensions,
    mimicking the C# approach:
      1. Adjust the animation data length to match facial_data.
      2. Compute animation deltas relative to a neutral pose (zeros).
      3. Add the delta (scaled by alpha) to the facial_data for each specified dimension.
      4. Use cyclic repetition for animation frames if needed.
      5. Clamp the result to [0.0, 1.0].
    
    Parameters:
        facial_data (list of lists): Base facial data.
        animation_data (list of lists): Animation data to merge.
        dimensions (list): Indices of dimensions to blend.
        alpha (float): Blending weight.
        
    Returns:
        list of lists: Facial data with merged animation data.
    """
    # Adjust the animation data to match the length of facial_data.
    animation_data = adjust_animation_data_length(facial_data, animation_data)
    
    # Compute animation deltas using a neutral pose (all zeros).
    # Since neutral pose is zeros, delta is just the animation data value.
    animation_deltas = []
    for frame in animation_data:
        # --- Highlighted Change ---
        # Instead of conditionally blending, we compute the delta directly for each dimension.
        frame_delta = [frame[dim] for dim in dimensions]
        animation_deltas.append(frame_delta)
    
    num_frames = len(facial_data)
    animation_frame_count = len(animation_deltas)
    
    # Blend the computed deltas into the facial data.
    # We iterate through each facial frame and add the appropriate delta.
    for i in range(num_frames):
        animation_frame_index = i % animation_frame_count  # Use cyclic repetition.
        for j, dimension in enumerate(dimensions):
            # --- Highlighted Change ---
            # Add the delta (scaled by alpha) directly to the current facial value.
            delta = animation_deltas[animation_frame_index][j]
            blended_value = facial_data[i][dimension] + alpha * delta
            
            # Clamp the value to [0.0, 1.0].
            blended_value = min(max(blended_value, 0.0), 1.0)
            facial_data[i][dimension] = blended_value
            
    return facial_data





# -------------------- Emotion Merging --------------------
def merge_emotion_data_into_facial_data_wrapper(facial_data, emotion_animation_data, alpha=0.5):
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
      
     #   FaceBlendShape.EyeSquintLeft.value,
      #  FaceBlendShape.EyeWideLeft.value,

     #   FaceBlendShape.EyeSquintRight.value,
       # FaceBlendShape.EyeWideRight.value,

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
     #   FaceBlendShape.MouthLeft.value,
     #   FaceBlendShape.MouthRight.value,
        FaceBlendShape.MouthSmileLeft.value,
        FaceBlendShape.MouthSmileRight.value,
        FaceBlendShape.MouthFrownLeft.value,
        FaceBlendShape.MouthFrownRight.value,
        FaceBlendShape.MouthDimpleLeft.value,
        FaceBlendShape.MouthDimpleRight.value,
     #   FaceBlendShape.MouthStretchLeft.value,
     #   FaceBlendShape.MouthStretchRight.value,
     #   FaceBlendShape.MouthRollLower.value,
     #   FaceBlendShape.MouthRollUpper.value,
     #   FaceBlendShape.MouthShrugLower.value,
     #   FaceBlendShape.MouthShrugUpper.value,
      #  FaceBlendShape.MouthPressLeft.value,
      #  FaceBlendShape.MouthPressRight.value,
     #   FaceBlendShape.MouthLowerDownLeft.value,
     #   FaceBlendShape.MouthLowerDownRight.value,
     #   FaceBlendShape.MouthUpperUpLeft.value,
    #    FaceBlendShape.MouthUpperUpRight.value,

    ]
    
    # Ensure emotion_animation_data matches the length of facial_data.
    emotion_animation_data = adjust_animation_data_length(facial_data, emotion_animation_data)
    
    # Merge using additive blending.
    facial_data = merge_animation_data_into_facial_data(facial_data, emotion_animation_data, dimensions, alpha)
    
    # -------------------- Added Print Statement --------------------
  #  print("Successfully merged emotion data!")  # This print indicates successful merging of emotion data.
       
    return facial_data

from livelink.connect.faceblendshapes import FaceBlendShape
import numpy as np
import random
import os
import pandas as pd

# -------------------- Emotion Detection --------------------
def determine_highest_emotion(facial_data, perform_calculation=True):
    """
    Determines the dominant emotion from facial data.
    
    Parameters:
      facial_data (np.ndarray): 2D array of shape (num_frames, dims). Expected dims=68 for emotion calculation.
      perform_calculation (bool): If False, returns "Neutral".
    
    Returns:
      str: Dominant emotion label from ["Angry", "Disgusted", "Fearful", "Happy", "Neutral", "Sad", "Surprised"].
    """
    if not perform_calculation or facial_data.shape[1] != 68:
        return "Neutral"
    
    # Extract the last 7 columns (assumed to be emotion values)
    emotion_data = facial_data[:, -7:]
    # Compute average for each emotion dimension
    emotion_averages = np.sum(emotion_data, axis=0) / facial_data.shape[0]
    # Apply a weight to "Neutral" (assumed index 4)
    neutral_weight = 0.7
    emotion_averages[4] *= neutral_weight
    
    emotion_labels = ["Angry", "Disgusted", "Fearful", "Happy", "Neutral", "Sad", "Surprised"]
    highest_idx = int(np.argmax(emotion_averages))
    return emotion_labels[highest_idx]


# -------------------- Helper Functions --------------------
def adjust_animation_data_length(facial_data, animation_data):
    """
    Adjusts the length of animation_data to match the number of frames in facial_data.
    If animation_data is too long, it is trimmed; if too short, frames are repeated cyclically.
    
    Parameters:
      facial_data: list-like of frames.
      animation_data: list-like of frames.
    
    Returns:
      list: Adjusted animation_data with the same length as facial_data.
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
    
    Parameters:
      facial_data (list of lists): Facial data frames.
      dimensions (list of int): Dimensions to smooth.
      blend_frame_count (int): Number of frames over which to blend.
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
    Merges animation_data into facial_data for specific dimensions using additive blending.
    The neutral pose is assumed to be zero.
    
    Parameters:
      facial_data (list of lists): Generated facial data.
      animation_data (list of lists): Emotion animation data (should be adjusted to same length as facial_data).
      dimensions (list of int): Indices corresponding to emotion dimensions.
      alpha (float): Blending weight.
    
    Returns:
      list of lists: Modified facial_data with blended emotion animation.
    """
    animation_data = adjust_animation_data_length(facial_data, animation_data)
    num_frames = len(facial_data)
    for i in range(num_frames):
        for dim in dimensions:
            delta = animation_data[i][dim]
            facial_data[i][dim] = min(max(facial_data[i][dim] + alpha * delta, 0.0), 1.0)
    return facial_data


# -------------------- Emotion Merging --------------------
def merge_emotion_data_into_facial_data_wrapper(facial_data, emotion_animation_data, dimensions=None, alpha=0.7, blend_frame_count=32):
    """
    Merges preloaded emotion animation data into generated facial data.
    If emotion_animation_data is shorter than facial_data, its frames are repeated to match the length.
    After merging using additive blending, the specified dimensions are smoothed between the last
    and first frames to create a seamless loop.
    
    Parameters:
      facial_data (list of lists): Generated facial data.
      emotion_animation_data (list of lists): Emotion animation data.
      dimensions (list of int, optional): Indices for emotion dimensions. Defaults to selected emotion blendshapes.
      alpha (float): Blending weight.
      blend_frame_count (int): Number of frames over which to smooth the transition.
    
    Returns:
      list of lists: Blended facial data.
    """
    # Default emotion dimensions (only include selected emotion-related blendshapes)
    if dimensions is None:
        dimensions = [
            FaceBlendShape.MouthSmileLeft.value,
            FaceBlendShape.MouthSmileRight.value,
            FaceBlendShape.MouthFrownLeft.value,
            FaceBlendShape.MouthFrownRight.value,
            FaceBlendShape.NoseSneerLeft.value,
            FaceBlendShape.NoseSneerRight.value,
        ]
    
    # Ensure emotion_animation_data matches the length of facial_data.
    emotion_animation_data = adjust_animation_data_length(facial_data, emotion_animation_data)
    
    # Merge using additive blending.
    facial_data = merge_animation_data_into_facial_data(facial_data, emotion_animation_data, dimensions, alpha)
    
    # Smooth the transition for the selected dimensions.
    blend_data_dimensions_to_loop(facial_data, dimensions, blend_frame_count)
    
    return facial_data


# -------------------- Preloading Emotion Animations --------------------
# Optionally, you can use an empty list for COLUMNS_TO_DROP here if none are needed.
COLUMNS_TO_DROP = []

def load_animation_from_csv(csv_path):
    """
    Loads an animation CSV file, dropping unnecessary columns.
    Returns the animation data as a NumPy array.
    """
    try:
        data = pd.read_csv(csv_path)
        data = data.drop(columns=['Timecode', 'BlendshapeCount'] + COLUMNS_TO_DROP, errors='ignore')
        return data.values
    except Exception as e:
        print(f"Error loading animation from {csv_path}: {e}")
        return None

def blend_animation(data, blend_frames=30):
    """
    Blends the start and end frames of the animation to create a smooth loop.
    """
    last_frames = data[-blend_frames:]
    first_frames = data[:blend_frames]
    blended_frames = np.zeros_like(last_frames)
    for i in range(blend_frames):
        alpha = i / blend_frames
        blended_frames[i] = (1 - alpha) * last_frames[i] + alpha * first_frames[i]
    blended_data = np.vstack([data[:-blend_frames], blended_frames])
    return blended_data

def load_emotion_animations(folder_path, blend_frames=30):
    """
    Loads all CSV files from a given emotion folder, blends their start and end frames,
    and returns a list of blended animations.
    """
    animations = []
    if not os.path.isdir(folder_path):
        print(f"Directory {folder_path} does not exist.")
        return animations
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(folder_path, file_name)
            animation = load_animation_from_csv(file_path)
            if animation is not None:
                try:
                    blended = blend_animation(animation, blend_frames=blend_frames)
                    animations.append(blended)
                except Exception as e:
                    print(f"Error blending animation {file_path}: {e}")
    return animations

# Define emotion folder paths.
emotion_paths = {
    "Angry": r"livelink/animations/Angry/",
    "Disgusted": r"livelink/animations/Disgusted/",
    "Fearful": r"livelink/animations/Fearful/",
    "Happy": r"livelink/animations/Happy/",
    "Neutral": r"livelink/animations/Neutral/",
    "Sad": r"livelink/animations/Sad/",
    "Surprised": r"livelink/animations/Surprised/"
}

# Preload emotion animations into a global dictionary.
emotion_animations = {}
for emotion, folder in emotion_paths.items():
    emotion_animations[emotion] = load_emotion_animations(folder)
    print(f"Loaded {len(emotion_animations[emotion])} animations for emotion '{emotion}'")

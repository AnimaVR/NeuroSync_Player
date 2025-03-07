import os
import numpy as np
import pandas as pd

def load_animation_from_csv(csv_path):
    """
    Loads an animation CSV file, dropping unnecessary columns ('Timecode', 'BlendshapeCount').
    
    Parameters:
        csv_path (str): Path to the CSV file.
        
    Returns:
        np.ndarray or None: The animation data as a NumPy array, or None if an error occurs.
    """
    try:
        data = pd.read_csv(csv_path)
        # Drop columns that are not needed for animation processing.
        data = data.drop(columns=['Timecode', 'BlendshapeCount'], errors='ignore')
        return data.values
    except Exception as e:
        print(f"Error loading animation from {csv_path}: {e}")
        return None

def blend_animation(data, blend_frames=30):
    """
    Blends the start and end frames of the animation to create a smooth loop.
    
    Parameters:
        data (np.ndarray): The animation data array.
        blend_frames (int): Number of frames to blend at the start and end.
        
    Returns:
        np.ndarray: The blended animation data.
    """
    last_frames = data[-blend_frames:]
    first_frames = data[:blend_frames]
    blended_frames = np.zeros_like(last_frames)
    for i in range(blend_frames):
        alpha = i / blend_frames
        blended_frames[i] = (1 - alpha) * last_frames[i] + alpha * first_frames[i]
    # Replace the last blend_frames with the blended ones.
    blended_data = np.vstack([data[:-blend_frames], blended_frames])
    return blended_data

def load_emotion_animations(folder_path, blend_frames=30):
    """
    Loads all CSV animation files from a given folder, blends their start and end frames,
    and returns a list of blended animations.
    
    Parameters:
        folder_path (str): Path to the folder containing emotion animation CSV files.
        blend_frames (int): Number of frames to blend for smooth looping.
        
    Returns:
        list: A list of blended animations as NumPy arrays.
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
    "Angry": os.path.join("livelink", "animations", "Angry"),
    "Disgusted": os.path.join("livelink", "animations", "Disgusted"),
    "Fearful": os.path.join("livelink", "animations", "Fearful"),
    "Happy": os.path.join("livelink", "animations", "Happy"),
    "Neutral": os.path.join("livelink", "animations", "Neutral"),
    "Sad": os.path.join("livelink", "animations", "Sad"),
    "Surprised": os.path.join("livelink", "animations", "Surprised")
}

# Preload emotion animations into a global dictionary.
emotion_animations = {}
for emotion, folder in emotion_paths.items():
    emotion_animations[emotion] = load_emotion_animations(folder)
    print(f"Loaded {len(emotion_animations[emotion])} animations for emotion '{emotion}'")

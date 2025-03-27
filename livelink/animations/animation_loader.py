# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

import os
import pandas as pd

def load_animation(csv_path):
    """
    Loads the default animation CSV file
    Returns the animation data as a NumPy array.
    """
    data = pd.read_csv(csv_path)
    data = data.drop(columns=['Timecode', 'BlendshapeCount'])
    return data.values

def load_emotion_animations(folder_path, blend_frames=16):
    
    from livelink.animations.blending_anims import blend_animation_start_end
    animations = []
    if not os.path.isdir(folder_path):
        print(f"Directory {folder_path} does not exist.")
        return animations
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(folder_path, file_name)
            animation = load_animation(file_path)
            if animation is not None:
                try:
                    blended = blend_animation_start_end(animation, blend_frames=blend_frames)
                    animations.append(blended)
                except Exception as e:
                    print(f"Error blending animation {file_path}: {e}")
    return animations

emotion_paths = {
    "Angry": os.path.join("livelink", "animations", "Angry"),
    "Disgusted": os.path.join("livelink", "animations", "Disgusted"),
    "Fearful": os.path.join("livelink", "animations", "Fearful"),
    "Happy": os.path.join("livelink", "animations", "Happy"),
    "Neutral": os.path.join("livelink", "animations", "Neutral"),
    "Sad": os.path.join("livelink", "animations", "Sad"),
    "Surprised": os.path.join("livelink", "animations", "Surprised")
}

emotion_animations = {}
for emotion, folder in emotion_paths.items():
    emotion_animations[emotion] = load_emotion_animations(folder)
    print(f"Loaded {len(emotion_animations[emotion])} animations for emotion '{emotion}'")

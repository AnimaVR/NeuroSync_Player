import numpy as np
import pandas as pd

def save_generated_data_as_csv(generated, output_path, include_emotion_dimensions=False):
    # Base columns for blendshape data
    base_columns = [
        'Timecode', 'BlendshapeCount', 'EyeBlinkLeft', 'EyeLookDownLeft', 'EyeLookInLeft', 'EyeLookOutLeft', 'EyeLookUpLeft', 
        'EyeSquintLeft', 'EyeWideLeft', 'EyeBlinkRight', 'EyeLookDownRight', 'EyeLookInRight', 'EyeLookOutRight', 'EyeLookUpRight', 
        'EyeSquintRight', 'EyeWideRight', 'JawForward', 'JawRight', 'JawLeft', 'JawOpen', 'MouthClose', 'MouthFunnel', 'MouthPucker', 
        'MouthRight', 'MouthLeft', 'MouthSmileLeft', 'MouthSmileRight', 'MouthFrownLeft', 'MouthFrownRight', 'MouthDimpleLeft', 
        'MouthDimpleRight', 'MouthStretchLeft', 'MouthStretchRight', 'MouthRollLower', 'MouthRollUpper', 'MouthShrugLower', 
        'MouthShrugUpper', 'MouthPressLeft', 'MouthPressRight', 'MouthLowerDownLeft', 'MouthLowerDownRight', 'MouthUpperUpLeft', 
        'MouthUpperUpRight', 'BrowDownLeft', 'BrowDownRight', 'BrowInnerUp', 'BrowOuterUpLeft', 'BrowOuterUpRight', 'CheekPuff', 
        'CheekSquintLeft', 'CheekSquintRight', 'NoseSneerLeft', 'NoseSneerRight', 'TongueOut', 'HeadYaw', 'HeadPitch', 'HeadRoll', 
        'LeftEyeYaw', 'LeftEyePitch', 'LeftEyeRoll', 'RightEyeYaw', 'RightEyePitch', 'RightEyeRoll'
    ]
    
    # Emotion dimensions (optional)
    emotion_columns = ['Angry', 'Disgusted', 'Fearful', 'Happy', 'Neutral', 'Sad', 'Surprised']
    
    # Include emotion dimensions conditionally
    if include_emotion_dimensions:
        columns = base_columns + emotion_columns
    else:
        columns = base_columns

    # Convert the generated list to a NumPy array
    generated = np.array(generated)
    
    # Reshape the array to match the column count
    total_columns = len(columns) - 2  # Subtract Timecode and BlendshapeCount columns
    generated = generated.reshape(-1, total_columns)
    
    # Generate timecodes
    frame_count = generated.shape[0]
    frame_rate = 60  # 60 FPS
    frame_duration = 1 / frame_rate  # Duration of each frame in seconds

    # Create timecodes in the HH:mm:ss:ff.mmm format
    timecodes = []
    for i in range(frame_count):
        total_seconds = i * frame_duration
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = (seconds - int(seconds)) * 1000
        frame_number = int(milliseconds / (1000 / frame_rate))
        timecode = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}:{frame_number:02}.{int(milliseconds):03}"
        timecodes.append(timecode)

    # Add timecodes and blendshape counts
    timecodes = np.array(timecodes).reshape(-1, 1)
    blendshape_counts = np.full((frame_count, 1), generated.shape[1])

    # Stack the data together
    data = np.hstack((timecodes, blendshape_counts, generated))

    # Create a DataFrame and save to CSV
    df = pd.DataFrame(data, columns=columns)
    df.to_csv(output_path, index=False)
    print(f"Generated data saved to {output_path}")

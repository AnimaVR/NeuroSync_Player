import numpy as np
import pandas as pd

def save_generated_data_as_csv(generated, output_path):
    # Base columns (Blendshape data)
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
    
    # Emotion columns
    emotion_columns = ['Angry', 'Disgusted', 'Fearful', 'Happy', 'Neutral', 'Sad', 'Surprised']

    # Convert the generated list to a NumPy array
    generated = np.array(generated)

    # Determine the number of dimensions
    num_dimensions = generated.shape[1]  # Number of columns in the generated data
    if num_dimensions == 68:
        selected_columns = base_columns + emotion_columns  # Include emotions
        selected_data = generated  # Keep all 68 columns
    elif num_dimensions == 61:
        selected_columns = base_columns  # Only blendshape columns
        selected_data = generated[:, :61]  # Keep only the first 61 columns
    else:
        raise ValueError(f"Unexpected number of columns: {num_dimensions}. Expected 61 or 68.")


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
    blendshape_counts = np.full((frame_count, 1), selected_data.shape[1])

    # Stack the data together
    data = np.hstack((timecodes, blendshape_counts, selected_data))

    # Create a DataFrame and save to CSV
    df = pd.DataFrame(data, columns=selected_columns)
    df.to_csv(output_path, index=False)
    print(f"Generated data saved to {output_path}")



def generate_csv_in_memory(generated):
    """Generates CSV content and returns it as a BytesIO object."""
    # Base columns (Blendshape data)
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

    # Emotion columns
    emotion_columns = ['Angry', 'Disgusted', 'Fearful', 'Happy', 'Neutral', 'Sad', 'Surprised']

    # Convert the generated list to a NumPy array
    generated = np.array(generated)

    # Determine the number of dimensions
    num_dimensions = generated.shape[1]
    if num_dimensions == 68:
        selected_columns = base_columns + emotion_columns
        selected_data = generated
    elif num_dimensions == 61:
        selected_columns = base_columns
        selected_data = generated[:, :61]
    else:
        raise ValueError(f"Unexpected number of columns: {num_dimensions}. Expected 61 or 68.")

    # Generate timecodes
    frame_count = generated.shape[0]
    frame_rate = 60
    frame_duration = 1 / frame_rate

    timecodes = []
    for i in range(frame_count):
        total_seconds = i * frame_duration
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = (seconds - int(seconds)) * 1000
        frame_number = int(milliseconds / (1000 / frame_rate))
        timecode = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}:{frame_number:02}.{int(milliseconds):03}"
        timecodes.append(timecode)

    timecodes = np.array(timecodes).reshape(-1, 1)
    blendshape_counts = np.full((frame_count, 1), selected_data.shape[1])

    data = np.hstack((timecodes, blendshape_counts, selected_data))

    # Convert to DataFrame
    df = pd.DataFrame(data, columns=selected_columns)

    # Save CSV content in memory
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_bytes = io.BytesIO(csv_buffer.getvalue().encode('utf-8'))
    return csv_bytes


def save_or_return_csv(generated, output_path=None, return_in_memory=False):
    """Saves to disk or returns a CSV as a BytesIO object based on the flag."""
    if return_in_memory:
        return generate_csv_in_memory(generated)
    else:
        save_generated_data_as_csv(generated, output_path)
        return None

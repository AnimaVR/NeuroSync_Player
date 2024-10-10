# This code is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
# For more details, visit: https://creativecommons.org/licenses/by-nc/4.0/

# faceblendshapes.py

from enum import Enum

class FaceBlendShape(Enum):
    EyeBlinkLeft = 0
    EyeLookDownLeft = 1
    EyeLookInLeft = 2
    EyeLookOutLeft = 3
    EyeLookUpLeft = 4
    EyeSquintLeft = 5
    EyeWideLeft = 6
    EyeBlinkRight = 7
    EyeLookDownRight = 8
    EyeLookInRight = 9
    EyeLookOutRight = 10
    EyeLookUpRight = 11
    EyeSquintRight = 12
    EyeWideRight = 13
    JawForward = 14
    JawLeft = 15
    JawRight = 16
    JawOpen = 17
    MouthClose = 18
    MouthFunnel = 19
    MouthPucker = 20
    MouthLeft = 21
    MouthRight = 22
    MouthSmileLeft = 23
    MouthSmileRight = 24
    MouthFrownLeft = 25
    MouthFrownRight = 26
    MouthDimpleLeft = 27
    MouthDimpleRight = 28
    MouthStretchLeft = 29
    MouthStretchRight = 30
    MouthRollLower = 31
    MouthRollUpper = 32
    MouthShrugLower = 33
    MouthShrugUpper = 34
    MouthPressLeft = 35
    MouthPressRight = 36
    MouthLowerDownLeft = 37
    MouthLowerDownRight = 38
    MouthUpperUpLeft = 39
    MouthUpperUpRight = 40
    BrowDownLeft = 41
    BrowDownRight = 42
    BrowInnerUp = 43
    BrowOuterUpLeft = 44
    BrowOuterUpRight = 45
    CheekPuff = 46
    CheekSquintLeft = 47
    CheekSquintRight = 48
    NoseSneerLeft = 49
    NoseSneerRight = 50
    TongueOut = 51
    HeadYaw = 52
    HeadPitch = 53
    HeadRoll = 54
    LeftEyeYaw = 55
    LeftEyePitch = 56
    LeftEyeRoll = 57
    RightEyeYaw = 58
    RightEyePitch = 59
    RightEyeRoll = 60
    Angry = 61
    Disgusted = 62
    Fearful = 63
    Happy = 64
    Neutral = 65
    Sad = 66
    Surprised = 67

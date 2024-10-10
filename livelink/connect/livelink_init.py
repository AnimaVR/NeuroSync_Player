# This code is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
# For more details, visit: https://creativecommons.org/licenses/by-nc/4.0/
# 
# # livelink_init.py

import socket
from livelink.connect.pylivelinkface import PyLiveLinkFace, FaceBlendShape


UDP_IP = "127.0.0.1"
UDP_PORT = 11111

def create_socket_connection():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((UDP_IP, UDP_PORT))
    return s

def initialize_py_face():
    py_face = PyLiveLinkFace()
    initial_blendshapes = [0.0] * 61
    for i, value in enumerate(initial_blendshapes):
        py_face.set_blendshape(FaceBlendShape(i), float(value))
    return py_face

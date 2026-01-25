import numpy as np

def calculate_angle(a, b, c):
    #the keypoints a, b, c are taken as an array of x, y coordinates
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    # Use arctan2 for cangle calculation
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    #if angle is greater than 180 take the supplementary angle 
    if angle > 180.0:
        angle = 360 - angle

    return angle

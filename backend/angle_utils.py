import numpy as np

def calculate_angle(a, b, c):
    """
    Calculates the angle at point B given points A, B, and C.
    A, B, C are (x, y) tuples or lists.
    Returns angle in degrees.
    """
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    # Use arctan2 for robust angle calculation
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle

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

class EMAFilter:
    """Exponential Moving Average Filter for smoothing jittery signals."""
    def __init__(self, alpha=0.3):
        self.alpha = alpha
        self.smoothed_value = None

    def apply(self, value):
        if self.smoothed_value is None:
            self.smoothed_value = value
        else:
            self.smoothed_value = (self.alpha * value) + (1 - self.alpha) * self.smoothed_value
        return self.smoothed_value

    def reset(self):
        self.smoothed_value = None

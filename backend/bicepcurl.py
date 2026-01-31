from angle_utils import calculate_angle, EMAFilter

class BicepCurlTracker:
    #constructor that gives the initial states, feedback and rep count initially set to 0
    def __init__(self):
        self.correct_reps = 0
        self.total_reps = 0
        self.accuracy = 0
        self.curl_state = "down"  # Arms start extended
        self.form_feedback = ""
        self.elbow_feedback = ""

        #these variables are used to validate a rep properly (to calculate accuracy)
        self.rep_valid = True
        self.hit_top = False

        # Calibration / Stable start
        self.is_calibrated = False
        self.stable_frames = 0
        
        # Filters for smoothing (EMA alpha=0.3)
        self.l_elbow_filter = EMAFilter(alpha=0.3)
        self.r_elbow_filter = EMAFilter(alpha=0.3)

    def process(self, landmarks):
        # Helper function to get landmark position and visibility
        def get_landmark(idx):
            lm = landmarks[idx]

            if hasattr(lm, 'x'):
                x = lm.x
            else:
                x = lm.get('x', 0)

            if hasattr(lm, 'y'):
                y = lm.y
            else:
                y = lm.get('y', 0)

            if hasattr(lm, 'visibility'):
                v = lm.visibility
            else:
                v = lm.get('visibility', 0)

            return [x, y], v

        try:
            # Required landmarks are taken

            # Left side landmarks are calculated
            left_shoulder, v1 = get_landmark(11)
            left_elbow, v2 = get_landmark(13)
            left_wrist, v3 = get_landmark(15)

            # Right side landmarks are calculated
            right_shoulder, v4 = get_landmark(12)
            right_elbow, v5 = get_landmark(14)
            right_wrist, v6 = get_landmark(16)

            #check the visibility scores to see if the that side(left/right) is visible 
            left_visible = all(v > 0.6 for v in [v1, v2, v3])
            right_visible = all(v > 0.6 for v in [v4, v5, v6])

            #angles are calculated based on the visible side
            left_elbow_angle = right_elbow_angle = 0

            #if both sides are visible then calculate the angles for both the sides
            if left_visible and right_visible:
                left_elbow_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
                right_elbow_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)

            #if only left side is visible then calculate the angles for the left side
            elif left_visible:
                left_elbow_angle = right_elbow_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)

            #if only right side is visible then calculate the angles for the right side
            elif right_visible:
                right_elbow_angle = left_elbow_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)

            #if no side is visible, give the rep count as it is, and send a message to the frontend
            else:
                accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0
                return {
                    "msg": "Upper body not fully visible", 
                    "reps": self.correct_reps, 
                    "total_reps": self.total_reps, 
                    "accuracy": round(accuracy, 2),
                    "feedback": {"form": "Body not visible"}
                }

            # Apply Smoothing
            left_elbow_angle = self.l_elbow_filter.apply(left_elbow_angle)
            right_elbow_angle = self.r_elbow_filter.apply(right_elbow_angle)
            avg_elbow_angle = (left_elbow_angle + right_elbow_angle) / 2

            # ---------------- CALIBRATION ----------------
            
            # Calibration: Hold steady 'Down' position (arms relaxed) for ~2 seconds (20 frames)
            if not self.is_calibrated:
                is_ready_pos = avg_elbow_angle >= 150 # Arms extended
                
                if is_ready_pos:
                    self.stable_frames += 1
                else:
                    self.stable_frames = 0

                if self.stable_frames >= 20:
                    self.is_calibrated = True
                else:
                    return {
                        "reps": self.correct_reps,
                        "total_reps": self.total_reps,
                        "accuracy": round(self.accuracy, 2),
                        "feedback": {"form": f"Hold arms steady for {max(0, (20 - self.stable_frames)//10)}s..."},
                        "msg": "Calibrating"
                    }

            # ---------------- POSITION CHECKS ----------------
            # EXTREMELY GENEROUS thresholds for counting (Total Reps)
            is_up = avg_elbow_angle <= 120   # Relaxed from 70/80
            is_down = avg_elbow_angle >= 140 # Relaxed from 150/160
            
            # Form check for Correct Reps (Keep strict for accuracy)
            is_up_strict = avg_elbow_angle <= 75

            # Extra strict check: do not over-curl too much (noise / wrong detection)
            too_high = left_elbow_angle < 35 or right_elbow_angle < 35

            #set the feedback, for elbow angle
            if is_up:
                self.elbow_feedback = "Good squeeze"
            elif is_down:
                self.elbow_feedback = "Curl up"
            else:
                self.elbow_feedback = "Full range"

            if too_high:
                self.form_feedback = "Too much curl (control it)"
            else:
                self.form_feedback = "Good form"

            #machine state logic
            if self.curl_state == "down":
                # Start moving up (with buffer)
                if avg_elbow_angle < 140:
                    self.curl_state = "up"
                    self.rep_valid = True
                    self.hit_top = False

            elif self.curl_state == "up":
                if is_up_strict:
                    self.hit_top = True

                if too_high:
                    self.rep_valid = False

                if is_down:
                    self.curl_state = "down"
                    self.total_reps += 1 # Always count the attempt

                    # Only count as correct if strict squeeze and control were met
                    if self.hit_top and self.rep_valid:
                        self.correct_reps += 1
                    
                    self.hit_top = False
                    self.rep_valid = True

            #calculate accuracy safely (avoid division by zero)
            self.accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0

            #average elbow angle for UI
            avg_elbow = (left_elbow_angle + right_elbow_angle) / 2

            return {
                "reps": self.correct_reps,
                "total_reps": self.total_reps,
                "accuracy": round(self.accuracy, 2),
                "state": self.curl_state,
                "feedback": {
                    "form": self.form_feedback,
                    "elbow": self.elbow_feedback
                },
                "angles": {
                    "left_elbow": int(left_elbow_angle),
                    "right_elbow": int(right_elbow_angle),
                    "elbow_avg": int(avg_elbow)
                }
            }

        except Exception as e:
            accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0
            return {
                "msg": f"Error: {str(e)}", 
                "reps": self.correct_reps, 
                "total_reps": self.total_reps, 
                "accuracy": round(accuracy, 2),
                "feedback": {"form": "Processing error"}
            }

from angle_utils import calculate_angle

class PushupTracker:
    #constructor that gives the initial states, feedback and rep count initially set to 0
    def __init__(self):
        self.correct_reps = 0
        self.total_reps = 0
        self.accuracy = 0
        self.pushup_state = "up"
        self.form_feedback = ""
        self.knee_feedback = ""
        self.elbow_feedback = ""

        #these variables are used to validate a rep properly (to calculate accuracy)
        self.rep_valid = True
        self.hit_bottom = False
        
        #makes sure the frames are stable before starting the exercise
        self.is_calibrated = False
        self.stable_frames = 0

    def process(self, landmarks):

        # this is a helper function to get the landmark position and the visibility of the landmark(this ensures if we have to take it into consideration or not)
        def get_landmark(idx):
            lm = landmarks[idx]
            
            #if the landmark is a dictionary then get the x, y, visibility from the dictionary
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
            #Required map landmarks are taken

            #left side landmarks are calculated
            left_shoulder, v1 = get_landmark(11); 
            left_elbow, v2 = get_landmark(13); 
            left_wrist, v3 = get_landmark(15)
            left_hip, v4 = get_landmark(23); 
            left_knee, v5 = get_landmark(25); 
            left_ankle, v6 = get_landmark(27)

            #right side landmarks are calculated
            right_shoulder, v7 = get_landmark(12); 
            right_elbow, v8 = get_landmark(14); 
            right_wrist, v9 = get_landmark(16)
            right_hip, v10 = get_landmark(24); 
            right_knee, v11 = get_landmark(26); 
            right_ankle, v12 = get_landmark(28)

            # Check upper body visibility (Required for counting)
            left_upper_visible = all(v > 0.4 for v in [v1, v2, v3])
            right_upper_visible = all(v > 0.4 for v in [v7, v8, v9])
            
            # Check lower body visibility (Optional for form feedback)
            left_lower_visible = all(v > 0.4 for v in [v4, v5, v6])
            right_lower_visible = all(v > 0.4 for v in [v10, v11, v12])

            left_visible = left_upper_visible
            right_visible = right_upper_visible

            #angles are calculated based on the visible side
            left_eb_angle = right_eb_angle = left_kn_angle = right_kn_angle = avg_spine = 0
            
            # Use average for elbow state
            avg_eb_angle = 0

            #if both sides are visible then calculate the angles for both the sides
            if left_visible and right_visible:
                left_eb_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
                right_eb_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
                avg_eb_angle = (left_eb_angle + right_eb_angle) / 2
                
                left_kn_angle = calculate_angle(left_hip, left_knee, left_ankle)
                right_kn_angle = calculate_angle(right_hip, right_knee, right_ankle)
                avg_spine = (calculate_angle(left_shoulder, left_hip, left_ankle) + 
                             calculate_angle(right_shoulder, right_hip, right_ankle)) / 2

            #if only left side is visible then calculate the angles for the left side
            elif left_visible:
                left_eb_angle = right_eb_angle = avg_eb_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
                left_kn_angle = right_kn_angle = calculate_angle(left_hip, left_knee, left_ankle)
                avg_spine = calculate_angle(left_shoulder, left_hip, left_ankle)

            #if only right side is visible then calculate the angles for the right side
            elif right_visible:
                right_eb_angle = left_eb_angle = avg_eb_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
                right_kn_angle = left_kn_angle = calculate_angle(right_hip, right_knee, right_ankle)
                avg_spine = calculate_angle(right_shoulder, right_hip, right_ankle)

            #if no side is visible, give the rep count as it is, and send a message to the frontend
            else:
                accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0
                return {
                    "msg": "Object not in frame", 
                    "reps": self.correct_reps, 
                    "total_reps": self.total_reps, 
                    "accuracy": round(accuracy, 2),
                    "feedback": {"form": "Object not in frame/Low visibility"}
                }

            # ---------------- ORIENTATION & CALIBRATION ----------------
            
            # Orientation check: For pushups, user MUST be horizontal
            # shoulder-to-hip Y difference should be smaller than X difference
            # (In a sitting position, Y difference is large)
            is_horizontal = abs(left_shoulder[1] - left_hip[1]) < abs(left_shoulder[0] - left_hip[0])
            
            if not is_horizontal:
                self.stable_frames = 0 # reset if they stand up
                return {
                    "reps": self.correct_reps,
                    "total_reps": self.total_reps,
                    "accuracy": round(self.accuracy, 2),
                    "feedback": {"form": "Please get into horizontal pushup position"},
                    "msg": "Waiting for proper orientation"
                }

            # Calibration: Hold steady 'Up' position for ~2 seconds (20 frames)
            if not self.is_calibrated:
                is_ready_pos = avg_eb_angle >= 150 # Mostly straight arms
                
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
                        "feedback": {"form": f"Hold steady for {max(0, (20 - self.stable_frames)//10)}s..."},
                        "msg": "Calibrating"
                    }

            # ---------------- POSITION CHECKS ----------------
            is_down = avg_eb_angle <= 110
            is_up = avg_eb_angle >= 155
            
            # form checks (Slightly relaxed)
            knees_ok = (left_kn_angle >= 150 or v5 < 0.5) and (right_kn_angle >= 150 or v11 < 0.5)
            body_ok = avg_spine >= 140

            #set the feedback, for form, knee angle, and elbow angle
            self.form_feedback = "Good posture" if body_ok else "Keep your body straight"
            self.knee_feedback = "Knees straight" if knees_ok else "Straighten your knees"
            self.elbow_feedback = "Good depth" if is_down else "Lower down"

            #machine state logic
            if self.pushup_state == "up":
                if avg_eb_angle < 145: # Started moving down (partial attempt)
                    self.pushup_state = "down"
                    self.rep_valid = True
                    self.hit_bottom = False # Haven't hit target depth yet

                    if not (body_ok and knees_ok):
                        self.rep_valid = False

            elif self.pushup_state == "down":
                if is_down:
                    self.hit_bottom = True

                if not (body_ok and knees_ok):
                    self.rep_valid = False

                if is_up:
                    self.pushup_state = "up"
                    self.total_reps += 1

                    if self.hit_bottom and self.rep_valid:
                        self.correct_reps += 1
                    
                    self.hit_bottom = False
                    self.rep_valid = True

            #calculate accuracy safely
            self.accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0

            return {
                "reps": self.correct_reps,
                "total_reps": self.total_reps,
                "accuracy": round(self.accuracy, 2),
                "state": self.pushup_state,
                "feedback": {
                    "form": self.form_feedback,
                    "knee": self.knee_feedback,
                    "elbow": self.elbow_feedback
                },
                "angles": {
                    "elbow_avg": int(avg_eb_angle),
                    "spine": int(avg_spine),
                    "left_knee": int(left_kn_angle),
                    "right_knee": int(right_kn_angle)
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

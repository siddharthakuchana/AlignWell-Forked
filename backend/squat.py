from angle_utils import calculate_angle

class SquatTracker:
    #constructor that gives the initial states, feedback and rep count initially set to 0
    def __init__(self):
        self.correct_reps = 0
        self.total_reps = 0
        self.accuracy = 0
        self.squat_state = "up"
        self.form_feedback = ""
        self.knee_feedback = ""
        self.posture_feedback = ""

        #extra feedback for strict squat validation
        self.symmetry_feedback = ""
        self.knee_cave_feedback = ""

        #these variables are used to validate a rep properly (to calculate accuracy)
        self.rep_valid = True
        self.hit_bottom = False

        # Calibration / Stable start
        self.is_calibrated = False
        self.stable_frames = 0

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
            left_hip, v2 = get_landmark(23)
            left_knee, v3 = get_landmark(25)
            left_ankle, v4 = get_landmark(27)

            # Right side landmarks are calculated
            right_shoulder, v5 = get_landmark(12)
            right_hip, v6 = get_landmark(24)
            right_knee, v7 = get_landmark(26)
            right_ankle, v8 = get_landmark(28)

            #check the visibility scores to see if the that side(left/right) is visible 
            left_visible = all(v > 0.6 for v in [v1, v2, v3, v4])
            right_visible = all(v > 0.6 for v in [v5, v6, v7, v8])

            #if no side is visible, give the rep count as it is, and send a message to the frontend
            if not left_visible and not right_visible:
                accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0
                return {
                    "msg": "Body not fully visible", 
                    "reps": self.correct_reps, 
                    "total_reps": self.total_reps, 
                    "accuracy": round(accuracy, 2),
                    "feedback": {"posture": "Body not visible"}
                }

            #angles are calculated based on the visible side
            left_knee_angle = right_knee_angle = 0
            left_hip_angle = right_hip_angle = 0

            #if both sides are visible then calculate the angles for both the sides
            if left_visible and right_visible:
                # Knee angle: Hip - Knee - Ankle
                left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
                right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)

                # Hip angle: Shoulder - Hip - Knee (for posture)
                left_hip_angle = calculate_angle(left_shoulder, left_hip, left_knee)
                right_hip_angle = calculate_angle(right_shoulder, right_hip, right_knee)

            #if only left side is visible then calculate the angles for the left side
            elif left_visible:
                left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
                right_knee_angle = left_knee_angle

                left_hip_angle = calculate_angle(left_shoulder, left_hip, left_knee)
                right_hip_angle = left_hip_angle

            #if only right side is visible then calculate the angles for the right side
            elif right_visible:
                right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)
                left_knee_angle = right_knee_angle

                right_hip_angle = calculate_angle(right_shoulder, right_hip, right_knee)
                left_hip_angle = right_hip_angle

            # ---------------- Practical squat rules ----------------
            avg_knee_angle = (left_knee_angle + right_knee_angle) / 2
            
            # ---------------- CALIBRATION ----------------
            
            # Calibration: Hold steady 'Up' position for ~2 seconds (20 frames)
            if not self.is_calibrated:
                is_ready_pos = avg_knee_angle >= 160 # Fully standing
                
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
                        "feedback": {"posture": f"Stand steady for {max(0, (20 - self.stable_frames)//10)}s..."},
                        "msg": "Calibrating"
                    }

            # ---------------- POSITION CHECKS ----------------
            # Squat depth (using average)
            is_down = avg_knee_angle <= 120

            # Standing up (using average)
            is_up = avg_knee_angle >= 155

            # Posture check: keep chest up (hip angle should not collapse too much)
            posture_ok = left_hip_angle >= 50 and right_hip_angle >= 50

            # Symmetry check: both legs should squat similarly
            # if difference is too much, user is leaning / shifting weight to one side
            symmetry_ok = abs(left_knee_angle - right_knee_angle) <= 15

            # Knee cave check (valgus): knee should not go too inward compared to ankle
            # (simple rule using x-coordinates)
            # Left leg: knee should not be too far inside the ankle
            # Right leg: knee should not be too far inside the ankle
            knee_cave_ok = True
            if left_visible:
                if left_knee[0] < left_ankle[0] - 0.03:
                    knee_cave_ok = False
            if right_visible:
                if right_knee[0] > right_ankle[0] + 0.03:
                    knee_cave_ok = False

            # ---------------- Feedback ----------------

            self.knee_feedback = "Good depth" if is_down else "Go lower"
            if is_up:
                self.knee_feedback = "Stand fully"

            self.posture_feedback = "Good posture" if posture_ok else "Keep chest up"
            self.symmetry_feedback = "Balanced squat" if symmetry_ok else "Do not lean to one side"
            self.knee_cave_feedback = "Knees aligned" if knee_cave_ok else "Do not let knees cave in"

            #machine state logic
            if self.squat_state == "up":
                if avg_knee_angle < 150: # Started squatting (partial attempt)
                    self.squat_state = "down"
                    self.rep_valid = True
                    self.hit_bottom = False

                    if not (posture_ok and symmetry_ok and knee_cave_ok):
                        self.rep_valid = False

            elif self.squat_state == "down":
                if is_down:
                    self.hit_bottom = True

                if not (posture_ok and symmetry_ok and knee_cave_ok):
                    self.rep_valid = False

                if is_up:
                    self.squat_state = "up"
                    self.total_reps += 1

                    if self.hit_bottom and self.rep_valid:
                        self.correct_reps += 1
                    
                    self.hit_bottom = False
                    self.rep_valid = True

            #calculate accuracy safely (avoid division by zero)
            self.accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0

            return {
                "reps": self.correct_reps,
                "total_reps": self.total_reps,
                "accuracy": round(self.accuracy, 2),
                "state": self.squat_state,
                "feedback": {
                    "knee": self.knee_feedback,
                    "posture": self.posture_feedback,
                    "symmetry": self.symmetry_feedback,
                    "knee_cave": self.knee_cave_feedback
                },
                "angles": {
                    "left_knee": int(left_knee_angle),
                    "right_knee": int(right_knee_angle),
                    "left_hip": int(left_hip_angle),
                    "right_hip": int(right_hip_angle)
                }
            }

        except Exception as e:
            accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0
            return {
                "msg": f"Error: {str(e)}", 
                "reps": self.correct_reps, 
                "total_reps": self.total_reps, 
                "accuracy": round(accuracy, 2),
                "feedback": {"posture": "Processing error"}
            }

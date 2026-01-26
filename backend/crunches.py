from angle_utils import calculate_angle

class CrunchesTracker:
    #constructor that gives the initial states, feedback and rep count initially set to 0
    def __init__(self):
        self.correct_reps = 0
        self.total_reps = 0
        self.accuracy = 0
        self.crunch_state = "down" # Shoulders on ground
        self.form_feedback = ""
        self.knee_feedback = ""

        #these variables are used to validate a rep properly (to calculate accuracy)
        self.rep_valid = True
        self.hit_top = False

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

            #left side landmarks are calculated
            left_shoulder, v1 = get_landmark(11)
            left_hip, v2 = get_landmark(23)
            left_knee, v3 = get_landmark(25)
            left_ankle, v4 = get_landmark(27)

            #right side landmarks are calculated
            right_shoulder, v5 = get_landmark(12)
            right_hip, v6 = get_landmark(24)
            right_knee, v7 = get_landmark(26)
            right_ankle, v8 = get_landmark(28)

            #check the visibility scores to see if the that side(left/right) is visible 
            left_visible = all(v > 0.6 for v in [v1, v2, v3])
            right_visible = all(v > 0.6 for v in [v5, v6, v7])

            #if no side is visible, give the rep count as it is, and send a message to the frontend
            if not left_visible and not right_visible:
                accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0
                return {"msg": "Body not fully visible", "reps": self.correct_reps, "total_reps": self.total_reps, "accuracy": round(accuracy, 2)}

            #angles are calculated based on the visible side
            left_hip_angle = right_hip_angle = 180
            left_knee_angle = right_knee_angle = 180

            #if both sides are visible then calculate the angles for both the sides
            if left_visible and right_visible:
                # Hip angle: Shoulder - Hip - Knee (crunch movement)
                left_hip_angle = calculate_angle(left_shoulder, left_hip, left_knee)
                right_hip_angle = calculate_angle(right_shoulder, right_hip, right_knee)

                # Knee angle: Hip - Knee - Ankle (knee should stay bent)
                # only calculate if ankle is also visible enough
                if v4 > 0.6:
                    left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
                if v8 > 0.6:
                    right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)

            #if only left side is visible then calculate the angles for the left side
            elif left_visible:
                left_hip_angle = right_hip_angle = calculate_angle(left_shoulder, left_hip, left_knee)

                if v4 > 0.6:
                    left_knee_angle = right_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)

            #if only right side is visible then calculate the angles for the right side
            elif right_visible:
                right_hip_angle = left_hip_angle = calculate_angle(right_shoulder, right_hip, right_knee)

                if v8 > 0.6:
                    right_knee_angle = left_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)

            # Crunches Logic:
            # Hip angle reduces when crunching up (shoulders move towards knees)
            avg_hip_angle = (left_hip_angle + right_hip_angle) / 2

            # Knee angle rule:
            # knee should stay bent, so knee angle should not become too straight
            avg_knee_angle = (left_knee_angle + right_knee_angle) / 2

            # Strict thresholds (you can tune later)
            is_up = avg_hip_angle <= 100
            is_down = avg_hip_angle >= 130

            # Extra strict check: too much movement / wrong detection
            too_high = avg_hip_angle < 60

            # Knee strict check (avoid straightening legs too much)
            # if ankle is not visible, knee angle will be ~180 default, so we handle it safely
            knee_check_available = (left_knee_angle != 180 or right_knee_angle != 180)
            knees_ok = True
            if knee_check_available:
                knees_ok = avg_knee_angle <= 140

            #set the feedback, for form
            if is_up:
                self.form_feedback = "Good crunch"
            elif is_down:
                self.form_feedback = "Crunch higher"
            else:
                self.form_feedback = "Keep moving"

            if too_high:
                self.form_feedback = "Too high (control it)"

            #set the feedback, for knee
            if knee_check_available:
                self.knee_feedback = "Knees bent" if knees_ok else "Keep knees bent"
            else:
                self.knee_feedback = "Knees not visible"

            #machine state is set to up, then this is when the rep validation starts
            if self.crunch_state == "down":
                if is_up:
                    self.crunch_state = "up"

                    #new rep attempt started so reset the validation flags
                    self.rep_valid = True
                    self.hit_top = False

                    #mark top only when proper up position is reached
                    if is_up:
                        self.hit_top = True

                    #if too high, mark rep invalid
                    if too_high:
                        self.rep_valid = False

                    #if knees are not ok, mark rep invalid
                    if not knees_ok:
                        self.rep_valid = False

            #if the state is up, keep checking if the form is correct during the rep
            elif self.crunch_state == "up":

                #if top position is reached, mark hit_top true
                if is_up:
                    self.hit_top = True

                #if crunch goes too high, mark rep invalid
                if too_high:
                    self.rep_valid = False

                #if knees are not ok, mark rep invalid
                if not knees_ok:
                    self.rep_valid = False

                #when state is back to down, it means the person completed the crunch rep
                if is_down:
                    self.crunch_state = "down"
                    self.total_reps += 1

                    #if the rep was valid throughout and top was reached, count it as correct rep
                    if self.hit_top and self.rep_valid:
                        self.correct_reps += 1

                    #reset flags for next rep
                    self.hit_top = False
                    self.rep_valid = True

            #calculate accuracy safely (avoid division by zero)
            self.accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0

            return {
                "reps": self.correct_reps,
                "total_reps": self.total_reps,
                "accuracy": round(self.accuracy, 2),
                "state": self.crunch_state,
                "feedback": {
                    "form": self.form_feedback,
                    "knee": self.knee_feedback
                },
                "angles": {
                    "left_hip": int(left_hip_angle),
                    "right_hip": int(right_hip_angle),
                    "hip_avg": int(avg_hip_angle),
                    "left_knee": int(left_knee_angle),
                    "right_knee": int(right_knee_angle),
                    "knee_avg": int(avg_knee_angle)
                }
            }

        except Exception as e:
            accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0
            return {"msg": f"Error: {str(e)}", "reps": self.correct_reps, "total_reps": self.total_reps, "accuracy": round(accuracy, 2)}

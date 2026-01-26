from .angle_utils import calculate_angle

class ShoulderRaiseTracker:
    #constructor that gives the initial states, feedback and rep count initially set to 0
    def __init__(self):
        self.correct_reps = 0
        self.total_reps = 0
        self.accuracy = 0
        self.raise_state = "down" # Arms at sides
        self.form_feedback = ""
        self.height_feedback = ""

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

            # Left side landmarks are calculated
            left_shoulder, v1 = get_landmark(11)
            left_elbow, v2 = get_landmark(13)
            left_hip, v3 = get_landmark(23)

            # Right side landmarks are calculated
            right_shoulder, v4 = get_landmark(12)
            right_elbow, v5 = get_landmark(14)
            right_hip, v6 = get_landmark(24)

            #check the visibility scores to see if the that side(left/right) is visible 
            left_visible = all(v > 0.6 for v in [v1, v2, v3])
            right_visible = all(v > 0.6 for v in [v4, v5, v6])

            #angles are calculated based on the visible side
            left_sh_angle = right_sh_angle = 0

            # Angle: Hip - Shoulder - Elbow
            # 0 degrees = arm straight down
            # 90 degrees = arm at shoulder height

            #if both sides are visible then calculate the angles for both the sides
            if left_visible and right_visible:
                left_sh_angle = calculate_angle(left_hip, left_shoulder, left_elbow)
                right_sh_angle = calculate_angle(right_hip, right_shoulder, right_elbow)

            #if only left side is visible then calculate the angles for the left side
            elif left_visible:
                left_sh_angle = right_sh_angle = calculate_angle(left_hip, left_shoulder, left_elbow)

            #if only right side is visible then calculate the angles for the right side
            elif right_visible:
                right_sh_angle = left_sh_angle = calculate_angle(right_hip, right_shoulder, right_elbow)

            #if no side is visible, give the rep count as it is, and send a message to the frontend
            else:
                accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0
                return {"msg": "Upper body not fully visible", "reps": self.correct_reps, "total_reps": self.total_reps, "accuracy": round(accuracy, 2)}

            # Form Judging (strict thresholds)
            # Down: Arms at sides (< 25 degrees)
            is_down = left_sh_angle <= 25 and right_sh_angle <= 25

            # Up: Arms at shoulder height (~90 degrees)
            is_up = left_sh_angle >= 80 and right_sh_angle >= 80

            # Extra strict check: going too high (trap engagement / cheating)
            too_high = left_sh_angle > 120 or right_sh_angle > 120

            #set the feedback, for form
            if is_up:
                self.height_feedback = "Good height"
            elif is_down:
                self.height_feedback = "Lift up"
            else:
                self.height_feedback = "Control movement"

            if too_high:
                self.form_feedback = "Too high (avoid shrugging)"
            else:
                self.form_feedback = "Good form"

            #machine state is set to up, then this is when the rep validation starts
            if self.raise_state == "down":
                if is_up:
                    self.raise_state = "up"

                    #new rep attempt started so reset the validation flags
                    self.rep_valid = True
                    self.hit_top = False

                    #mark top only when proper up position is reached
                    if is_up:
                        self.hit_top = True

                    #if too high, mark rep invalid
                    if too_high:
                        self.rep_valid = False

            #if the state is up, keep checking if the form is correct during the rep
            elif self.raise_state == "up":

                #if top position is reached, mark hit_top true
                if is_up:
                    self.hit_top = True

                #if raise goes too high, mark rep invalid
                if too_high:
                    self.rep_valid = False

                #when state is back to down, it means the person completed the shoulder raise rep
                if is_down:
                    self.raise_state = "down"
                    self.total_reps += 1

                    #if the rep was valid throughout and top was reached, count it as correct rep
                    if self.hit_top and self.rep_valid:
                        self.correct_reps += 1

                    #reset flags for next rep
                    self.hit_top = False
                    self.rep_valid = True

            #calculate accuracy safely (avoid division by zero)
            self.accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0

            #average shoulder angle for UI
            avg_shoulder = (left_sh_angle + right_sh_angle) / 2

            return {
                "reps": self.correct_reps,
                "total_reps": self.total_reps,
                "accuracy": round(self.accuracy, 2),
                "state": self.raise_state,
                "feedback": {
                    "form": self.form_feedback,
                    "height": self.height_feedback
                },
                "angles": {
                    "left_shoulder": int(left_sh_angle),
                    "right_shoulder": int(right_sh_angle),
                    "shoulder_avg": int(avg_shoulder)
                }
            }

        except Exception as e:
            accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0
            return {"msg": f"Error: {str(e)}", "reps": self.correct_reps, "total_reps": self.total_reps, "accuracy": round(accuracy, 2)}

from .angle_utils import calculate_angle

class BenchPressTracker:
    #constructor that gives the initial states, feedback and rep count initially set to 0
    def __init__(self):
        self.correct_reps = 0
        self.total_reps = 0
        self.accuracy = 0
        self.bench_state = "up"  # Usually unrack at top
        self.form_feedback = ""
        self.elbow_feedback = ""

        #these variables are used to validate a rep properly (to calculate accuracy)
        self.rep_valid = True
        self.hit_bottom = False

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
                return {"msg": "Upper body not fully visible", "reps": self.correct_reps, "total_reps": self.total_reps, "accuracy": round(accuracy, 2)}

            # Form Judging (strict thresholds)
            # Up: Arms extended (lockout)
            is_up = left_elbow_angle >= 170 and right_elbow_angle >= 170

            # Down: Arms bent (bar near chest)
            is_down = left_elbow_angle <= 100 and right_elbow_angle <= 100

            # Extra strict check: too deep (elbow too closed)
            too_deep = left_elbow_angle < 60 or right_elbow_angle < 60

            #set the feedback, for elbow angle
            if is_down:
                self.elbow_feedback = "Good depth"
            elif is_up:
                self.elbow_feedback = "Locked out"
            else:
                self.elbow_feedback = "Full range needed"

            if too_deep:
                self.form_feedback = "Too deep (control the bar)"
            else:
                self.form_feedback = "Good form"

            #machine state is set to down, then this is when the rep validation starts
            if self.bench_state == "up":
                if is_down:
                    self.bench_state = "down"

                    #new rep attempt started so reset the validation flags
                    self.rep_valid = True
                    self.hit_bottom = False

                    #mark bottom only when proper down depth is reached
                    if is_down:
                        self.hit_bottom = True

                    #if too deep, mark rep invalid
                    if too_deep:
                        self.rep_valid = False

            #if the state is down, keep checking if the form is correct during the rep
            elif self.bench_state == "down":

                #if bottom depth is reached, mark hit_bottom true
                if is_down:
                    self.hit_bottom = True

                #if bar goes too deep, mark rep invalid
                if too_deep:
                    self.rep_valid = False

                #when state is back to up, it means the person completed the bench press rep
                if is_up:
                    self.bench_state = "up"
                    self.total_reps += 1

                    #if the rep was valid throughout and bottom was reached, count it as correct rep
                    if self.hit_bottom and self.rep_valid:
                        self.correct_reps += 1

                    #reset flags for next rep
                    self.hit_bottom = False
                    self.rep_valid = True

            #calculate accuracy safely (avoid division by zero)
            self.accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0

            return {
                "reps": self.correct_reps,
                "total_reps": self.total_reps,
                "accuracy": round(self.accuracy, 2),
                "state": self.bench_state,
                "feedback": {
                    "form": self.form_feedback,
                    "elbow": self.elbow_feedback
                },
                "angles": {
                    "left_elbow": int(left_elbow_angle),
                    "right_elbow": int(right_elbow_angle)
                }
            }

        except Exception as e:
            accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0
            return {"msg": f"Error: {str(e)}", "reps": self.correct_reps, "total_reps": self.total_reps, "accuracy": round(accuracy, 2)}

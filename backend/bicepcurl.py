from .angle_utils import calculate_angle

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
            # Down: arms extended (full stretch)
            is_down = left_elbow_angle >= 160 and right_elbow_angle >= 160

            # Up: arms curled (full squeeze)
            is_up = left_elbow_angle <= 60 and right_elbow_angle <= 60

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

            #machine state is set to up, then this is when the rep validation starts
            if self.curl_state == "down":
                if is_up:
                    self.curl_state = "up"

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
            elif self.curl_state == "up":

                #if top position is reached, mark hit_top true
                if is_up:
                    self.hit_top = True

                #if curl goes too high, mark rep invalid
                if too_high:
                    self.rep_valid = False

                #when state is back to down, it means the person completed the curl rep
                if is_down:
                    self.curl_state = "down"
                    self.total_reps += 1

                    #if the rep was valid throughout and top was reached, count it as correct rep
                    if self.hit_top and self.rep_valid:
                        self.correct_reps += 1

                    #reset flags for next rep
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
            return {"msg": f"Error: {str(e)}", "reps": self.correct_reps, "total_reps": self.total_reps, "accuracy": round(accuracy, 2)}

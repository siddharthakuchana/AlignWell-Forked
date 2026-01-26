from .angle_utils import calculate_angle

class DeadliftTracker:
    #constructor that gives the initial states, feedback and rep count initially set to 0
    def __init__(self):
        self.correct_reps = 0
        self.total_reps = 0
        self.accuracy = 0
        self.deadlift_state = "down" # Deadlift starts from the ground usually
        self.form_feedback = ""
        self.posture_feedback = ""
        self.knee_feedback = ""

        #extra strict feedback
        self.symmetry_feedback = ""
        self.hip_hinge_feedback = ""

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
                return {"msg": "Body not fully visible", "reps": self.correct_reps, "total_reps": self.total_reps, "accuracy": round(accuracy, 2)}

            #angles are calculated based on the visible side
            left_hip_angle = right_hip_angle = 0
            left_knee_angle = right_knee_angle = 0

            #if both sides are visible then calculate the angles for both the sides
            if left_visible and right_visible:
                # Hip angle: Shoulder - Hip - Knee
                left_hip_angle = calculate_angle(left_shoulder, left_hip, left_knee)
                right_hip_angle = calculate_angle(right_shoulder, right_hip, right_knee)

                # Knee angle: Hip - Knee - Ankle
                left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
                right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)

            #if only left side is visible then calculate the angles for the left side
            elif left_visible:
                left_hip_angle = right_hip_angle = calculate_angle(left_shoulder, left_hip, left_knee)
                left_knee_angle = right_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)

            #if only right side is visible then calculate the angles for the right side
            elif right_visible:
                right_hip_angle = left_hip_angle = calculate_angle(right_shoulder, right_hip, right_knee)
                right_knee_angle = left_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)

            # ---------------- Strict deadlift rules ----------------

            # Up position: Hips extended, knees extended
            is_up = (left_hip_angle >= 165 and right_hip_angle >= 165 and
                     left_knee_angle >= 165 and right_knee_angle >= 165)

            # Down position: hip hinge (hip angle smaller)
            is_down = left_hip_angle <= 140 and right_hip_angle <= 140

            # Hip hinge rule: user must actually hinge, not just bend knees
            hip_hinge_ok = left_hip_angle <= 150 and right_hip_angle <= 150

            # Knee rule: do not squat too deep (deadlift is hinge dominant)
            # if knee angle becomes too small, it looks like a squat deadlift
            knees_ok = left_knee_angle >= 90 and right_knee_angle >= 90

            # Symmetry rule: both legs should move similarly
            symmetry_ok = abs(left_knee_angle - right_knee_angle) <= 15 and abs(left_hip_angle - right_hip_angle) <= 15

            # ---------------- Feedback ----------------

            if is_up:
                self.form_feedback = "Good stand"
            elif is_down:
                self.form_feedback = "Drive up"
            else:
                self.form_feedback = "Keep going"

            self.hip_hinge_feedback = "Good hinge" if hip_hinge_ok else "Hinge at hips"
            self.knee_feedback = "Knees ok" if knees_ok else "Do not squat too deep"
            self.symmetry_feedback = "Balanced" if symmetry_ok else "Do not shift weight"

            # Posture feedback (proxy)
            # We cannot truly detect rounded back using only 2D points, so we give a reminder + use symmetry/hinge
            self.posture_feedback = "Keep back straight"

            #machine state is set to up, then this is when the rep validation starts
            if self.deadlift_state == "down":
                if is_up:
                    self.deadlift_state = "up"

                    #new rep attempt started so reset the validation flags
                    self.rep_valid = True
                    self.hit_top = False

                    #mark top only when proper up position is reached
                    if is_up:
                        self.hit_top = True

                    #validate this frame
                    if not (hip_hinge_ok and knees_ok and symmetry_ok):
                        self.rep_valid = False

            #if the state is up, keep checking if the form is correct during the rep
            elif self.deadlift_state == "up":

                #if top position is reached, mark hit_top true
                if is_up:
                    self.hit_top = True

                #if form becomes wrong in any frame, mark rep invalid
                if not (hip_hinge_ok and knees_ok and symmetry_ok):
                    self.rep_valid = False

                #when state is back to down, it means the person completed the deadlift rep
                if is_down:
                    self.deadlift_state = "down"
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
                "state": self.deadlift_state,
                "feedback": {
                    "form": self.form_feedback,
                    "posture": self.posture_feedback,
                    "hinge": self.hip_hinge_feedback,
                    "knee": self.knee_feedback,
                    "symmetry": self.symmetry_feedback
                },
                "angles": {
                    "left_hip": int(left_hip_angle),
                    "right_hip": int(right_hip_angle),
                    "left_knee": int(left_knee_angle),
                    "right_knee": int(right_knee_angle)
                }
            }

        except Exception as e:
            accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0
            return {"msg": f"Error: {str(e)}", "reps": self.correct_reps, "total_reps": self.total_reps, "accuracy": round(accuracy, 2)}

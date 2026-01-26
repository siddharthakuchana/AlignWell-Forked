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

            #check the visibility scores to see if the that side(left/right) is visible 
            left_visible = all(v > 0.6 for v in [v1, v2, v3, v4, v5, v6])
            right_visible = all(v > 0.6 for v in [v7, v8, v9, v10, v11, v12])

            #angles are calculated based on the visible side
            left_eb_angle = right_eb_angle = left_kn_angle = right_kn_angle = avg_spine = 0

            #if both sides are visible then calculate the angles for both the sides
            if left_visible and right_visible:
                left_eb_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
                right_eb_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
                left_kn_angle = calculate_angle(left_hip, left_knee, left_ankle)
                right_kn_angle = calculate_angle(right_hip, right_knee, right_ankle)
                avg_spine = (calculate_angle(left_shoulder, left_hip, left_ankle) + 
                             calculate_angle(right_shoulder, right_hip, right_ankle)) / 2

            #if only left side is visible then calculate the angles for the left side
            elif left_visible:
                left_eb_angle = right_eb_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
                left_kn_angle = right_kn_angle = calculate_angle(left_hip, left_knee, left_ankle)
                avg_spine = calculate_angle(left_shoulder, left_hip, left_ankle)

            #if only right side is visible then calculate the angles for the right side
            elif right_visible:
                right_eb_angle = left_eb_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
                right_kn_angle = left_kn_angle = calculate_angle(right_hip, right_knee, right_ankle)
                avg_spine = calculate_angle(right_shoulder, right_hip, right_ankle)

            #if no side is visible, give the rep count as it is, and send a message to the frontend
            else:
                accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0
                return {"msg": "Object not in frame", "reps": self.correct_reps, "total_reps": self.total_reps, "accuracy": round(accuracy, 2)}

            #angles for up and down
            is_down = left_eb_angle <= 100 and right_eb_angle <= 100
            is_up = left_eb_angle >= 170 and right_eb_angle >= 170
            knees_ok = left_kn_angle >= 160 and right_kn_angle >= 160
            body_ok = avg_spine >= 150

            #set the feedback, for form, knee angle, and elbow angle
            self.form_feedback = "Good posture" if body_ok else "Keep your body straight"
            self.knee_feedback = "Knees straight" if knees_ok else "Straighten your knees"
            self.elbow_feedback = "Good depth" if is_down else "Lower down"

            #machine state is set to down, then this is when the rep validation starts
            if self.pushup_state == "up":
                if is_down:
                    self.pushup_state = "down"

                    #new rep attempt started so reset the validation flags
                    self.rep_valid = True
                    self.hit_bottom = False

                    #immediately validate this frame also
                    if not (body_ok and knees_ok):
                        self.rep_valid = False

            #if the state is down, keep checking if the form is correct during the rep
            elif self.pushup_state == "down":

                #if bottom depth is reached, mark hit_bottom true
                if is_down:
                    self.hit_bottom = True

                #if form becomes wrong in any frame, mark rep as invalid
                if not (body_ok and knees_ok):
                    self.rep_valid = False

                #when state is back to up, it means the person completed the pushup
                if is_up:
                    self.pushup_state = "up"
                    self.total_reps += 1

                    #if the rep was valid throughout and bottom was reached, count it as correct rep
                    if self.hit_bottom and self.rep_valid:
                        self.correct_reps += 1

                    #reset flags for next rep
                    self.hit_bottom = False
                    self.rep_valid = True

            #calculate accuracy safely (avoid division by zero)
            self.accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0

            #return the response to the frontend
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
                    "left_elbow": int(left_eb_angle),
                    "right_elbow": int(right_eb_angle),
                    "spine": int(avg_spine),
                    "left_knee": int(left_kn_angle),
                    "right_knee": int(right_kn_angle)
                }
            }

        except Exception as e:
            accuracy = (self.correct_reps / self.total_reps) * 100 if self.total_reps > 0 else 0
            return {"msg": f"Error: {str(e)}", "reps": self.correct_reps, "total_reps": self.total_reps, "accuracy": round(accuracy, 2)}

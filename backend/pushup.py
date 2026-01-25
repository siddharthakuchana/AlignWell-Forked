from .angle_utils import calculate_angle

class PushupTracker:
    #constructor that gives the initial states, feedback and rep count initially set to 0
    def __init__(self):
        self.rep_count = 0
        self.pushup_state = "up"
        self.form_feedback = ""
        self.knee_feedback = ""
        self.elbow_feedback = ""

    def process(self, landmarks):

        # this is a helper function to get the landmark position and the visibility of the landmark(this ensures if we have to take it into consideration or not)
        def get_landmark(idx):
            lm = landmarks[idx]
            # Handle both object-style and dict-style landmarks
            x = lm.x if hasattr(lm, 'x') else lm.get('x', 0)
            y = lm.y if hasattr(lm, 'y') else lm.get('y', 0)
            v = lm.visibility if hasattr(lm, 'visibility') else lm.get('visibility', 0)
            return [x, y], v

        try:
            #Required map landmarks are taken
            # Left side
            l_shoulder, v1 = get_landmark(11); 
            l_elbow, v2 = get_landmark(13); 
            l_wrist, v3 = get_landmark(15)
            l_hip, v4 = get_landmark(23); 
            l_knee, v5 = get_landmark(25); 
            l_ankle, v6 = get_landmark(27)

            # Right side
            r_shoulder, v7 = get_landmark(12); 
            r_elbow, v8 = get_landmark(14); 
            r_wrist, v9 = get_landmark(16)
            r_hip, v10 = get_landmark(24); 
            r_knee, v11 = get_landmark(26); 
            r_ankle, v12 = get_landmark(28)

            # 2. Check visibility scores
            left_visible = all(v > 0.6 for v in [v1, v2, v3, v4, v5, v6])
            right_visible = all(v > 0.6 for v in [v7, v8, v9, v10, v11, v12])

            # 3. Calculate Angles based on visible side
            l_eb_angle = r_eb_angle = l_kn_angle = r_kn_angle = avg_spine = 0

            if left_visible and right_visible:
                l_eb_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
                r_eb_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
                l_kn_angle = calculate_angle(l_hip, l_knee, l_ankle)
                r_kn_angle = calculate_angle(r_hip, r_knee, r_ankle)
                avg_spine = (calculate_angle(l_shoulder, l_hip, l_ankle) + 
                             calculate_angle(r_shoulder, r_hip, r_ankle)) / 2
            elif left_visible:
                l_eb_angle = r_eb_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
                l_kn_angle = r_kn_angle = calculate_angle(l_hip, l_knee, l_ankle)
                avg_spine = calculate_angle(l_shoulder, l_hip, l_ankle)
            elif right_visible:
                r_eb_angle = l_eb_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
                r_kn_angle = l_kn_angle = calculate_angle(r_hip, r_knee, r_ankle)
                avg_spine = calculate_angle(r_shoulder, r_hip, r_ankle)
            else:
                return {"msg": "Object not in frame", "reps": self.rep_count}

            # 4. Form Judging (using user's specific rules)
            is_down = l_eb_angle < 100 and r_eb_angle < 100
            is_up = l_eb_angle > 170 and r_eb_angle > 170
            knees_ok = l_kn_angle > 160 and r_kn_angle > 160
            body_ok = avg_spine > 150

            # Set Feedback
            self.form_feedback = "Good posture" if body_ok else "Keep your body straight"
            self.knee_feedback = "Knees straight" if knees_ok else "Straighten your knees"
            self.elbow_feedback = "Good depth" if is_down else "Lower down"

            # 5. State Machine for counting reps
            if is_down and body_ok and knees_ok and self.pushup_state == "up":
                self.pushup_state = "down"
            elif is_up and self.pushup_state == "down":
                self.pushup_state = "up"
                self.rep_count += 1

            return {
                "reps": self.rep_count,
                "state": self.pushup_state,
                "feedback": {
                    "form": self.form_feedback,
                    "knee": self.knee_feedback,
                    "elbow": self.elbow_feedback
                },
                "angles": {
                    "elbow": int(l_eb_angle),
                    "spine": int(avg_spine),
                    "knee": int(l_kn_angle)
                }
            }

        except Exception as e:
            return {"msg": f"Error: {str(e)}", "reps": self.rep_count}

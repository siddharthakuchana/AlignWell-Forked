from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import cv2
import numpy as np
import base64
import json
import mediapipe as mp

from pushup import PushupTracker
from squat import SquatTracker
from benchpress import BenchPressTracker
from bicepcurl import BicepCurlTracker
from crunches import CrunchesTracker
from deadlift import DeadliftTracker
from shoulderraise import ShoulderRaiseTracker

app = FastAPI()

# MediaPipe Pose
mp_pose = mp.solutions.pose
pose_model = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

@app.get("/")
def welcome():
    return {"status": "online", "message": "AlignWell Backend is running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ Client connected")

    tracker = None
    current_exercise = None

    try:
        while True:
            data = await websocket.receive_text()
            
            # ---------- TRY JSON ----------
            try:
                message = json.loads(data)
                is_json = True
            except:
                is_json = False

            # ---------- RESET ACTION ----------
            if is_json and message.get("action") == "reset":
                print(f"🔄 Resetting {current_exercise} tracker")
                if current_exercise == "pushup":
                    tracker = PushupTracker()
                elif current_exercise == "squat":
                    tracker = SquatTracker()
                elif current_exercise == "benchpress":
                    tracker = BenchPressTracker()
                elif current_exercise == "bicepcurl":
                    tracker = BicepCurlTracker()
                elif current_exercise == "crunches":
                    tracker = CrunchesTracker()
                elif current_exercise == "deadlift":
                    tracker = DeadliftTracker()
                elif current_exercise == "shoulderraise":
                    tracker = ShoulderRaiseTracker()
                
                await websocket.send_text(json.dumps({
                    "status": "ready",
                    "message": "Stats reset",
                    "reps": 0,
                    "total_reps": 0,
                    "accuracy": 0
                }))
                continue

            # ---------- EXERCISE SELECT ----------
            if is_json and "exercise" in message:
                ex_type = message["exercise"]
                
                if ex_type == current_exercise and tracker is not None:
                    print(f"🔄 {ex_type} already active - keeping state")
                    await websocket.send_text(json.dumps({
                        "status": "ready",
                        "message": f"{ex_type.capitalize()} tracker resumed"
                    }))
                else:
                    current_exercise = ex_type
                    print(f"🏋 Switching to: {ex_type}")

                    if ex_type == "pushup":
                        tracker = PushupTracker()
                    elif ex_type == "squat":
                        tracker = SquatTracker()
                    elif ex_type == "benchpress":
                        tracker = BenchPressTracker()
                    elif ex_type == "bicepcurl":
                        tracker = BicepCurlTracker()
                    elif ex_type == "crunches":
                        tracker = CrunchesTracker()
                    elif ex_type == "deadlift":
                        tracker = DeadliftTracker()
                    elif ex_type == "shoulderraise":
                        tracker = ShoulderRaiseTracker()
                    else:
                        current_exercise = None
                        tracker = None
                        await websocket.send_text(json.dumps({
                            "status": "error",
                            "message": f"Exercise '{ex_type}' not supported"
                        }))
                        continue

                    await websocket.send_text(json.dumps({
                        "status": "ready",
                        "message": f"{ex_type.capitalize()} tracker started"
                    }))
                continue

            # ---------- FRAME ----------
            if tracker is None:
                continue

            frame_b64 = data
            if "," in frame_b64:
                frame_b64 = frame_b64.split(",")[1]

            try:
                img_bytes = base64.b64decode(frame_b64)
                nparr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is None:
                    continue

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose_model.process(rgb)

                if results.pose_landmarks:
                    landmarks_for_ui = [
                        {"x": lm.x, "y": lm.y}
                        for lm in results.pose_landmarks.landmark
                    ]

                    response = tracker.process(results.pose_landmarks.landmark)
                    response["landmarks"] = landmarks_for_ui
                    response["exercise"] = current_exercise

                    await websocket.send_text(json.dumps(response))
                    # print("📤 processed frame")
                else:
                    # Always send current reps even if no person detected
                    await websocket.send_text(json.dumps({
                        "status": "nodetect",
                        "reps": getattr(tracker, 'correct_reps', 0),
                        "total_reps": getattr(tracker, 'total_reps', 0),
                        "feedback": {"form": "No person detected"},
                        "landmarks": []
                    }))

            except Exception as e:
                print("❌ Frame error:", e)
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "message": "Frame processing failed"
                }))

    except WebSocketDisconnect:
        print("⚠ Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")

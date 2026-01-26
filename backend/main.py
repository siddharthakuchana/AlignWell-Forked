from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import cv2
import numpy as np
import base64
import json
import mediapipe as mp
from pushup import PushupTracker

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

    try:
        while True:
            data = await websocket.receive_text()
            print("📥 data received")

            # ---------- TRY JSON ----------
            try:
                message = json.loads(data)
                is_json = True
            except:
                is_json = False

            # ---------- EXERCISE SELECT ----------
            if is_json and "exercise" in message:
                ex_type = message["exercise"]
                print("🏋 Exercise:", ex_type)

                if ex_type == "pushup":
                    tracker = PushupTracker()
                    await websocket.send_text(json.dumps({
                        "status": "ready",
                        "message": "Pushup counter started"
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "status": "error",
                        "message": "Exercise not supported"
                    }))
                continue

            # ---------- FRAME ----------
            if tracker is None:
                await websocket.send_text(json.dumps({
                    "status": "waiting",
                    "message": "Select exercise first"
                }))
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

                print("🟢 pose detected:", results.pose_landmarks is not None)

                if results.pose_landmarks:
                    landmarks_for_ui = [
                        {"x": lm.x, "y": lm.y}
                        for lm in results.pose_landmarks.landmark
                    ]

                    response = tracker.process(results.pose_landmarks.landmark)
                    response["landmarks"] = landmarks_for_ui

                    await websocket.send_text(json.dumps(response))
                    print("📤 sent landmarks")

                else:
                    await websocket.send_text(json.dumps({
                        "status": "nodetect",
                        "message": "No person detected",
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

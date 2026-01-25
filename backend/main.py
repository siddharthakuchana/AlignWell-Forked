from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import cv2
import numpy as np
import base64
import json
import mediapipe as mp
from .pushup import PushupTracker

app = FastAPI()

# Global MediaPipe setup
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
    print("Client connected")
    
    # This stores the current exercise session
    tracker = None

    try:
        while True:
            # Receive data from frontend
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle Exercise Selection/Reset
            if "exercise" in message:
                ex_type = message["exercise"]
                if ex_type == "pushup":
                    tracker = PushupTracker()
                    await websocket.send_text(json.dumps({"status": "ready", "msg": "Pushup counter started"}))
                else:
                    await websocket.send_text(json.dumps({"status": "error", "msg": f"Exercise '{ex_type}' not supported yet"}))
                continue

            # handles the image, if the tracker is none, it means no exercise is selected
            if tracker is None:
                await websocket.send_text(json.dumps({"status": "waiting", "msg": "Please select an exercise first"}))
                continue

            if "image" not in message:
                continue

            # Decode image
            b64_str = message["image"]
            if "," in b64_str:
                b64_str = b64_str.split(",")[1]

            try:
                #Image first decoded from base64 and then converted to numpy array, then converted to opencv2 image
                img_data = base64.b64decode(b64_str)
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is None:
                    continue

                #the decoded frame is then passed to mediapipe model converted into RGB format
                results = pose_model.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                #if the landmarks are detected, then pass them to the tracker
                if results.pose_landmarks:
                    #pass landmarks to the track using websocket
                    response = tracker.process(results.pose_landmarks.landmark)
                    await websocket.send_text(json.dumps(response))
                else:
                    await websocket.send_text(json.dumps({"msg": "No person detected"}))

            except Exception as e:
                print(f"Frame processing error: {e}")
                await websocket.send_text(json.dumps({"status": "error", "msg": "Frame processing failed"}))

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")

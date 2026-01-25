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
    #accept the websocket connection
    await websocket.accept()
    print("Client connected")

    #tracker is used to store the exercise session, inititally its None
    tracker = None

    try:
        while True:
            #Recieves the data from the frontend
            data = await websocket.recieve_text()
            message = json.loads(data)

            #handles if the exercise is in the message
            if exercise in "message":
                ex_type = message['exercise']
                if ex_type == "pushup":
                    tracker = PushupTracker()
                    #send a message to frontend that the pushup counter has been started
                    await websocket.send_text(json.dumps({"status": "ready", "message": "Pushup counter started"}))
                else:
                    await websocket.send_text(json.dumps({"status": "error", "message": f"Exercise '{ex_type}' not supported yet"}))
                continue

            #checks if the tracker has the exercise selected, and if not responds to the use to select the exercise
            if tracker is None:
                await websocket.send_text(json.dumps({"status": "waiting", "message": "Please select an exercise first"}))
                continue
            
            #check if the image frame is present
            if "image" not in message:
                continue

            #decoding the image
            base64 = message['image']
            if "," in base64:
                base64 = base64.split(",")[1]

            try:
                #Image first decoded from base64 and then converted to numpy array, then converted to opencv2 image to support mediapipe model
                img_data = base64.b64decode(base64)
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is None:
                    continue

                #the decoded frame is then passed to mediapipe model converted into RGB format
                results = pose_model.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                #if landmarks are detected then pass them to the tracker
                if result.pose_landmarks:
                    #pass landmarks to the tracker using websocket 

                    #these raw landmarks are taken and prepared to display on the frontend UI to draw
                    landmarks_for_ui = [{"x": lm.x, "y": lm.y} for lm in results.pose_landmarks.landmark]

                    #get the response from the process function in pushup.py
                    response = tracker.process(results.pose_landmarks.landmark)

                    #attach the landmarks to the response along with the already existing response
                    response['landmarks'] = landmarks_for_ui

                    #send the response to the frontend
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




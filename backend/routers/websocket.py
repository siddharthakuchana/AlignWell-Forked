from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import base64
import cv2
import numpy as np
import mediapipe as mp

from exercises.pushup import PushupTracker
from exercises.squat import SquatTracker
from exercises.benchpress import BenchPressTracker
from exercises.bicepcurl import BicepCurlTracker
from exercises.crunches import CrunchesTracker
from exercises.deadlift import DeadliftTracker
from exercises.shoulderraise import ShoulderRaiseTracker

#websocket router
router = APIRouter()

#websocket endpoint
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Initialize mediapipe pose model for this connection
    mp_pose = mp.solutions.pose
    pose_model = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    
    #websocket connection accepted
    await websocket.accept()
    print("✅ Client connected")
    
    #initialize tracker and current exercise variables
    tracker = None
    current_exercise = None

    try:
        #websocket loop
        while True:
            #receive data from client
            data = await websocket.receive_text()
            
            is_json = False
            try:
                #parse data
                msg = json.loads(data)
                is_json = True

                #exercise selection
                if "exercise" in msg:
                    ex = msg["exercise"]
                    current_exercise = ex
                    if ex == "pushup": tracker = PushupTracker()
                    elif ex == "squat": tracker = SquatTracker()
                    elif ex == "benchpress": tracker = BenchPressTracker()
                    elif ex == "bicepcurl": tracker = BicepCurlTracker()
                    elif ex == "crunches": tracker = CrunchesTracker()
                    elif ex == "deadlift": tracker = DeadliftTracker()
                    elif ex == "shoulderraise": tracker = ShoulderRaiseTracker()
                    await websocket.send_text(json.dumps({"status": "ready", "message": f"{ex} active"}))
                    continue
                
                #resets the exercise session
                if msg.get("action") == "reset" and tracker:
                    if current_exercise == "pushup": tracker = PushupTracker()
                    elif current_exercise == "squat": tracker = SquatTracker()
                    elif current_exercise == "benchpress": tracker = BenchPressTracker()
                    elif current_exercise == "bicepcurl": tracker = BicepCurlTracker()
                    elif current_exercise == "crunches": tracker = CrunchesTracker()
                    elif current_exercise == "deadlift": tracker = DeadliftTracker()
                    elif current_exercise == "shoulderraise": tracker = ShoulderRaiseTracker()
                    await websocket.send_text(json.dumps({"status": "ready", "reps": 0, "accuracy": 0}))
                    continue
            except:
                pass

            if tracker and not is_json:
                try:
                    #recieve frame data
                    frame_data = data.split(",")[1] if "," in data else data
                    #decode frame data from base64
                    decoded = base64.b64decode(frame_data)
                    #convert to numpy array
                    nparr = np.frombuffer(decoded, np.uint8)
                    #convert to cv2 image
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    if img is not None:
                        #convert to rgb to support mediapipe
                        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        #process the frame with mediapipe
                        results = pose_model.process(rgb)
                        #if results contain landmarks send response to the client
                        if results.pose_landmarks:
                            #send the landmarks as response to the client along with the exercise name
                            response = tracker.process(results.pose_landmarks.landmark)
                            response["landmarks"] = [{"x": lm.x, "y": lm.y} for lm in results.pose_landmarks.landmark]
                            response["exercise"] = current_exercise
                            await websocket.send_text(json.dumps(response))
                except Exception as e:
                    print("WebSocket error:", e)

    except WebSocketDisconnect:
        print("⚠ Client disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
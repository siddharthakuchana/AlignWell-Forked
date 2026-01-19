from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import cv2
import numpy as np
import base64
import json
from typing import List

app = FastAPI()

@app.get("/")
def welcome():
    return {"Hello": "World"}


# WebSocket route
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            #the frame data thats in json format {image: frameData} is loaded
            frame_data = json.loads(data)
            #the image data is in the form of b64 we are decoding it
            b64_str = frame_data["image"]
            if "," in b64_str:
                b64_str = b64_str.split(",")[1]

            # base64 -> bytes
            img_data = base64.b64decode(b64_str)
            #this is converted to an array using numpy
            nparr = np.frombuffer(img_data, np.uint8)
            #the image is converted to a cv2 image to further process it as a pipeline
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except WebSocketDisconnect:
        print("Client disconnected")



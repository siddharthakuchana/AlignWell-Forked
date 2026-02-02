from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import cv2
import numpy as np
import base64
import json
import mediapipe as mp
import os
import sys
import pymysql
from datetime import datetime, timezone
from typing import Optional, List
from dotenv import load_dotenv

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Load .env from root
dotenv_path = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(dotenv_path)

# --- APP SETUP ---
app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and Templates
app.mount("/scripts", StaticFiles(directory=os.path.join(BASE_DIR, "..", "frontend", "scripts")), name="scripts")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "..", "frontend", "html files"))

# --- DB & MODELS & UTILS ---
from database import Base, engine, SessionLocal
from models import User
from utils import hash_password, verify_password, create_access_token, get_current_user_id
from schemas import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- EXERCISE TRACKERS ---
from pushup import PushupTracker
from squat import SquatTracker
from benchpress import BenchPressTracker
from bicepcurl import BicepCurlTracker
from crunches import CrunchesTracker
from deadlift import DeadliftTracker
from shoulderraise import ShoulderRaiseTracker

# --- POSE MODEL ---
mp_pose = mp.solutions.pose
pose_model = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# --- WEBSOCKET ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ Client connected")
    
    tracker = None
    current_exercise = None

    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                msg = json.loads(data)
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

            if tracker:
                try:
                    frame_data = data.split(",")[1] if "," in data else data
                    decoded = base64.b64decode(frame_data)
                    nparr = np.frombuffer(decoded, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    if img is not None:
                        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        results = pose_model.process(rgb)
                        if results.pose_landmarks:
                            response = tracker.process(results.pose_landmarks.landmark)
                            response["landmarks"] = [{"x": lm.x, "y": lm.y} for lm in results.pose_landmarks.landmark]
                            response["exercise"] = current_exercise
                            await websocket.send_text(json.dumps(response))
                except Exception as e:
                    print("WebSocket error:", e)

    except Exception as e:
        print("WebSocket error:", e)


# --- HTML ROUTES ---
@app.get("/")
def index(request: Request, response_class=HTMLResponse):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register")
def register_page(request: Request, response_class=HTMLResponse):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login")
def login_page(request: Request, response_class=HTMLResponse):
    return templates.TemplateResponse("login.html", {"request": request})


# --- AUTH API ---
@app.post("/register")
async def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            data = await request.json()
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")
        except:
            pass

    if not username or not email or not password:
        if "application/json" in content_type:
            raise HTTPException(status_code=400, detail="All fields are required")
        return templates.TemplateResponse("register.html", {"request": request, "error": "All fields are required"}, status_code=400)

    existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        if "application/json" in content_type:
            raise HTTPException(status_code=400, detail="Username or email already exists")
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request, 
                "error": "Username or email already exists"
            }, 
            status_code=400
        )

    new_user = User(
        username=username,
        email=email,
        password=hash_password(password),
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)


    if "application/json" in content_type:
        return RegisterResponse.model_validate(new_user)
    
    return RedirectResponse(
        url="/login?message=Registration successful",
        status_code=status.HTTP_303_SEE_OTHER
    )


@app.post("/login")
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            data = await request.json()
            email = data.get("email")
            password = data.get("password")
        except:
            pass

    if not email or not password:
        if "application/json" in content_type:
            raise HTTPException(status_code=400, detail="Email and password required")
        return templates.TemplateResponse(
            "login.html", 
            {
                "request": request, 
                "error": "Email and password required"
            }, 
            status_code=400
        )

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        if "application/json" in content_type:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        return templates.TemplateResponse(
            "login.html", 
            {
                "request": request, 
                "error": "Invalid credentials"
            },
            status_code=400
        )

    access_token = create_access_token(data={"sub": str(user.id), "username": user.username})

    if "application/json" in content_type:
        return LoginResponse(
            user_id=user.id,
            username=user.username,
            email=user.email,
            access_token=access_token
        )
    
    response = RedirectResponse(url="/detect", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token", 
        value=f"Bearer {access_token}", 
        httponly=True,
        samesite="lax",
        secure=False # Set to True in production with HTTPS
    )
    return response


@app.get("/detect")
def detect_page(request: Request, db: Session = Depends(get_db), response_class=HTMLResponse):
    # Check if user is logged in
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify user exists
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    return templates.TemplateResponse("detect.html", {"request": request, "username": user.username})
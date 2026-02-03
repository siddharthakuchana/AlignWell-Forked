import os
import sys
from dotenv import load_dotenv

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXERCISES_DIR = os.path.join(BASE_DIR, "exercises")
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
if EXERCISES_DIR not in sys.path:
    sys.path.append(EXERCISES_DIR)

# Load .env from root
dotenv_path = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(dotenv_path)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from database.database import Base, engine
from templating import templates
from routers import authentication, display_pages, exercise_guide, websocket

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

# Include Routers
app.include_router(authentication.router)
app.include_router(display_pages.router)
app.include_router(exercise_guide.router)
app.include_router(websocket.router)

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

# --- HTML ROUTES ---
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


import os
import sys
from dotenv import load_dotenv

# ---------------- PATH SETUP ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXERCISES_DIR = os.path.join(BASE_DIR, "exercises")

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

if EXERCISES_DIR not in sys.path:
    sys.path.append(EXERCISES_DIR)

# ---------------- LOAD ENV ----------------
# ✅ Correct: loads .env from backend folder
load_dotenv()

# ---------------- IMPORTS ----------------
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from database.database import Base, engine
from templating import templates
from routers import authentication, display_pages, exercise_guide, websocket

# ---------------- APP SETUP ----------------
app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- STATIC FILES ----------------
app.mount(
    "/scripts",
    StaticFiles(directory=os.path.join(BASE_DIR, "..", "frontend", "scripts")),
    name="scripts"
)

# ✅ ADD THIS
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "..", "frontend", "static")),
    name="static"
)

# ---------------- ROUTERS ----------------
app.include_router(authentication.router)
app.include_router(display_pages.router)
app.include_router(exercise_guide.router)
app.include_router(websocket.router)

# ---------------- DATABASE SETUP ----------------
@app.on_event("startup")
def startup_event():
    # ❌ COMMENT THIS
    # Base.metadata.create_all(bind=engine)
    print("Startup done without DB")
# ---------------- INIT DB ----------------
@app.get("/init-db")
def init_db():
    Base.metadata.create_all(bind=engine)
    return {"msg": "Database initialized"}
# ---------------- DB TEST ----------------
@app.get("/db-test")
def db_test():
    with engine.connect() as conn:
        return {"db": "connected"}

# ---------------- HOME ROUTE ----------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
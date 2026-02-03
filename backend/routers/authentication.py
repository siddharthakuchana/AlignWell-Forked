from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database.dependencies import get_db
from database.models import User
from database.schemas import RegisterResponse, LoginResponse
from utils import hash_password, verify_password, create_access_token
from templating import templates

router = APIRouter()

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# --- AUTH API ---
@router.post("/register")
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


@router.post("/login")
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


@router.get("/logout")
def logout():
    response = RedirectResponse(
        url="/login",
        status_code=status.HTTP_302_FOUND
    )
    #only removes the cookie if everything matches
    response.delete_cookie(
        key="access_token",
        path="/",
        samesite="lax",
        secure=False
    )
    return response

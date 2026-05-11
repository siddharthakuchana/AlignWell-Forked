from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from database.dependencies import get_db
from database.models import User
from utils import get_current_user_id
from templating import templates

#display pages router
router = APIRouter()

#renders the detect.html page
@router.get("/detect", response_class=HTMLResponse)
def detect_page(request: Request, db: Session = Depends(get_db)):
    # Check if user is logged in
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify user exists
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    return templates.TemplateResponse(
        "detect.html", 
        {
            "request": request, 
            "username": user.username
        }
    )

#renders the guide.html page
@router.get("/guide", response_class=HTMLResponse)
def guide_page(request: Request, db: Session = Depends(get_db)):
    # Check if user is logged in
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify user exists
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    return templates.TemplateResponse(
        "guide.html", 
        {
            "request": request, 
            "username": user.username
        }
    )

#renders the contributors.html page
@router.get("/contributors", response_class=HTMLResponse)
def creators_page(request: Request, db: Session = Depends(get_db)):
    # Try to get user info if logged in (for navbar "Hi, username")
    user_id = get_current_user_id(request)
    username = None
    if user_id:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user:
            username = user.username
        
    return templates.TemplateResponse(
        "contributors.html", 
        {
            "request": request, 
            "username": username
        }
    )

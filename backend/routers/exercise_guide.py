from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from database.dependencies import get_db
from database.models import User
from utils import get_current_user_id
from templating import templates

router = APIRouter()

@router.get("/pushup", response_class=HTMLResponse)
def pushup_page(request: Request, db: Session = Depends(get_db)):
    # Check if user is logged in
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify user exists
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    return templates.TemplateResponse(
        "pushups.html", 
        {
            "request": request, 
            "username": user.username
        }
    )

@router.get("/squat", response_class=HTMLResponse)
def squat_page(request: Request, db: Session = Depends(get_db)):
    # Check if user is logged in
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify user exists
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    return templates.TemplateResponse(
        "squat.html", 
        {
            "request": request, 
            "username": user.username
        }
    )

@router.get("/shoulder_raise", response_class=HTMLResponse)
def shoulderraise_page(request: Request, db: Session = Depends(get_db)):
    # Check if user is logged in
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify user exists
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    return templates.TemplateResponse(
        "shoulder_raise.html", 
        {
            "request": request, 
            "username": user.username
        }
    )

@router.get("/bicep_curl", response_class=HTMLResponse)
def bicepcurl_page(request: Request, db: Session = Depends(get_db)):
    # Check if user is logged in
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify user exists
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    return templates.TemplateResponse(
        "bicep_curl.html", 
        {
            "request": request, 
            "username": user.username
        }
    )

@router.get("/bench_press", response_class=HTMLResponse)
def benchpress_page(request: Request, db: Session = Depends(get_db)):
    # Check if user is logged in
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify user exists
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    return templates.TemplateResponse(
        "bench_press.html", 
        {
            "request": request, 
            "username": user.username
        }
    )

@router.get("/deadlift", response_class=HTMLResponse)
def deadlift_page(request: Request, db: Session = Depends(get_db)):
    # Check if user is logged in
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify user exists
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    return templates.TemplateResponse(
        "deadlift.html", 
        {
            "request": request, 
            "username": user.username
        }
    )

@router.get('/crunches', response_class=HTMLResponse)
def crunches_page(request: Request, db: Session = Depends(get_db)):
    # Check if user is logged in
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify user exists
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    return templates.TemplateResponse(
        "crunches.html", 
        {
            "request": request, 
            "username": user.username
        }
    )

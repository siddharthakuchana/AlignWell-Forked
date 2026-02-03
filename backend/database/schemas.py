from pydantic import BaseModel, EmailStr
from datetime import datetime

#register request schema
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

#register response schema
class RegisterResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    created_at: datetime
    class Config:
        from_attributes = True

#login request schema
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

#login response schema
class LoginResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    access_token: str
    token_type: str = "bearer"
    class Config:
        from_attributes = True
import os
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from dotenv import load_dotenv
from fastapi import Request

#path set up of main file and .env file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(dotenv_path)

#secret key, algorithm and expire minutes for jwt authentication
SECRET_KEY = os.getenv("SECRET_KEY", "your-fallback-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 60))

#password context for password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

#prehash function for password hashing
def _prehash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

#hash function for password hashing
def hash_password(password: str) -> str:
    return pwd_context.hash(_prehash(password))

#verify function for password verification
def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_prehash(password), hashed_password)

#function to create access token for jwt authentication
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

#to return the current user id, from the token in the cookie
def get_current_user_id(request: Request) -> Optional[str]:
    token = request.cookies.get("access_token")

    if not token:
        return None

    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

from typing import Optional
from datetime import date
from pydantic import BaseModel

class UserRegisterRequest(BaseModel):
    user_id: str
    password: str
    name: str
    user_email: str
    sex: Optional[str] = None
    birth_date: Optional[date] = None

class LoginRequest(BaseModel):
    user_id: str
    password: str

class UserDeleteRequest(BaseModel):
    user_id: str
    password: str

class UserRegisterResponse(BaseModel):
    success: bool
    user_id: Optional[str] = None
    name: Optional[str] = None
    user_email: Optional[str] = None
    message: str

class LoginResponse(BaseModel):
    success: bool
    user_id: Optional[str] = None
    name: Optional[str] = None
    user_email: Optional[str] = None
    message: str

class UserDeleteResponse(BaseModel):
    success: bool
    message: str

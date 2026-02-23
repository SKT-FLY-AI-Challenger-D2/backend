from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.features.user.user_service import UserService
from app.features.user.user_schema import (
    UserRegisterRequest, UserRegisterResponse,
    LoginRequest, LoginResponse,
    UserDeleteRequest, UserDeleteResponse,
)

router = APIRouter()

@router.get("/test")
def test_user():
    return {"message": "User Router is working!"}

@router.post("/register", response_model=UserRegisterResponse)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    service = UserService(db)
    result = service.register(request)
    status_code = 201 if result.success else 409
    return JSONResponse(status_code=status_code, content=result.model_dump())

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    service = UserService(db)
    result = service.login(request)
    status_code = 200 if result.success else 401
    return JSONResponse(status_code=status_code, content=result.model_dump())

@router.post("/withdraw", response_model=UserDeleteResponse)
def withdraw(request: UserDeleteRequest, db: Session = Depends(get_db)):
    service = UserService(db)
    result = service.delete(request)
    status_code = 200 if result.success else 401
    return JSONResponse(status_code=status_code, content=result.model_dump())
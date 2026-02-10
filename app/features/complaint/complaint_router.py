from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()

@router.get("/test")
def test_complaint():
    return {"message": "Complaint Router is working!"}
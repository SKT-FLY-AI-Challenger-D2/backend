from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()

@router.get("/test")
def test_report():
    return {"message": "Report Router is working!"}
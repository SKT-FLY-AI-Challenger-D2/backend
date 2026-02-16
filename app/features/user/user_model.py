from sqlalchemy import Column, String, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(255), primary_key=True)
    password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    sex = Column(String(1))
    birth_date = Column(Date)
    created_at = Column(DateTime, default=func.now())
    user_email = Column(String(255), unique=True, nullable=False)

    # Constraint: CHECK (sex IN ('M', 'F'))
    __table_args__ = (
        CheckConstraint("sex IN ('M', 'F')", name="chk_sex"),
    )

class UserYoutube(Base):
    __tablename__ = "user_youtubes"

    youtube_account_id = Column(String(255), primary_key=True)
    youtube_email = Column(String(255), unique=True)
    youtube_nickname = Column(String(255))
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

class ParentChild(Base):
    __tablename__ = "parent_child"

    parent_user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    child_user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
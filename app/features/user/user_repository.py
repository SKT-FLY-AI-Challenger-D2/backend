from sqlalchemy.orm import Session
from app.features.user.user_model import User, UserYoutube, ParentChild
from typing import Optional, List

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    # ==========================
    # 1. User (기본 유저)
    # ==========================
    def create_user(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.user_id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.user_email == email).first()

    def update_user(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: str) -> None:
        user = self.get_user_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()

    # ==========================
    # 2. UserYoutube (유튜브 연동)
    # ==========================
    def add_youtube_account(self, youtube: UserYoutube) -> UserYoutube:
        self.db.add(youtube)
        self.db.commit()
        self.db.refresh(youtube)
        return youtube

    def get_youtube_accounts_by_user(self, user_id: str) -> List[UserYoutube]:
        return self.db.query(UserYoutube).filter(UserYoutube.user_id == user_id).all()

    # ==========================
    # 3. ParentChild (가족 관계)
    # ==========================
    def add_parent_child(self, relation: ParentChild) -> ParentChild:
        self.db.add(relation)
        self.db.commit()
        self.db.refresh(relation)
        return relation

    def get_children(self, parent_id: str) -> List[ParentChild]:
        """부모 ID로 자녀 목록 조회"""
        return self.db.query(ParentChild).filter(ParentChild.parent_user_id == parent_id).all()
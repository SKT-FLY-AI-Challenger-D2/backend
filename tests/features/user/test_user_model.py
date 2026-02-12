# tests/features/user/test_user_model.py
from app.features.user.user_model import User, UserYoutube, ParentChild
from sqlalchemy.exc import IntegrityError
import pytest

def test_user_flow(db_session):
    # [Step 1] 데이터 생성 (INSERT)
    user = User(
        user_id="user_1",
        password="password123",
        name="김철수",
        sex="M",
        user_email="chulsoo@example.com"
    )
    db_session.add(user)
    
    # [Step 2] 저장 (COMMIT)
    db_session.commit()

    # [Step 3] 조회 (SELECT)
    saved_user = db_session.query(User).filter(User.user_id == "user_1").first()
    assert saved_user is not None
    assert saved_user.name == "김철수"
    assert saved_user.sex == "M"

    # [Step 4] 삭제 (DELETE)
    db_session.delete(saved_user)
    db_session.commit()
    
    # 삭제 확인
    deleted_user = db_session.query(User).filter(User.user_id == "user_1").first()
    assert deleted_user is None


def test_user_youtube_relation(db_session):
    # 부모(User) 먼저 생성
    user = User(user_id="user_2", password="pw", name="유튜버", user_email="y@e.com")
    db_session.add(user)
    db_session.commit()

    # 유튜브 계정 연결 (INSERT)
    youtube = UserYoutube(
        youtube_account_id="yt_1",
        youtube_email="yt@google.com",
        youtube_nickname="철수TV",
        user_id="user_2" # FK
    )
    db_session.add(youtube)
    db_session.commit()

    # 조회 (SELECT)
    saved_yt = db_session.query(UserYoutube).filter(UserYoutube.youtube_account_id == "yt_1").first()
    assert saved_yt.user_id == "user_2"


def test_parent_child_relationship(db_session):
    # 부모, 자녀 유저 생성
    parent = User(user_id="dad", password="pw", name="아빠", user_email="dad@e.com")
    child = User(user_id="son", password="pw", name="아들", user_email="son@e.com")
    db_session.add_all([parent, child])
    db_session.commit()

    # 관계 맺기 (INSERT)
    relation = ParentChild(parent_user_id="dad", child_user_id="son")
    db_session.add(relation)
    db_session.commit()

    # 조회 (SELECT)
    saved_relation = db_session.query(ParentChild).filter_by(parent_user_id="dad").first()
    assert saved_relation.child_user_id == "son"
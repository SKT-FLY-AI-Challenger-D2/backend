# tests/features/user/test_user_model.py
from app.features.user.user_model import User, UserYoutube, ParentChild
from sqlalchemy.exc import IntegrityError
import pytest

# [테스트 목적] User 모델의 기본 CRUD 동작 검증
# [테스트 방식] 인메모리 SQLite DB에서 직접 ORM 조작
# [테스트 동작]
#   1. User INSERT (user_id, password, name, sex, user_email)
#   2. COMMIT
#   3. SELECT → name, sex 일치 assert
#   4. UPDATE (name 변경) → COMMIT → SELECT → 변경 확인 assert
#   5. DELETE → COMMIT → SELECT → None assert
# [Input] User(user_id="user_1", name="김철수", sex="M", user_email="chulsoo@example.com")
# [Output] 저장 후 name/sex 일치, Update 후 name 변경, 삭제 후 None
def test_user_flow(db_session):
    # 1. Create (INSERT)
    user = User(
        user_id="user_1",
        password="password123",
        name="김철수",
        sex="M",
        user_email="chulsoo@example.com"
    )
    db_session.add(user)
    db_session.commit()

    # 2. Read (SELECT)
    saved_user = db_session.query(User).filter(User.user_id == "user_1").first()
    assert saved_user is not None
    assert saved_user.name == "김철수"
    assert saved_user.sex == "M"

    # 3. Update
    saved_user.name = "수정된이름"
    db_session.commit()
    updated_user = db_session.query(User).filter(User.user_id == "user_1").first()
    assert updated_user.name == "수정된이름"

    # 4. Delete
    db_session.delete(updated_user)
    db_session.commit()
    deleted_user = db_session.query(User).filter(User.user_id == "user_1").first()
    assert deleted_user is None


# [테스트 목적] User-UserYoutube 1:N 관계 검증
# [테스트 방식] 인메모리 SQLite DB에서 직접 ORM 조작
# [테스트 동작]
#   1. User INSERT (FK 선행조건)
#   2. UserYoutube INSERT (youtube_account_id, user_id FK)
#   3. COMMIT
#   4. SELECT → user_id FK 일치 assert
# [Input] User(user_id="user_2") → UserYoutube(youtube_account_id="yt_1", user_id="user_2")
# [Output] UserYoutube의 user_id가 "user_2"와 일치
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


# [테스트 목적] ParentChild M:N 관계 (복합 PK) 검증
# [테스트 방식] 인메모리 SQLite DB에서 직접 ORM 조작
# [테스트 동작]
#   1. User 2명 INSERT ("dad", "son")
#   2. COMMIT
#   3. ParentChild INSERT (parent="dad", child="son")
#   4. COMMIT
#   5. SELECT (filter parent_user_id="dad") → child_user_id="son" assert
# [Input] User 2명("dad", "son") → ParentChild(parent="dad", child="son")
# [Output] parent_user_id="dad"로 조회 시 child_user_id="son" 일치
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
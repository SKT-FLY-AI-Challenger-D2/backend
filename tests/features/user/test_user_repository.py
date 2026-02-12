import pytest
from app.features.user.user_repository import UserRepository
from app.features.user.user_model import User, UserYoutube, ParentChild

def test_user_crud(db_session):
    repo = UserRepository(db_session)

    # 1. Create
    user = User(user_id="u1", password="pw", name="테스트", user_email="t@t.com", sex="M")
    created_user = repo.create_user(user)
    assert created_user.user_id == "u1"

    # 2. Read (Get)
    fetched_user = repo.get_user_by_email("t@t.com")
    assert fetched_user is not None
    assert fetched_user.name == "테스트"

    # 3. Update
    fetched_user.name = "수정된이름"
    updated_user = repo.update_user(fetched_user)
    assert updated_user.name == "수정된이름"

    # 4. Delete
    repo.delete_user("u1")
    assert repo.get_user_by_id("u1") is None

def test_user_relations(db_session):
    repo = UserRepository(db_session)
    
    # 부모/자녀 유저 준비
    parent = User(user_id="dad", password="pw", name="아빠", user_email="d@d.com", sex="M")
    child = User(user_id="son", password="pw", name="아들", user_email="s@s.com", sex="M")
    repo.create_user(parent)
    repo.create_user(child)

    # 1. 유튜브 계정 추가 테스트
    yt = UserYoutube(
        youtube_account_id="yt_1", 
        user_id="dad", 
        youtube_email="yt@g.com", 
        youtube_nickname="아빠TV"
    )
    repo.add_youtube_account(yt)
    
    accounts = repo.get_youtube_accounts_by_user("dad")
    assert len(accounts) == 1
    assert accounts[0].youtube_nickname == "아빠TV"

    # 2. 부모-자녀 관계 테스트
    relation = ParentChild(parent_user_id="dad", child_user_id="son")
    repo.add_parent_child(relation)

    children = repo.get_children("dad")
    assert len(children) == 1
    assert children[0].child_user_id == "son"
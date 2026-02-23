import pytest
from app.features.user.user_service import UserService
from app.features.user.user_schema import UserRegisterRequest, LoginRequest, UserDeleteRequest

# [테스트 목적] UserService.register()의 정상 회원가입 동작 검증
# [테스트 방식] 인메모리 SQLite DB + UserService.register() 호출
# [테스트 동작] 유효한 회원 정보로 register() 호출 → 성공 응답 확인
# [Input] UserRegisterRequest(user_id="u1", password="pw", name="테스트", user_email="t@t.com")
# [Output] UserRegisterResponse(success=True, user_id="u1", message="회원가입이 완료되었습니다.")
def test_register_success(db_session):
    service = UserService(db_session)
    result = service.register(UserRegisterRequest(user_id="u1", password="pw", name="테스트", user_email="t@t.com"))
    assert result.success == True
    assert result.user_id == "u1"
    assert result.message == "회원가입이 완료되었습니다."

# [테스트 목적] 동일 user_id로 중복 가입 시 실패 응답 검증
# [테스트 방식] 인메모리 SQLite DB + 동일 ID로 register() 2회 호출
# [테스트 동작] 1회 정상 가입 → 동일 ID로 2회 가입 시도 → 실패 응답 확인
# [Input] 1차: UserRegisterRequest(user_id="u1", ...), 2차: UserRegisterRequest(user_id="u1", ...)
# [Output] UserRegisterResponse(success=False, message="이미 존재하는 사용자 ID입니다.")
def test_register_duplicate_id(db_session):
    service = UserService(db_session)
    service.register(UserRegisterRequest(user_id="u1", password="pw", name="테스트", user_email="t@t.com"))
    result = service.register(UserRegisterRequest(user_id="u1", password="pw2", name="다른", user_email="o@o.com"))
    assert result.success == False
    assert result.message == "이미 존재하는 사용자 ID입니다."

# [테스트 목적] 동일 이메일로 중복 가입 시 실패 응답 검증
# [테스트 방식] 인메모리 SQLite DB + 동일 이메일로 register() 2회 호출
# [테스트 동작] 1차 정상 가입 → 다른 ID + 동일 이메일로 2차 가입 시도 → 실패 응답 확인
# [Input] 1차: (user_id="u1", email="t@t.com"), 2차: (user_id="u2", email="t@t.com")
# [Output] UserRegisterResponse(success=False, message="이미 존재하는 이메일입니다.")
def test_register_duplicate_email(db_session):
    service = UserService(db_session)
    service.register(UserRegisterRequest(user_id="u1", password="pw", name="테스트", user_email="t@t.com"))
    result = service.register(UserRegisterRequest(user_id="u2", password="pw2", name="다른", user_email="t@t.com"))
    assert result.success == False
    assert result.message == "이미 존재하는 이메일입니다."

# [테스트 목적] UserService.login()의 정상 로그인 동작 검증
# [테스트 방식] 인메모리 SQLite DB + 가입 후 동일 ID/PW로 login() 호출
# [테스트 동작] register()로 유저 생성 → 동일 ID/PW로 login() → 성공 응답 확인
# [Input] LoginRequest(user_id="u1", password="pw")
# [Output] LoginResponse(success=True, user_id="u1")
def test_login_success(db_session):
    service = UserService(db_session)
    service.register(UserRegisterRequest(user_id="u1", password="pw", name="테스트", user_email="t@t.com"))
    result = service.login(LoginRequest(user_id="u1", password="pw"))
    assert result.success == True
    assert result.user_id == "u1"

# [테스트 목적] 틀린 비밀번호로 로그인 시 실패 응답 검증
# [테스트 방식] 인메모리 SQLite DB + 가입 후 다른 PW로 login() 호출
# [테스트 동작] register()로 유저 생성 → 틀린 PW로 login() → 실패 응답 확인
# [Input] LoginRequest(user_id="u1", password="wrong")
# [Output] LoginResponse(success=False, message="아이디 또는 비밀번호가 올바르지 않습니다.")
def test_login_wrong_password(db_session):
    service = UserService(db_session)
    service.register(UserRegisterRequest(user_id="u1", password="pw", name="테스트", user_email="t@t.com"))
    result = service.login(LoginRequest(user_id="u1", password="wrong"))
    assert result.success == False

# [테스트 목적] 존재하지 않는 ID로 로그인 시 실패 응답 검증
# [테스트 방식] 인메모리 SQLite DB + 가입 없이 login() 호출
# [테스트 동작] DB에 유저 없는 상태에서 login() → 실패 응답 확인
# [Input] LoginRequest(user_id="ghost", password="pw")
# [Output] LoginResponse(success=False, message="아이디 또는 비밀번호가 올바르지 않습니다.")
def test_login_nonexistent_user(db_session):
    service = UserService(db_session)
    result = service.login(LoginRequest(user_id="ghost", password="pw"))
    assert result.success == False

# [테스트 목적] UserService.delete()의 정상 회원 탈퇴 동작 검증
# [테스트 방식] 인메모리 SQLite DB + 가입 후 동일 ID/PW로 delete() 호출
# [테스트 동작] register()로 유저 생성 → 동일 ID/PW로 delete() → 성공 응답 확인 → 로그인 시도 → 실패 확인
# [Input] UserDeleteRequest(user_id="u1", password="pw")
# [Output] UserDeleteResponse(success=True, message="회원 탈퇴가 완료되었습니다.")
def test_delete_success(db_session):
    service = UserService(db_session)
    service.register(UserRegisterRequest(user_id="u1", password="pw", name="테스트", user_email="t@t.com"))
    result = service.delete(UserDeleteRequest(user_id="u1", password="pw"))
    assert result.success == True
    assert result.message == "회원 탈퇴가 완료되었습니다."
    # 탈퇴 후 로그인 불가 확인
    login_result = service.login(LoginRequest(user_id="u1", password="pw"))
    assert login_result.success == False

# [테스트 목적] 틀린 비밀번호로 회원 탈퇴 시 실패 응답 검증
# [테스트 방식] 인메모리 SQLite DB + 가입 후 다른 PW로 delete() 호출
# [테스트 동작] register()로 유저 생성 → 틀린 PW로 delete() → 실패 응답 확인
# [Input] UserDeleteRequest(user_id="u1", password="wrong")
# [Output] UserDeleteResponse(success=False, message="아이디 또는 비밀번호가 올바르지 않습니다.")
def test_delete_wrong_password(db_session):
    service = UserService(db_session)
    service.register(UserRegisterRequest(user_id="u1", password="pw", name="테스트", user_email="t@t.com"))
    result = service.delete(UserDeleteRequest(user_id="u1", password="wrong"))
    assert result.success == False

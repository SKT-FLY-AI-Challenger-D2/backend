from sqlalchemy.orm import Session
from app.features.user.user_repository import UserRepository
from app.features.user.user_model import User
from app.features.user.user_schema import (
    UserRegisterRequest, UserRegisterResponse,
    LoginRequest, LoginResponse,
    UserDeleteRequest, UserDeleteResponse,
)


class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def register(self, request: UserRegisterRequest) -> UserRegisterResponse:
        # 1. ID 중복 체크
        if self.repo.get_user_by_id(request.user_id):
            return UserRegisterResponse(
                success=False,
                message="이미 존재하는 사용자 ID입니다."
            )

        # 2. 이메일 중복 체크
        if self.repo.get_user_by_email(request.user_email):
            return UserRegisterResponse(
                success=False,
                message="이미 존재하는 이메일입니다."
            )

        # 3. User 모델 생성 및 저장
        user = User(
            user_id=request.user_id,
            password=request.password,
            name=request.name,
            user_email=request.user_email,
            sex=request.sex,
            birth_date=request.birth_date,
        )
        self.repo.create_user(user)

        # 4. 성공 응답
        return UserRegisterResponse(
            success=True,
            user_id=user.user_id,
            name=user.name,
            user_email=user.user_email,
            message="회원가입이 완료되었습니다."
        )

    def login(self, request: LoginRequest) -> LoginResponse:
        # 1. 유저 조회
        user = self.repo.get_user_by_id(request.user_id)

        # 2. 유저 없음
        if not user:
            return LoginResponse(
                success=False,
                message="아이디 또는 비밀번호가 올바르지 않습니다."
            )

        # 3. 비밀번호 단순 비교
        if user.password != request.password:
            return LoginResponse(
                success=False,
                message="아이디 또는 비밀번호가 올바르지 않습니다."
            )

        # 4. 성공 응답
        return LoginResponse(
            success=True,
            user_id=user.user_id,
            name=user.name,
            user_email=user.user_email,
            message="로그인 성공"
        )

    def delete(self, request: UserDeleteRequest) -> UserDeleteResponse:
        # 1. 유저 조회
        user = self.repo.get_user_by_id(request.user_id)

        # 2. 유저 없음
        if not user:
            return UserDeleteResponse(
                success=False,
                message="아이디 또는 비밀번호가 올바르지 않습니다."
            )

        # 3. 비밀번호 단순 비교
        if user.password != request.password:
            return UserDeleteResponse(
                success=False,
                message="아이디 또는 비밀번호가 올바르지 않습니다."
            )

        # 4. 유저 삭제
        self.repo.delete_user(request.user_id)

        # 5. 성공 응답
        return UserDeleteResponse(
            success=True,
            message="회원 탈퇴가 완료되었습니다."
        )

# VideoService의 요청 단위 DB Session 격리·rollback 검증 (TASK-04)

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.features.video.video_schema import SearchRequest
from app.features.video.video_service import VideoService

# 모든 모델 import (FK가 걸린 전체 테이블이 올바른 순서로 생성되도록 보장, conftest와 동일한 이유)
import app.features.user.user_model
import app.features.video.video_model
import app.features.report.report_model
import app.features.complaint.complaint_model

FAKE_SEARCH_RESULT = {
    "video_id": "abc123",
    "title": "테스트 제목",
    "channel_title": "테스트 채널",
    "url": "https://www.youtube.com/watch?v=abc123",
}


def _make_request() -> SearchRequest:
    return SearchRequest(title="테스트 제목", channel="테스트 채널", duration=120)


@patch("app.features.video.video_service.VideoSearch")
def test_분석_실패시_세션이_rollback되고_이후_사용_가능하다(mock_video_search_cls, db_session):
    """report_service.analyze_video 실패 시 self.db.rollback()이 실행되어,
    같은 세션으로도 이후 쓰기가 정상 동작해야 한다 (FR-12).

    VideoRepository.create_video는 자체적으로 즉시 commit하므로, 분석 실패 시점에는
    이미 Video row가 커밋되어 있다. rollback()이 지키는 것은 이 row의 존재 여부가
    아니라 "예외 이후에도 같은 세션을 계속 정상적으로 쓸 수 있는가"이다.
    """
    from app.features.video.video_model import Video

    mock_video_search_cls.return_value.search_youtube.return_value = dict(FAKE_SEARCH_RESULT)

    service = VideoService(db_session)
    service.report_service.analyze_video = MagicMock(side_effect=RuntimeError("AI 서버 호출 실패"))

    with pytest.raises(RuntimeError):
        service.search_and_analyze_video(_make_request())

    # create_video()가 이미 commit했으므로 신규 Video row 1건은 남아있어야 한다
    assert db_session.query(Video).count() == 1

    # rollback 이후에도 같은 세션으로 정상적인 추가 커밋이 가능해야 한다 (세션이 오염되지 않음)
    db_session.add(
        Video(video_id="ok", video_title="t", channel="c", youtube_url="u", status="PENDING")
    )
    db_session.commit()
    assert db_session.query(Video).count() == 2


@patch("app.features.video.video_service.VideoSearch")
def test_서로_다른_VideoService는_독립된_세션을_사용한다(mock_video_search_cls):
    """VideoService(db)가 주입받은 세션을 그대로 쓰므로, 두 인스턴스는
    서로 다른 세션을 갖고 한쪽의 실패가 다른 쪽에 전파되지 않는다 (FR-12)."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db_a = TestingSessionLocal()
    db_b = TestingSessionLocal()
    try:
        service_a = VideoService(db_a)
        service_b = VideoService(db_b)

        assert service_a.db is db_a
        assert service_b.db is db_b
        assert service_a.db is not service_b.db
    finally:
        db_a.close()
        db_b.close()
        Base.metadata.drop_all(bind=engine)

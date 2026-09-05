# Backend↔AI 공개 계약 검증 (TASK-05)
#
# `tests/fixtures/ai_analysis_response.json`은 AI 저장소 `schemas.py`의
# AnalyzeResponse(is_ad, legal: LegalResult|None, deepfake: DeepfakeResult|None,
# fact: FactResult|None, final_score, report)와 필드명을 맞춰 만든 대표 정상
# 응답이다. 두 저장소는 서로 다른 Git 저장소라 import로 직접 스키마를 공유할
# 수 없으므로, 이 파일의 필드 목록은 AI `schemas.py`를 수동으로 대조해서
# 작성했다. 두 저장소를 모두 아는 CI가 생기면(TASK-15) 그쪽에서 자동 대조로
# 승격하는 것을 목표로 한다.
#
# 이 파일은 실제 AI 서버를 호출하지 않는다(httpx.post를 fixture로 대체).
# 스테이지 2(Compose 내부 /health·/ready 연결)와 스테이지 4(실제 /analyze
# 전체 흐름)의 실제 연결 검증은 각각 TASK-06/TASK-16에서 별도로 수행한다.

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.features.report.report_service import ReportService
from app.features.report.report_schema import AnalysisRequest
from app.features.report.report_repository import ReportRepository
from app.features.video.video_repository import VideoRepository
from app.features.video.video_model import Video

FIXTURE_PATH = Path(__file__).parent.parent.parent / "fixtures" / "ai_analysis_response.json"

# AI schemas.py의 AnalyzeResponse 공개 필드. fixture와 어긋나면 드리프트를 의미한다.
EXPECTED_TOP_LEVEL_FIELDS = {"is_ad", "legal", "deepfake", "fact", "final_score", "report"}
EXPECTED_LEGAL_FIELDS = {"legal_issue_score", "legal_issue_evidence"}
EXPECTED_DEEPFAKE_FIELDS = {"deepfake_ai_score", "deepfake_ai_evidence"}
EXPECTED_FACT_FIELDS = {"fake_score", "fake_evidence"}


def _load_fixture() -> dict:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_fixture_필드가_AI_공개_스키마와_일치한다():
    """fixture의 필드 구성이 AI schemas.py의 AnalyzeResponse와 어긋나지 않는지 확인한다."""
    data = _load_fixture()

    assert set(data.keys()) == EXPECTED_TOP_LEVEL_FIELDS
    assert set(data["legal"].keys()) == EXPECTED_LEGAL_FIELDS
    assert set(data["deepfake"].keys()) == EXPECTED_DEEPFAKE_FIELDS
    assert set(data["fact"].keys()) == EXPECTED_FACT_FIELDS

    assert isinstance(data["is_ad"], bool)
    assert isinstance(data["final_score"], (int, float))
    assert isinstance(data["report"], str)
    assert isinstance(data["legal"]["legal_issue_evidence"], list)
    assert isinstance(data["deepfake"]["deepfake_ai_evidence"], list)
    assert isinstance(data["fact"]["fake_evidence"], list)


def test_fixture_nullable_카테고리도_스키마와_호환된다():
    """legal/deepfake/fact는 Optional이므로 None이어도 AI 쪽 계약을 벗어나지 않는다."""
    data = _load_fixture()
    data["legal"] = None
    data["deepfake"] = None
    # analysis_ai_result가 None 카테고리를 그대로 받아들이는지는
    # test_report_service.py의 기존 케이스들이 이미 검증한다. 여기서는
    # "fixture 형태가 nullable 조합에서도 유효한 JSON 계약을 유지하는가"만 확인한다.
    assert data["fact"] is not None
    assert data["legal"] is None
    assert data["deepfake"] is None


@patch("app.features.report.report_service.httpx.post")
def test_fixture로_전체_흐름_요청조립_파싱_저장_응답을_검증한다(mock_post, db_session):
    """실제 AI 서버 호출 없이 fixture 응답만으로 요청 조립→파싱→DB 저장→응답까지 확인한다."""
    fixture_data = _load_fixture()

    video_repo = VideoRepository(db_session)
    report_repo = ReportRepository(db_session)
    report_service = ReportService(db_session)

    video = Video(video_id="v_contract_test", video_title="Contract Test", status="PENDING")
    video_repo.create_video(video)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = fixture_data
    mock_post.return_value = mock_response

    request = AnalysisRequest(
        youtube_url="https://youtube.com/watch?v=contract",
        video_id="v_contract_test",
    )

    result = report_service.analyze_video(request)

    # 1. 요청 조립: AI에는 youtube_url만 전달한다 (계약 유지)
    mock_post.assert_called_once()
    assert mock_post.call_args[1]["json"] == {
        "youtube_url": "https://youtube.com/watch?v=contract"
    }

    # 2. 파싱: fixture의 세 카테고리 점수 대신 AI가 명시적으로 준
    # final_score(0.62)를 그대로 쓴다. 0.62 >= 0.6이므로 고위험(2)이다.
    assert result.final_score == fixture_data["final_score"]
    assert result.final_risk_level == 2
    assert result.analysis_report == fixture_data["report"]
    assert result.error is None

    # 3. 저장: AIReport와 각 카테고리 ReportEvidence가 실제로 커밋됐는지 확인
    saved_report = report_repo.get_report_by_video_id("v_contract_test")
    assert saved_report is not None
    assert float(saved_report.final_score) == fixture_data["final_score"]
    assert float(saved_report.legal_issue_score) == fixture_data["legal"]["legal_issue_score"]
    assert float(saved_report.deepfake_score) == fixture_data["deepfake"]["deepfake_ai_score"]
    assert float(saved_report.fact_score) == fixture_data["fact"]["fake_score"]

    evidences = report_repo.get_evidence_by_report(saved_report.report_id)
    legal_evidence = [e.content for e in evidences if e.category == "LEGAL"]
    assert legal_evidence == fixture_data["legal"]["legal_issue_evidence"]

    # 4. 응답: legal(0.82)·fact(0.68) >= 0.4 & 증거 있음 → 각각 status=1,
    # deepfake(0.35) < 0.4 → status=0 이므로 두 문구만 포함돼야 한다.
    assert "위법의 소지가 있는" in result.short_report
    assert "허위 정보를 포함한" in result.short_report
    assert "AI로 생성된" not in result.short_report
    # danger_evidence: threshold 0.6 이상인 legal(2건)·fact(1건)만 포함, deepfake(0.35)는 제외
    assert len(result.danger_evidence) == 3


@patch("app.features.report.report_service.httpx.post")
def test_AI_연결_실패시_에러_결과를_반환하고_DB에_저장하지_않는다(mock_post, db_session):
    """AI 서버 연결 자체가 실패하면 계약대로 error가 채워진 AnalysisResult를 반환한다."""
    import httpx

    report_repo = ReportRepository(db_session)
    report_service = ReportService(db_session)

    mock_post.side_effect = httpx.ConnectError("Connection refused")

    request = AnalysisRequest(
        youtube_url="https://youtube.com/watch?v=down",
        video_id="v_contract_down",
    )

    result = report_service.analyze_video(request)

    assert result.error is not None
    assert report_repo.get_report_by_video_id("v_contract_down") is None

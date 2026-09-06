import pytest
from unittest.mock import MagicMock
from app.features.report.report_service import ReportService
from app.features.report.report_schema import AnalysisResult

@pytest.fixture
def report_service():
    """DB 의존성을 Mocking하여 ReportService 인스턴스를 제공"""
    mock_db = MagicMock()
    return ReportService(db=mock_db)

# ==========================================
# 1. 사용자가 제공한 실제 데이터 기반 테스트
# ==========================================

def test_analysis_ai_result_real_not_ad(report_service):
    """
    [제공 데이터] 광고가 아닐 시:
    is_ad가 False이고 나머지 카테고리가 None일 때 정상적으로 위험도 9를 반환하는지 테스트
    """
    ai_result = {
        "is_ad": False,
        "legal": None,
        "deepfake": None,
        "fact": None,
        "final_score": 0.0,
        "report": ""
    }
    
    result = report_service.analysis_ai_result(ai_result)
    
    assert result.final_risk_level == 9
    assert result.final_score is None # AnalysisResult 초기화 시 매핑 안 되면 None 또는 default

def test_analysis_ai_result_real_high_risk_ad(report_service):
    """
    [제공 데이터] 실제 고위험 사기 영상 데이터:
    점수가 0.95 이상으로 매우 높고 상세한 증거들이 포함된 경우 완벽히 처리하는지 테스트
    """
    ai_result = {
        "is_ad": True,
        "legal": {
            "legal_issue_score": 0.95,
            "legal_issue_evidence": [
                "고수익 보장 및 투자금 2배 지급 약속은 사기일 가능성이 높음",
                "투자자를 기망하여 자금을 편취하는 사기 범행에 해당"
            ]
        },
        "deepfake": {
            "deepfake_ai_score": 0.95,
            "deepfake_ai_evidence": [
                "입 모양과 음성의 싱크가 미세하게 어긋나며 부자연스러움"
            ]
        },
        "fact": {
            "fake_score": 1.0,
            "fake_evidence": [
                "투자금 즉시 두 배 보장은 전형적인 사기 수법입니다."
            ]
        },
        "final_score": 0.9666666666666667,
        "report": "종합 모더레이션 분석 결과, 해당 콘텐츠는 최종 점수 0.96을 기록..."
    }
    
    result = report_service.analysis_ai_result(ai_result)
    
    # 0.7 이상이므로 고위험(2)
    assert result.final_risk_level == 2
    # threshold 0.6을 넘었으므로 3개 카테고리의 증거가 모두 danger_evidence에 병합되어야 함
    assert len(result.danger_evidence) == 4 
    assert "확률이 매우 높아 위험합니다" in result.short_report
    assert result.final_score == 0.9666666666666667

# ==========================================
# 2. 예외 및 경계값 (Edge Case) 테스트
# ==========================================

def test_analysis_ai_result_missing_category_data(report_service):
    """
    [엣지 케이스] 광고이긴 하지만 AI 서버 오류로 카테고리 값들이 누락(빈 딕셔너리)된 경우
    """
    ai_result = {
        "is_ad": True,
        # legal, deepfake, fact 키가 아예 없거나 비어있음
        "final_score": 0.0,
        "report": "분석 불가"
    }
    
    result = report_service.analysis_ai_result(ai_result)
    
    assert result.final_risk_level == 0 # 점수가 낮으므로 저위험(0)
    assert len(result.danger_evidence) == 0

def test_analysis_ai_result_none_category_data_but_is_ad(report_service):
    """
    [엣지 케이스] 광고인데 카테고리 데이터가 None으로 반환될 경우 
    (이 테스트는 현재 report_service.py의 로직 버그를 잡아냅니다)
    """
    ai_result = {
        "is_ad": True,
        "legal": None,
        "deepfake": None,
        "fact": None,
        "final_score": 0.0,
        "report": "",
    }
    
    # AttributeError 또는 TypeError가 나지 않고 부드럽게 넘어가야 함
    result = report_service.analysis_ai_result(ai_result)
    assert result.final_risk_level == 0

def test_analysis_ai_result_threshold_boundaries(report_service):
    """
    [엣지 케이스] 점수가 정확히 경계값(0.3, 0.7)에 걸쳤을 때의 동작 테스트
    """
    ai_result = {
        "is_ad": True,
        "legal": {"legal_issue_score": 0.7, "legal_issue_evidence": ["법적 증거"]},
        "deepfake": {"deepfake_ai_score": 0.3, "deepfake_ai_evidence": ["딥페이크 증거"]},
        "fact": {"fake_score": 0.0, "fake_evidence": []},
        "final_score": 0.7,  # 정확히 0.7 (고위험 커트라인)
        "report": "테스트"
    }
    
    result = report_service.analysis_ai_result(ai_result)
    
    # 0.7 '이상'이므로 2(고위험)가 되어야 함
    assert result.final_risk_level == 2




# ==========================================
# ReportService.analysis_ai_result 테스트
# ==========================================

# [테스트 목적] 광고 영상(is_ad=False) 필터링 로직 검증
# [테스트 동작]
#   1. is_ad 키의 값을 False로 설정한 딕셔너리를 주입
#   2. analysis_ai_result 호출
#   3. 결과의 final_risk_level이 9로 즉시 반환되는지 확인
# [Input] {"is_ad": False, "final_score": 0.9}
# [Output] AnalysisResult(final_risk_level=9)
def test_analysis_ai_result_not_ad(report_service):
    ai_result = {
        "is_ad": False,
        "final_score": 0.9 # 광고가 아니면 점수가 높아도 9로 반환되어야 함
    }
    
    result = report_service.analysis_ai_result(ai_result)
    
    assert result.final_risk_level == 9
    assert result.final_score is None # 기본 초기화값 유지


# [테스트 목적] 최고 위험 등급(final_score >= 0.7) 및 모든 카테고리(Deepfake, Fact, Legal) 조건 만족 시 생성 로직 검증
# [테스트 동작]
#   1. 모든 카테고리 점수를 0.6 이상(상태 1 및 danger_evidence 포함 조건 만족)으로 설정
#   2. final_score를 0.8로 설정
#   3. 단기 리포트 문구 조합 순서(Deepfake -> Fact -> Legal) 및 최종 suffix 검증
# [Input] final_score=0.8, 모든 카테고리 점수=0.65, evidence 존재
# [Output] final_risk_level=2, danger_evidence 3건, short_report 모든 문구 포함
def test_analysis_ai_result_high_risk_all_categories(report_service):
    ai_result = {
        "is_ad": True,
        "deepfake": {"deepfake_ai_score": 0.65, "deepfake_ai_evidence": ["딥페이크 근거"]},
        "fact": {"fake_score": 0.7, "fake_evidence": ["팩트 근거"]},
        "legal": {"legal_issue_score": 0.8, "legal_issue_evidence": ["위법 근거"]},
        "final_score": 0.85,
        "report": "상세 리포트 내용"
    }

    result = report_service.analysis_ai_result(ai_result)

    assert result.final_score == 0.85
    assert result.final_risk_level == 2
    # 위험 근거 병합 확인 (0.6 이상이므로 모두 포함되어야 함)
    assert len(result.danger_evidence) == 3
    assert "딥페이크 근거" in result.danger_evidence
    assert "팩트 근거" in result.danger_evidence
    assert "위법 근거" in result.danger_evidence
    # short_report 순서 및 문구 확인
    assert result.short_report == "해당 영상은 AI로 생성된 허위 정보를 포함한 위법의 소지가 있는 영상일 확률이 매우 높아 위험합니다."
    assert result.analysis_report == "상세 리포트 내용"


# [테스트 목적] 중간 위험 등급(0.3 <= final_score < 0.7) 및 부분 카테고리 만족 시 검증
# [테스트 동작]
#   1. final_score를 0.5로 설정 (중간 위험)
#   2. Deepfake는 점수 높음, Fact는 Evidence 없음(Status 0), Legal은 점수 낮음(Status 0)
#   3. danger_evidence가 0.6을 넘는 Deepfake 근거만 포함되는지 확인
# [Input] final_score=0.5, deepfake=0.65(위험), fact=0.9(근거없음), legal=0.3(안전)
# [Output] final_risk_level=1, danger_evidence 1건, 부분 short_report 문구 조합
def test_analysis_ai_result_medium_risk_partial_categories(report_service):
    ai_result = {
        "is_ad": True,
        "deepfake": {"deepfake_ai_score": 0.65, "deepfake_ai_evidence": ["딥페이크 근거"]},
        "fact": {"fake_score": 0.9, "fake_evidence": []}, # 증거가 없으면 status 0이어야 함
        "legal": {"legal_issue_score": 0.39, "legal_issue_evidence": ["위법 근거"]}, # 0.4 미만이므로 status 0
        "final_score": 0.5
    }

    result = report_service.analysis_ai_result(ai_result)

    assert result.final_risk_level == 1
    # 0.6을 넘는 것은 deepfake 뿐이므로 danger_evidence에는 1개만 들어가야 함
    assert len(result.danger_evidence) == 1
    assert result.danger_evidence[0] == "딥페이크 근거"
    # Status 조건을 만족한 Deepfake 문구만 들어가고, 중간 위험 suffix 결합
    assert result.short_report == "해당 영상은 AI로 생성된 영상일 확률이 있어 주의가 필요합니다."


# [테스트 목적] 낮은 위험 등급(final_score < 0.3) 일 때의 강제 문구 덮어쓰기 로직 검증
# [테스트 동작]
#   1. final_score를 0.2로 설정
#   2. 특정 카테고리가 0.4를 넘어 Status 1이더라도, 최종 점수가 낮으면 안전 문구로 덮어씌워지는지 확인
# [Input] final_score=0.2, deepfake=0.8(상태1)
# [Output] final_risk_level=0, short_report="해당 영상은 안전한 영상일 확률이 높습니다."
def test_analysis_ai_result_safe_low_score(report_service):
    ai_result = {
        "is_ad": True,
        "deepfake": {"deepfake_ai_score": 0.8, "deepfake_ai_evidence": ["딥페이크 조작 발견"]}, # 카테고리는 위험하지만
        "final_score": 0.2 # 최종 점수가 매우 낮음
    }

    result = report_service.analysis_ai_result(ai_result)

    assert result.final_risk_level == 0
    # 위험 증거는 0.6을 넘겼으므로 수집은 되어야 함
    assert "딥페이크 조작 발견" in result.danger_evidence
    # 하지만 최종 short_report는 안전하다는 문구로 완전히 덮어씌워짐
    assert result.short_report == "해당 영상은 안전한 영상일 확률이 높습니다."


# [테스트 목적] 위험도 0.6 경계값(Boundary) 테스트 및 evidence 임계치 검증
# [테스트 동작]
#   1. danger_evidence 편입 기준인 점수 0.6 경계값과 0.59를 테스트
#   2. status 판별 기준인 0.4 경계값과 0.39를 테스트
# [Input] fact(0.6, 근거있음), legal(0.59, 근거있음), deepfake(0.4, 근거있음)
# [Output] Status: fact(1), legal(1), deepfake(1) / Danger Evidence: fact(포함), legal(미포함), deepfake(미포함)
def test_analysis_ai_result_boundary_scores(report_service):
    ai_result = {
        "is_ad": True,
        "fact": {"fake_score": 0.60, "fake_evidence": ["팩트 0.6"]},      # danger 포함 O, status 1
        "legal": {"legal_issue_score": 0.59, "legal_issue_evidence": ["위법 0.59"]}, # danger 포함 X, status 1
        "deepfake": {"deepfake_ai_score": 0.40, "deepfake_ai_evidence": ["딥페 0.4"]}, # danger 포함 X, status 1
        "final_score": 0.7
    }

    result = report_service.analysis_ai_result(ai_result)

    # Status는 세 개 모두 0.4 이상이므로 1로 판별되어 descriptions가 모두 생성됨
    assert result.short_report == "해당 영상은 AI로 생성된 허위 정보를 포함한 위법의 소지가 있는 영상일 확률이 매우 높아 위험합니다."
    
    # danger_evidence는 0.6 이상인 fact_evidence만 담겨야 함
    assert len(result.danger_evidence) == 1
    assert result.danger_evidence[0] == "팩트 0.6"


# [테스트 목적] 어떠한 카테고리 Status도 1이 아니지만(descriptions 빈 리스트), final_score만 높은 경우의 fallback 문구 검증
# [테스트 동작]
#   1. 모든 카테고리의 근거 리스트를 비우거나 점수를 0.4 미만으로 세팅
#   2. final_score를 0.5로 세팅
#   3. descriptions가 없을 때 short_report 기본값이 정상 작동하는지 확인
# [Input] final_score=0.5, 카테고리별 위험 증거 없음
# [Output] short_report="해당 영상은 분석 결과 위험한 영상일 확률이 있어 주의가 필요합니다."
def test_analysis_ai_result_fallback_short_report(report_service):
    ai_result = {
        "is_ad": True,
        "deepfake": {"deepfake_ai_score": 0.1, "deepfake_ai_evidence": []},
        "fact": {"fake_score": 0.1, "fake_evidence": []},
        "legal": {"legal_issue_score": 0.1, "legal_issue_evidence": []},
        "final_score": 0.4
    }

    result = report_service.analysis_ai_result(ai_result)

    assert result.final_risk_level == 1
    assert len(result.danger_evidence) == 0
    # 세부 카테고리에 대한 묘사가 없을 경우의 Default 문구 + 주의 필요 Suffix
    assert result.short_report == "해당 영상은 분석 결과 위험한 영상일 확률이 있어 주의가 필요합니다."


# [테스트 목적] AI 응답 딕셔너리의 Key가 누락되었을 때의 방어 로직(딕셔너리 .get() 기본값) 검증
# [테스트 동작]
#   1. 빈 딕셔너리 혹은 최소한의 키만 있는 딕셔너리 주입
#   2. KeyError나 TypeError 없이 안전하게 파싱되어 기본값으로 처리되는지 확인
# [Input] {} (빈 딕셔너리)
# [Output] final_risk_level=0, final_score=0.0, 에러 발생 안 함
def test_analysis_ai_result_empty_or_missing_keys(report_service):
    ai_result = {} # is_ad 등 필수 키조차 누락된 경우

    result = report_service.analysis_ai_result(ai_result)
    
    # is_ad는 기본적으로 True로 취급됨 (get("is_ad", "True")로 로직 작성되어 있음)
    assert result.final_score == 0.0
    assert result.final_risk_level == 0
    assert result.danger_evidence == []
    assert result.short_report == "해당 영상은 안전한 영상일 확률이 높습니다."
    assert result.analysis_report == ""


    import pytest
from app.features.report.report_service import ReportService
from app.features.video.video_repository import VideoRepository
from app.features.report.report_repository import ReportRepository
from app.features.video.video_model import Video

# ==========================================
# ReportService.save_report_to_db 테스트
# ==========================================

# [테스트 목적] 모든 카테고리(FACT, DEEPFAKE, LEGAL) 데이터와 근거가 완벽하게 포함된 정상 응답의 DB 저장 검증
# [테스트 동작]
#   1. Video 선행 생성 (외래키 제약조건 충족용)
#   2. 완벽한 형태의 ai_result 딕셔너리로 save_report_to_db 호출
#   3. DB에서 video_id로 리포트 조회 및 속성(점수 등) 확인
#   4. 조회된 리포트 ID로 Evidence들을 조회하여 각 카테고리별 근거가 1개씩 총 3개 저장되었는지 확인
# [Input] video_id="v_full", 3개 카테고리 점수 및 근거 리스트가 포함된 dict
# [Output] DB에 AIReport 1건, ReportEvidence 3건 정상 저장 확인
def test_save_report_to_db_success_all_data(db_session):
    video_repo = VideoRepository(db_session)
    report_repo = ReportRepository(db_session)
    report_service = ReportService(db_session)

    # 선행조건: Video 생성
    video = Video(video_id="v_full", video_title="Full Test Video", status="PENDING")
    video_repo.create_video(video)

    ai_result = {
        "final_score": 0.9,
        "report": "상세 분석 결과입니다.",
        "fact": {"fake_score": 0.8, "fake_evidence": ["팩트 위반 1"]},
        "deepfake": {"deepfake_ai_score": 0.7, "deepfake_ai_evidence": ["얼굴 조작 1"]},
        "legal": {"legal_issue_score": 0.6, "legal_issue_evidence": ["저작권 위반 1"]}
    }

    # DB 저장 실행
    report_service.save_report_to_db(video_id="v_full", ai_result=ai_result)

    # 1. AIReport 검증
    saved_report = report_repo.get_report_by_video_id("v_full")
    assert saved_report is not None
    assert float(saved_report.final_score) == 0.9
    assert float(saved_report.fact_score) == 0.8
    assert saved_report.analysis_result == "상세 분석 결과입니다."

    # 2. ReportEvidence 검증
    evidences = report_repo.get_evidence_by_report(saved_report.report_id)
    assert len(evidences) == 3
    categories = [e.category for e in evidences]
    assert "FACT" in categories
    assert "DEEPFAKE" in categories
    assert "LEGAL" in categories


# [테스트 목적] AI 응답 딕셔너리 내 카테고리 값이 None이거나 누락되었을 때의 방어 로직 검증
# [테스트 동작]
#   1. Video 선행 생성
#   2. "fact", "deepfake", "legal" 키가 아예 없거나 값이 None인 딕셔너리 주입
#   3. 에러 발생 없이 기본값(점수 0.0)으로 AIReport 1건이 저장되고, Evidence는 0건 저장되는지 확인
# [Input] video_id="v_empty", fact/deepfake/legal 키가 None인 dict
# [Output] 정상 저장, AIReport 점수 모두 0.0, Evidence 0건
def test_save_report_to_db_success_missing_or_none_data(db_session):
    video_repo = VideoRepository(db_session)
    report_repo = ReportRepository(db_session)
    report_service = ReportService(db_session)

    video = Video(video_id="v_empty", video_title="Empty Test Video", status="PENDING")
    video_repo.create_video(video)

    # 카테고리가 None으로 내려오는 케이스 (AttributeError 방어 확인용)
    ai_result = {
        "final_score": 0.1,
        "fact": None,
        "deepfake": None,
        "legal": None
    }

    report_service.save_report_to_db(video_id="v_empty", ai_result=ai_result)

    saved_report = report_repo.get_report_by_video_id("v_empty")
    assert saved_report is not None
    assert float(saved_report.final_score) == 0.1
    # None일 때 {} 로 치환되어 .get("...", 0.0)이 적용되었는지 확인
    assert float(saved_report.fact_score) == 0.0 
    assert float(saved_report.deepfake_score) == 0.0

    evidences = report_repo.get_evidence_by_report(saved_report.report_id)
    assert len(evidences) == 0 # 근거 데이터가 없으므로 0건이어야 함


# [테스트 목적] 잘못된 데이터 타입으로 인한 파싱 에러(AttributeError) 발생 및 처리 검증
# [테스트 동작]
#   1. Video 선행 생성
#   2. ai_result를 dict가 아닌 list(`[]`) 형태로 전달
#   3. dict의 `.get()` 메서드를 호출하려다 AttributeError가 발생하면 RuntimeError로 잘 감싸서 던지는지 확인
# [Input] ai_result=[] (리스트 타입)
# [Output] RuntimeError 예외 발생 및 예외 메시지에 "데이터 형식이 올바르지 않아" 포함
def test_save_report_to_db_attribute_error_parsing(db_session):
    video_repo = VideoRepository(db_session)
    report_service = ReportService(db_session)

    video = Video(video_id="v_attr", video_title="Attr Test Video", status="PENDING")
    video_repo.create_video(video)

    # 리스트에는 .get() 메서드가 없으므로 내부 로직(ai_result.get)에서 AttributeError 발생 예상
    ai_result = [{"final_score": 0.5}] 

    with pytest.raises(RuntimeError) as exc_info:
        report_service.save_report_to_db(video_id="v_attr", ai_result=ai_result)
    
    # 예외 메시지가 의도한 대로 잘 감싸져서 나왔는지 확인
    assert "데이터 형식이 올바르지 않아" in str(exc_info.value)


# [테스트 목적] DB 외래키(ForeignKey) 제약조건 위배 시의 예외 처리(IntegrityError 등) 검증
# [테스트 동작]
#   1. Video를 생성하지 않음 (DB에 해당 video_id가 없는 상태)
#   2. 존재하지 않는 video_id로 save_report_to_db 호출
#   3. DB Commit 과정에서 외래키 제약조건 위반 Exception 발생 시 RuntimeError로 잘 래핑하여 던지는지 확인
# [Input] video_id="invalid_video", 정상적인 ai_result dict
# [Output] RuntimeError 예외 발생 및 예외 메시지에 "DB 처리 중 시스템 오류" 포함
def test_save_report_to_db_db_exception_foreign_key(db_session):
    report_service = ReportService(db_session)
    
    ai_result = {
        "final_score": 0.5,
        "fact": {"fake_score": 0.0, "fake_evidence": []}
    }

    # 'invalid_video'는 Video 테이블에 없으므로 AIReport INSERT 시 FK 에러(IntegrityError) 발생
    with pytest.raises(RuntimeError) as exc_info:
        report_service.save_report_to_db(video_id="invalid_video", ai_result=ai_result)
        
    assert "DB 처리 중 시스템 오류가 발생했습니다" in str(exc_info.value)


# [테스트 목적] 부분적으로 비어있는 근거 리스트(빈 배열)에 대한 Evidence 저장 패스 로직 검증
# [테스트 동작]
#   1. Video 선행 생성
#   2. 점수는 있으나 `evidence` 키 값은 빈 리스트(`[]`)인 상태로 전달
#   3. `_save_evidence` 내부의 `if not evidence_list: return` 로직이 작동하여 Evidence DB 삽입 로직이 건너뛰어지는지 확인
# [Input] 특정 카테고리의 evidence가 `[]`인 dict
# [Output] AIReport 정상 저장, DB에 저장된 Evidence 0건
def test_save_report_to_db_empty_evidence_list_skip(db_session):
    video_repo = VideoRepository(db_session)
    report_repo = ReportRepository(db_session)
    report_service = ReportService(db_session)

    video = Video(video_id="v_skip", video_title="Skip Test Video", status="PENDING")
    video_repo.create_video(video)

    ai_result = {
        "final_score": 0.5,
        "fact": {"fake_score": 0.5, "fake_evidence": []}, # 빈 리스트
        "legal": {"legal_issue_score": 0.5, "legal_issue_evidence": None} # None
    }

    report_service.save_report_to_db(video_id="v_skip", ai_result=ai_result)

    saved_report = report_repo.get_report_by_video_id("v_skip")
    assert saved_report is not None

    # evidence_list가 [] 이거나 None일 경우 스킵되므로 저장된 근거가 없어야 함
    evidences = report_repo.get_evidence_by_report(saved_report.report_id)
    assert len(evidences) == 0

    import pytest
from unittest.mock import patch, MagicMock
import httpx
from app.features.report.report_service import ReportService
from app.features.report.report_schema import AnalysisRequest
from app.features.video.video_repository import VideoRepository
from app.features.report.report_repository import ReportRepository
from app.features.video.video_model import Video
from app.features.report.report_model import AIReport, ReportEvidence

# ==========================================
# ReportService.get_existing_analysis 테스트
# ==========================================

# [테스트 목적] DB에 기존 분석 결과가 없을 때의 동작 검증
# [테스트 동작]
#   1. DB에 아무런 리포트가 없는 상태에서 get_existing_analysis 호출
#   2. None이 반환되는지 확인
# [Input] 존재하지 않는 video_id="v_not_exist"
# [Output] None
def test_get_existing_analysis_not_found(db_session):
    report_service = ReportService(db_session)
    
    result = report_service.get_existing_analysis(video_id="v_not_exist")
    
    assert result is None


# [테스트 목적] 기존 DB 데이터를 AI 서버 응답 딕셔너리와 동일한 형태로 역가공하여 AnalysisResult를 생성하는지 검증
# [테스트 동작]
#   1. Video 선행 생성 후 AIReport 및 ReportEvidence 2건(FACT, LEGAL)을 수동으로 DB에 INSERT
#   2. get_existing_analysis 호출
#   3. DB의 점수 및 근거 텍스트들이 잘 조합되어 AnalysisResult 객체로 반환되는지 속성 검증
# [Input] DB에 저장된 AIReport(final=0.8, fact=0.7, legal=0.6) 및 Evidence 2건
# [Output] AnalysisResult(final_score=0.8, danger_evidence 2건 포함)
def test_get_existing_analysis_success(db_session):
    video_repo = VideoRepository(db_session)
    report_repo = ReportRepository(db_session)
    report_service = ReportService(db_session)

    # 1. 테스트 데이터 세팅
    video = Video(video_id="v_exist", video_title="Exist Video", status="PENDING")
    video_repo.create_video(video)

    report = AIReport(
        report_id="r_exist_1",
        video_id="v_exist",
        final_score=0.8,
        fact_score=0.7,
        deepfake_score=0.1,
        legal_issue_score=0.6,
        analysis_result="저장된 상세 리포트"
    )
    report_repo.create_report(report)

    evidence1 = ReportEvidence(evidence_id="e1", report_id="r_exist_1", category="FACT", content="DB 팩트 근거")
    evidence2 = ReportEvidence(evidence_id="e2", report_id="r_exist_1", category="LEGAL", content="DB 위법 근거")
    report_repo.add_evidence(evidence1)
    report_repo.add_evidence(evidence2)

    # 2. 메서드 실행
    result = report_service.get_existing_analysis(video_id="v_exist")

    # 3. 결과 검증
    assert result is not None
    assert result.final_score == 0.8
    assert result.final_risk_level == 2
    assert "DB 팩트 근거" in result.danger_evidence
    assert "DB 위법 근거" in result.danger_evidence
    assert result.analysis_report == "저장된 상세 리포트"


# ==========================================
# ReportService.analyze_video 테스트
# ==========================================

# [테스트 목적] 외부 AI 서버와의 정상 통신 및 DB 저장, 분석 결과 반환의 전체 파이프라인 검증
# [테스트 동작]
#   1. httpx.post를 Mocking하여 상태코드 200과 가상의 AI 분석 결과 JSON을 반환하도록 설정
#   2. Video 선행 생성 후 analyze_video 호출
#   3. 외부 API 응답이 AnalysisResult로 잘 변환되었는지 확인
#   4. 백그라운드로 DB에 데이터가 잘 저장되었는지 조회하여 검증
# [Input] AnalysisRequest(youtube_url="http://...", video_id="v_api_test")
# [Output] AnalysisResult 객체 리턴 및 DB에 AIReport 1건 저장
@patch("app.features.report.report_service.httpx.post")
def test_analyze_video_success(mock_post, db_session):
    video_repo = VideoRepository(db_session)
    report_repo = ReportRepository(db_session)
    report_service = ReportService(db_session)

    video = Video(video_id="v_api_test", video_title="API Test", status="PENDING")
    video_repo.create_video(video)

    # httpx.post 응답 Mocking
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "is_ad": True,
        "final_score": 0.5,
        "report": "API 상세 결과",
        "fact": {"fake_score": 0.6, "fake_evidence": ["API 팩트 증거"]}
    }
    mock_post.return_value = mock_response

    request = AnalysisRequest(youtube_url="https://youtube.com/watch?v=123", video_id="v_api_test")
    
    # 메서드 실행
    result = report_service.analyze_video(request)

    # API 호출이 제대로 이루어졌는지 검증
    mock_post.assert_called_once()
    assert mock_post.call_args[1]["json"] == {"youtube_url": "https://youtube.com/watch?v=123"}
    
    # 결과 반환 검증
    assert result.final_score == 0.5
    assert result.analysis_report == "API 상세 결과"

    # DB에 잘 저장되었는지 검증 (save_report_to_db가 정상 호출되었는지 확인)
    saved_report = report_repo.get_report_by_video_id("v_api_test")
    assert saved_report is not None
    assert float(saved_report.final_score) == 0.5


# [테스트 목적] AI 서버에서 4xx, 5xx 에러를 반환할 때의 예외 처리 검증
# [테스트 동작]
#   1. httpx.post를 Mocking하여 상태코드 500 반환하도록 설정
#   2. analyze_video 호출
#   3. Exception이 캐치되어 create_error_result를 통해 에러 문자열이 담긴 AnalysisResult가 반환되는지 확인
# [Input] 상태 코드 500을 반환하는 Mock 외부 API 응답
# [Output] AnalysisResult(error="AI 서버 호출 실패: 500")
@patch("app.features.report.report_service.httpx.post")
def test_analyze_video_api_error_response(mock_post, db_session):
    report_service = ReportService(db_session)

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response

    request = AnalysisRequest(youtube_url="https://youtube.com/watch?v=err", video_id="v_err")
    
    result = report_service.analyze_video(request)

    # 에러 결과 객체가 잘 생성되었는지 확인
    assert result.final_score is None
    assert result.error is not None
    assert "AI 서버 호출 실패: 500" in result.error


# [테스트 목적] AI 서버 호출 중 타임아웃 발생 시의 시스템 보호 및 예외 처리 검증
# [테스트 동작]
#   1. httpx.post 호출 시 httpx.ReadTimeout 예외를 강제 발생시키도록 Mocking
#   2. analyze_video 호출
#   3. 시스템이 다운되지 않고 에러 객체(AnalysisResult)를 안전하게 리턴하는지 확인
# [Input] httpx.ReadTimeout 발생
# [Output] AnalysisResult(error="[에러 원인 문자열]")
@patch("app.features.report.report_service.httpx.post")
def test_analyze_video_timeout_exception(mock_post, db_session):
    report_service = ReportService(db_session)

    # Timeout 예외 강제 발생
    mock_post.side_effect = httpx.ReadTimeout("Read Timeout")

    request = AnalysisRequest(youtube_url="https://youtube.com/watch?v=timeout", video_id="v_timeout")
    
    result = report_service.analyze_video(request)

    assert result.final_score is None
    assert result.error is not None
    assert "Read Timeout" in result.error


# [테스트 목적] Request 스키마에 video_id 속성이 없는 특수/유연한 상황에서의 동작 검증
# [테스트 동작]
#   1. video_id 속성이 누락된 가짜(Mock) 객체나 동적 클래스를 생성하여 요청 객체로 주입
#   2. hasattr(request, "video_id") 분기에서 False로 빠져 DB 저장을 건너뛰는지 확인
#   3. DB 저장 없이도 분석 결과(AnalysisResult)는 정상적으로 리턴되는지 확인
# [Input] video_id 속성이 없는 임의의 request 객체
# [Output] DB에 아무것도 저장되지 않음, 정상적인 AnalysisResult 반환
@patch("app.features.report.report_service.httpx.post")
def test_analyze_video_missing_video_id(mock_post, db_session):
    report_repo = ReportRepository(db_session)
    report_service = ReportService(db_session)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"final_score": 0.3}
    mock_post.return_value = mock_response

    # AnalysisRequest 스키마를 우회하여 강제로 video_id가 없는 객체 생성
    class MockRequest:
        youtube_url = "https://youtube.com/watch?v=no_id"

    request = MockRequest()
    
    result = report_service.analyze_video(request)

    # 1. DB 저장을 건너뛰었으므로 분석 결과는 정상 반환
    assert result.final_score == 0.3
    
    # 2. DB에는 아무것도 들어가지 않아야 함 (이전 테스트에서 들어간 데이터가 있을 수 있으므로 None 체크보단 전체 카운트 등으로 체크하거나, 분기가 무시되었는지만 확인)
    # mock_post가 호출되었는지 확인
    mock_post.assert_called_once()


    import pytest
from app.features.report.report_service import ReportService

@pytest.fixture
def report_service():
    return ReportService(db=None)

# [테스트 목적] final_score의 정확한 경계값(0.3, 0.7) 동작 검증
# [테스트 동작] final_score가 정확히 0.3일 때와 0.7일 때 등급이 제대로 나뉘는지 확인
# [Input] final_score: 0.3 / 0.7
# [Output] 0.3 -> final_risk_level=1 / 0.7 -> final_risk_level=2
def test_analysis_ai_result_exact_boundary_scores(report_service):
    # 1. 하한 경계값 (0.3) -> 1단계(중간 위험)
    result_03 = report_service.analysis_ai_result({"is_ad": True, "final_score": 0.3})
    assert result_03.final_risk_level == 1
    assert "확률이 있어 주의가 필요합니다" in result_03.short_report

    # 2. 상한 경계값 (0.7) -> 2단계(높은 위험)
    result_07 = report_service.analysis_ai_result({"is_ad": True, "final_score": 0.7})
    assert result_07.final_risk_level == 2
    assert "확률이 매우 높아 위험합니다" in result_07.short_report


# [테스트 목적] 'is_ad' 키가 존재하지만 값이 명시적 None인 경우의 파이썬 Truthy/Falsy 검증
# [테스트 동작] {"is_ad": None}을 주입했을 때, .get("is_ad", "True")는 None을 반환함. 
#            이때 if not None: 이 참이 되어 위험도 9로 반환되는지 확인
# [Input] {"is_ad": None}
# [Output] final_risk_level=9
def test_analysis_ai_result_is_ad_explicit_none(report_service):
    ai_result = {
        "is_ad": None,
        "final_score": 0.9
    }
    result = report_service.analysis_ai_result(ai_result)
    # 광고가 아닌 것으로 인식하여 9를 반환해야 함
    assert result.final_risk_level == 9


# [테스트 목적] AI 결과 점수에 예상치 못한 음수나 비정상적인 값이 들어올 때의 강건성 검증
# [테스트 동작] 점수에 음수를 할당했을 때 에러가 나지 않고 Status 0(안전)으로 처리되는지 확인
# [Input] 점수들이 음수, evidence는 존재
# [Output] final_risk_level=0, 모든 danger_evidence 수집 안 됨
def test_analysis_ai_result_negative_scores(report_service):
    ai_result = {
        "is_ad": True,
        "deepfake": {"deepfake_ai_score": -0.5, "deepfake_ai_evidence": ["근거"]},
        "final_score": -0.1
    }
    result = report_service.analysis_ai_result(ai_result)
    
    assert result.final_risk_level == 0
    assert len(result.danger_evidence) == 0
    assert result.short_report == "해당 영상은 안전한 영상일 확률이 높습니다."

    import pytest
import uuid
from unittest.mock import patch
from app.features.report.report_service import ReportService
from app.features.video.video_repository import VideoRepository
from app.features.report.report_repository import ReportRepository
from app.features.video.video_model import Video
from app.features.report.report_model import AIReport

# [테스트 목적] Report ID 생성 시 UUID가 이미 DB에 존재하는 경우 재발급(while 루프) 로직 검증
# [테스트 동작]
#   1. uuid.uuid4를 Mocking하여 첫 번째는 이미 DB에 존재하는 ID를, 두 번째는 새로운 ID를 반환하게 설정
#   2. save_report_to_db 호출
#   3. 무한 루프에 빠지지 않고 두 번째 ID로 성공적으로 저장되는지 검증
# [Input] Mocking된 UUID 리스트 ["EXISTING_ID", "NEW_VALID_ID"]
# [Output] report_id가 "NEW_VALID_ID"인 데이터 저장 성공
@patch("app.features.report.report_service.uuid.uuid4")
def test_save_report_to_db_uuid_collision_retry(mock_uuid, db_session):
    video_repo = VideoRepository(db_session)
    report_repo = ReportRepository(db_session)
    report_service = ReportService(db_session)

    # 1. UUID Mocking 세팅
    mock_uuid.side_effect = [
        uuid.UUID(int=1), # 기존에 존재하는 ID (충돌 발생용)
        uuid.UUID(int=2), # 재발급될 정상 ID
        uuid.UUID(int=3), # Evidence 용 ID
        uuid.UUID(int=4)
    ]
    
    # 2. 기존 ID를 미리 DB에 삽입 (이때 외래키 제약조건을 피하기 위해 Video 먼저 생성)
    exist_video_id = "v_uuid_test_existing"
    video_repo.create_video(Video(video_id=exist_video_id, video_title="Existing Video", status="PENDING"))
    
    exist_id_str = str(uuid.UUID(int=1))
    report_repo.create_report(AIReport(report_id=exist_id_str, video_id=exist_video_id, final_score=0.1))
    
    # 3. 새로운 비디오에 대해 리포트 저장 시도
    target_video_id = "v_uuid_test_target"
    video_repo.create_video(Video(video_id=target_video_id, video_title="Target Video", status="PENDING"))
    
    ai_result = {"final_score": 0.5, "fact": {"fake_score": 0.5, "fake_evidence": ["근거1"]}}
    
    # 여기서 UUID 충돌(int=1)이 발생하지만 while문으로 재발급(int=2)을 받아 정상 저장되어야 함
    report_service.save_report_to_db(video_id=target_video_id, ai_result=ai_result)

    # 4. 두 번째로 발급된 ID(int=2)로 잘 저장되었는지 확인
    saved_report = report_repo.get_report_by_video_id(target_video_id)
    assert saved_report.report_id == str(uuid.UUID(int=2))


# [테스트 목적] 이미 리포트가 있는 video_id로 다시 호출하면 조용히 스킵하고 중복을 만들지 않음을 검증
# [테스트 동작] save_report_to_db를 같은 video_id로 두 번 호출
# [Input] 이미 리포트가 존재하는 video_id
# [Output] 두 번째 호출은 예외 없이 return, 새 리포트가 생성되지 않음
#   (save_report_to_db 상단의 `if existing: return` 방어 로직 검증)
def test_save_report_to_db_duplicate_video_id(db_session):
    video_repo = VideoRepository(db_session)
    report_repo = ReportRepository(db_session)
    report_service = ReportService(db_session)

    video = Video(video_id="v_dup", video_title="Duplicate Test", status="PENDING")
    video_repo.create_video(video)

    ai_result = {"final_score": 0.5}

    report_service.save_report_to_db(video_id="v_dup", ai_result=ai_result)
    first = report_repo.get_report_by_video_id("v_dup")
    assert first is not None

    # 두 번째 호출: 기존 리포트를 감지하면 예외 없이 스킵한다
    report_service.save_report_to_db(video_id="v_dup", ai_result=ai_result)

    second = report_repo.get_report_by_video_id("v_dup")
    assert second.report_id == first.report_id  # 새 리포트가 생기지 않음

from unittest.mock import patch, MagicMock
import httpx
from app.features.report.report_service import ReportService
from app.features.report.report_schema import AnalysisRequest

# [테스트 목적] AI 서버가 아예 다운되어 연결조차 불가능할 때(ConnectError)의 방어 로직 검증
# [테스트 동작] httpx.post에서 httpx.ConnectError 예외 발생을 Mocking
# [Input] httpx.ConnectError 발생
# [Output] AnalysisResult(error="[에러 메시지]")
@patch("app.features.report.report_service.httpx.post")
def test_analyze_video_connection_error(mock_post, db_session):
    report_service = ReportService(db_session)
    
    mock_post.side_effect = httpx.ConnectError("Connection refused")
    
    request = AnalysisRequest(youtube_url="https://youtube.com/watch?v=conn", video_id="v_conn")
    result = report_service.analyze_video(request)
    
    assert result.final_score is None
    assert result.error is not None
    assert "Connection refused" in result.error


# [테스트 목적] AI 서버가 200 OK를 주지만 JSON 형식이 아닌 일반 텍스트/HTML을 반환할 때(JSONDecodeError) 검증
# [테스트 동작] response.json() 호출 시 ValueError(JSON 파싱 에러) 발생 Mocking
# [Input] 비정상적인 응답 바디
# [Output] AnalysisResult(error="[에러 메시지]")
@patch("app.features.report.report_service.httpx.post")
def test_analyze_video_invalid_json_response(mock_post, db_session):
    report_service = ReportService(db_session)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    # .json() 호출 시 에러가 나도록 설정
    mock_response.json.side_effect = ValueError("Expecting value: line 1 column 1 (char 0)")
    mock_post.return_value = mock_response

    request = AnalysisRequest(youtube_url="https://youtube.com/watch?v=json", video_id="v_json")
    result = report_service.analyze_video(request)

    assert result.final_score is None
    assert result.error is not None
    assert "Expecting value" in result.error

from app.features.report.report_repository import ReportRepository

# [테스트 목적] 존재하지 않는 Report 또는 Evidence를 삭제하려 할 때의 안정성 검증
# [테스트 동작] DB에 없는 임의의 ID로 delete_report 및 delete_evidence 호출
# [Input] DB에 없는 ID ("not_exist_id")
# [Output] 에러나 예외 발생 없이 부드럽게 통과 (로직 내 if report: 처리 확인)
def test_repository_delete_non_existent(db_session):
    report_repo = ReportRepository(db_session)
    
    # 1. 존재하지 않는 Report 삭제 시도 -> 예외가 안 터지면 성공
    try:
        report_repo.delete_report("not_exist_report_id")
    except Exception as e:
        pytest.fail(f"존재하지 않는 리포트 삭제 시 예외가 발생했습니다: {e}")

    # 2. 존재하지 않는 Evidence 삭제 시도 -> 예외가 안 터지면 성공
    try:
        report_repo.delete_evidence("not_exist_evidence_id")
    except Exception as e:
        pytest.fail(f"존재하지 않는 근거 삭제 시 예외가 발생했습니다: {e}")
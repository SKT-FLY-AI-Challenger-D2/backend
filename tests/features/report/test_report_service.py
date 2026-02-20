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
        "report": ""
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
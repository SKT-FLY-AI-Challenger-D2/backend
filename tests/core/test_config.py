# Settings의 필수 설정 누락 표현 검증 (TASK-04)

import importlib


def _reload_config(monkeypatch, **env):
    for key in ("DB_URL", "AI_BASE_URL"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    import app.core.config as config_module

    importlib.reload(config_module)
    return config_module


def test_DB_URL이_없으면_None이고_실제_비밀값_기본값을_쓰지_않는다(monkeypatch):
    config_module = _reload_config(monkeypatch)
    assert config_module.settings.DB_URL is None


def test_DB_URL_환경변수가_그대로_반영된다(monkeypatch):
    config_module = _reload_config(monkeypatch, DB_URL="mysql+pymysql://user:pw@host:3306/db")
    assert config_module.settings.DB_URL == "mysql+pymysql://user:pw@host:3306/db"


def test_AI_BASE_URL_기본값은_로컬_주소다(monkeypatch):
    config_module = _reload_config(monkeypatch)
    assert config_module.settings.AI_BASE_URL == "http://127.0.0.1:8001"


def test_AI_BASE_URL_환경변수가_그대로_반영된다(monkeypatch):
    config_module = _reload_config(monkeypatch, AI_BASE_URL="http://ai-server:9000")
    assert config_module.settings.AI_BASE_URL == "http://ai-server:9000"

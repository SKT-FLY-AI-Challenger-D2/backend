# DB_URL 누락 시 import는 성공하고, 실제 사용 시점에만 명확한 오류를 내는지 검증 (TASK-04, FR-10)

import importlib

import pytest


def _reload_database(monkeypatch, db_url: str | None):
    monkeypatch.delenv("DB_URL", raising=False)
    if db_url is not None:
        monkeypatch.setenv("DB_URL", db_url)

    import app.core.config as config_module
    importlib.reload(config_module)

    import app.core.database as database_module
    importlib.reload(database_module)
    return database_module


def test_DB_URL이_없어도_import는_성공한다(monkeypatch):
    database_module = _reload_database(monkeypatch, None)
    assert database_module.engine is not None
    assert database_module.Base is not None


def test_DB_URL이_없으면_engine_사용_시점에_명확한_오류를_낸다(monkeypatch):
    database_module = _reload_database(monkeypatch, None)

    # main.py의 lifespan이 Base.metadata.create_all(bind=engine)에서 실제로
    # engine 속성(.connect 등)에 접근하는 순간과 동일한 상황을 재현한다.
    with pytest.raises(RuntimeError, match="DB_URL"):
        database_module.engine.connect()


def test_DB_URL이_없으면_get_db도_명확한_오류를_낸다(monkeypatch):
    database_module = _reload_database(monkeypatch, None)

    with pytest.raises(RuntimeError, match="DB_URL"):
        next(database_module.get_db())


def test_DB_URL이_있으면_get_db가_요청마다_다른_세션을_만든다(monkeypatch):
    database_module = _reload_database(monkeypatch, "sqlite:///:memory:")

    gen1 = database_module.get_db()
    gen2 = database_module.get_db()
    db1 = next(gen1)
    db2 = next(gen2)
    try:
        assert db1 is not db2
    finally:
        gen1.close()
        gen2.close()

from app.config import Settings


def test_uses_current_flash_lite_model_by_default(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    assert Settings.from_env().gemini_model == "gemini-3.5-flash-lite"

"""Unit tests for application settings."""

from config.settings import Settings, get_settings


def test_settings_defaults():
    settings = Settings()
    assert settings.app_name == "german-bureaucracy-agent"
    assert settings.api_port == 8000
    assert settings.agent_default_locale == "en"
    assert settings.max_upload_size_mb == 20


def test_get_settings_cached():
    a = get_settings()
    b = get_settings()
    assert a is b

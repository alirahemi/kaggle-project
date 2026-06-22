"""Unit tests for application settings."""

from pathlib import Path

from config.settings import ENV_FILE, Settings, get_settings, reload_settings


def test_settings_defaults():
    settings = Settings()
    assert settings.app_name == "german-bureaucracy-agent"
    assert settings.api_port == 8000
    assert settings.agent_default_locale == "en"
    assert settings.max_upload_size_mb == 20


def test_get_settings_cached():
    reload_settings()
    a = get_settings()
    b = get_settings()
    assert a is b


def test_env_file_path_is_project_root():
    assert ENV_FILE == Path(__file__).resolve().parents[2] / ".env"

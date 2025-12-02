"""Tests for configuration management."""

import pytest
from pathlib import Path
from tour_guide.config import Settings, get_settings
from tour_guide.config.settings import reset_settings


class TestSettings:
    def setup_method(self):
        reset_settings()

    def test_default_settings(self):
        settings = Settings()
        assert settings.logging.max_bytes == 10485760
        assert settings.routing.osrm_url == "http://router.project-osrm.org"
        assert settings.agents.content_timeout == 30
        assert settings.poi.count == 10

    def test_load_from_yaml(self, config_path):
        settings = Settings.from_yaml(config_path)
        assert settings.logging.level == "DEBUG"
        assert settings.logging.max_bytes == 1048576

    def test_missing_yaml_returns_defaults(self, tmp_path):
        settings = Settings.from_yaml(tmp_path / "nonexistent.yaml")
        assert settings.logging.max_bytes == 10485760

    def test_get_settings_singleton(self):
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def test_routes():
    """10 Israeli test routes."""
    return [
        ("Tel Aviv", "Jerusalem"),
        ("Haifa", "Akko"),
        ("Tel Aviv", "Eilat"),
        ("Jerusalem", "Dead Sea"),
        ("Nazareth", "Tiberias"),
        ("Tel Aviv", "Caesarea"),
        ("Beer Sheva", "Masada"),
        ("Haifa", "Rosh Hanikra"),
        ("Jerusalem", "Bethlehem"),
        ("Tel Aviv", "Jaffa"),
    ]


@pytest.fixture
def sample_poi():
    """Sample POI for testing."""
    return {
        "name": "Latrun",
        "lat": 31.838,
        "lon": 34.978,
        "description": "Historic site of the 1948 Arab-Israeli War",
        "category": "historical",
    }


@pytest.fixture
def config_path(tmp_path):
    """Temporary config file."""
    config = tmp_path / "settings.yaml"
    config.write_text(
        """
logging:
  max_bytes: 1048576
  backup_count: 3
  level: DEBUG
"""
    )
    return config

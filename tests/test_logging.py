"""Tests for logging system."""

import pytest
import logging
import json
from pathlib import Path
from tour_guide.logging import setup_logging, get_logger
from tour_guide.logging.setup import reset_logging, JSONFormatter


class TestLogging:
    def setup_method(self):
        reset_logging()

    def test_get_logger(self, tmp_path):
        logger = get_logger("test")
        assert logger.name == "tour_guide.test"

    def test_json_formatter(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert data["message"] == "Test message"
        assert data["level"] == "INFO"
        assert "timestamp" in data

    def test_log_rotation_setup(self, tmp_path):
        setup_logging(log_dir=tmp_path, console=False)
        logger = get_logger("rotation_test")
        logger.info("Test message")

        log_files = list(tmp_path.glob("*.log"))
        assert len(log_files) == 1

    def test_custom_fields(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.agent = "youtube"
        record.poi = "Latrun"

        output = formatter.format(record)
        data = json.loads(output)
        assert data["agent"] == "youtube"
        assert data["poi"] == "Latrun"

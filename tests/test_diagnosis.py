"""Tests for diagnosis system."""

import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from tour_guide.diagnosis.parser import LogParser, LogEntry


class TestLogParser:
    """Tests for LogParser class."""

    @pytest.fixture
    def parser(self):
        """Create LogParser instance."""
        return LogParser()

    @pytest.fixture
    def sample_log_entries(self):
        """Create sample log entries as JSON strings."""
        return [
            {
                "timestamp": "2025-12-02T10:00:00",
                "level": "INFO",
                "logger": "tour_guide.agents.youtube",
                "message": "Searching YouTube for content",
                "module": "youtube",
                "function": "search",
                "line": 42,
            },
            {
                "timestamp": "2025-12-02T10:00:01",
                "level": "ERROR",
                "logger": "tour_guide.agents.youtube",
                "message": "TimeoutError: Request timed out",
                "module": "youtube",
                "function": "search",
                "line": 45,
                "exception": "TimeoutError: Request timed out",
            },
            {
                "timestamp": "2025-12-02T10:00:02",
                "level": "INFO",
                "logger": "tour_guide.agents.spotify",
                "message": "Found 5 tracks",
                "module": "spotify",
                "function": "search",
                "line": 38,
                "execution_time": 1.5,
            },
            {
                "timestamp": "2025-12-02T10:00:03",
                "level": "WARNING",
                "logger": "tour_guide.agents.history",
                "message": "Slow response from Claude",
                "module": "history",
                "function": "generate",
                "line": 67,
            },
            {
                "timestamp": "2025-12-02T10:00:04",
                "level": "ERROR",
                "logger": "tour_guide.agents.youtube",
                "message": "Failed to connect",
                "module": "youtube",
                "function": "search",
                "line": 48,
            },
        ]

    @pytest.fixture
    def temp_log_file(self, sample_log_entries):
        """Create temporary log file with sample entries."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False
        ) as f:
            for entry in sample_log_entries:
                f.write(json.dumps(entry) + "\n")
            return Path(f.name)

    def test_parse_file_valid(self, parser, temp_log_file):
        """Test parsing a valid log file."""
        entries = parser.parse_file(temp_log_file)

        assert len(entries) == 5
        assert all(isinstance(e, LogEntry) for e in entries)

        # Check first entry
        assert entries[0].level == "INFO"
        assert entries[0].agent == "youtube"
        assert entries[0].logger == "tour_guide.agents.youtube"

        # Check second entry (error with exception)
        assert entries[1].level == "ERROR"
        assert entries[1].exception == "TimeoutError: Request timed out"

        # Check third entry (with execution time)
        assert entries[2].execution_time == 1.5
        assert entries[2].agent == "spotify"

        # Clean up
        temp_log_file.unlink()

    def test_parse_file_nonexistent(self, parser):
        """Test parsing a nonexistent file."""
        entries = parser.parse_file(Path("/nonexistent/file.log"))
        assert entries == []

    def test_parse_file_malformed_lines(self, parser):
        """Test parsing file with malformed lines."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False
        ) as f:
            # Valid entry
            f.write(
                json.dumps(
                    {
                        "timestamp": "2025-12-02T10:00:00",
                        "level": "INFO",
                        "logger": "test",
                        "message": "test",
                        "module": "test",
                        "function": "test",
                        "line": 1,
                    }
                )
                + "\n"
            )
            # Malformed JSON
            f.write("not json at all\n")
            # Another valid entry
            f.write(
                json.dumps(
                    {
                        "timestamp": "2025-12-02T10:00:01",
                        "level": "ERROR",
                        "logger": "test",
                        "message": "error",
                        "module": "test",
                        "function": "test",
                        "line": 2,
                    }
                )
                + "\n"
            )
            log_path = Path(f.name)

        entries = parser.parse_file(log_path)

        # Should parse 2 valid entries, skip malformed
        assert len(entries) == 2
        assert entries[0].level == "INFO"
        assert entries[1].level == "ERROR"

        # Clean up
        log_path.unlink()

    def test_filter_by_agent(self, parser, temp_log_file):
        """Test filtering entries by agent."""
        entries = parser.parse_file(temp_log_file)

        youtube_entries = parser.filter_by_agent(entries, "youtube")
        assert len(youtube_entries) == 3  # 2 errors + 1 info
        assert all(e.agent == "youtube" for e in youtube_entries)

        spotify_entries = parser.filter_by_agent(entries, "spotify")
        assert len(spotify_entries) == 1
        assert spotify_entries[0].agent == "spotify"

        history_entries = parser.filter_by_agent(entries, "history")
        assert len(history_entries) == 1

        # Clean up
        temp_log_file.unlink()

    def test_filter_by_level(self, parser, temp_log_file):
        """Test filtering entries by log level."""
        entries = parser.parse_file(temp_log_file)

        error_entries = parser.filter_by_level(entries, "ERROR")
        assert len(error_entries) == 2
        assert all(e.level == "ERROR" for e in error_entries)

        info_entries = parser.filter_by_level(entries, "INFO")
        assert len(info_entries) == 2

        warning_entries = parser.filter_by_level(entries, "WARNING")
        assert len(warning_entries) == 1

        # Clean up
        temp_log_file.unlink()

    def test_get_errors(self, parser, temp_log_file):
        """Test getting all errors."""
        entries = parser.parse_file(temp_log_file)
        errors = parser.get_errors(entries)

        assert len(errors) == 2
        assert all(e.level == "ERROR" for e in errors)

        # Clean up
        temp_log_file.unlink()

    def test_parse_recent(self, parser, sample_log_entries):
        """Test parsing recent entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)

            # Create log file with entries from 1 hour ago
            old_entries = [
                {
                    **sample_log_entries[0],
                    "timestamp": (
                        datetime.now() - timedelta(hours=2)
                    ).isoformat(),
                }
            ]
            with open(log_dir / "tour_guide_old.log", "w") as f:
                for entry in old_entries:
                    f.write(json.dumps(entry) + "\n")

            # Create log file with recent entries
            recent_entries = [
                {**sample_log_entries[1], "timestamp": datetime.now().isoformat()}
            ]
            with open(log_dir / "tour_guide_recent.log", "w") as f:
                for entry in recent_entries:
                    f.write(json.dumps(entry) + "\n")

            # Parse last 1 hour
            entries = parser.parse_recent(log_dir, hours=1)

            # Should only get recent entry
            assert len(entries) == 1
            assert entries[0].level == "ERROR"

    def test_parse_empty_directory(self, parser):
        """Test parsing empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entries = parser.parse_recent(Path(tmpdir), hours=24)
            assert entries == []

    def test_timestamp_parsing(self, parser):
        """Test various timestamp formats."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False
        ) as f:
            # ISO format with Z
            f.write(
                json.dumps(
                    {
                        "timestamp": "2025-12-02T10:00:00Z",
                        "level": "INFO",
                        "logger": "test",
                        "message": "test",
                        "module": "test",
                        "function": "test",
                        "line": 1,
                    }
                )
                + "\n"
            )
            # ISO format without Z
            f.write(
                json.dumps(
                    {
                        "timestamp": "2025-12-02T10:00:01",
                        "level": "INFO",
                        "logger": "test",
                        "message": "test",
                        "module": "test",
                        "function": "test",
                        "line": 2,
                    }
                )
                + "\n"
            )
            log_path = Path(f.name)

        entries = parser.parse_file(log_path)
        assert len(entries) == 2
        assert all(isinstance(e.timestamp, datetime) for e in entries)

        # Clean up
        log_path.unlink()

    def test_agent_extraction_from_message(self, parser):
        """Test extracting agent from message when not in logger."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False
        ) as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": "2025-12-02T10:00:00",
                        "level": "INFO",
                        "logger": "tour_guide.routing",
                        "message": "YouTube agent returned results",
                        "module": "routing",
                        "function": "process",
                        "line": 1,
                    }
                )
                + "\n"
            )
            log_path = Path(f.name)

        entries = parser.parse_file(log_path)
        assert len(entries) == 1
        assert entries[0].agent == "youtube"

        # Clean up
        log_path.unlink()

from tour_guide.diagnosis.analyzer import DiagnosticAnalyzer, DiagnosticReport, Pattern, AgentStats


class TestDiagnosticAnalyzer:
    """Tests for DiagnosticAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create DiagnosticAnalyzer instance."""
        return DiagnosticAnalyzer()

    @pytest.fixture
    def sample_entries_with_patterns(self):
        """Create sample log entries with detectable patterns."""
        entries = []

        # Create frequent error pattern (same error 4 times)
        for i in range(4):
            entries.append(
                LogEntry(
                    timestamp=datetime.now() - timedelta(minutes=i),
                    level="ERROR",
                    logger="tour_guide.agents.youtube",
                    message="Connection refused",
                    module="youtube",
                    function="search",
                    line=42,
                    agent="youtube",
                )
            )

        # Create timeout pattern (3 timeout errors)
        for i in range(3):
            entries.append(
                LogEntry(
                    timestamp=datetime.now() - timedelta(minutes=i + 5),
                    level="ERROR",
                    logger="tour_guide.agents.spotify",
                    message="Request timed out after 30s",
                    module="spotify",
                    function="search",
                    line=38,
                    agent="spotify",
                )
            )

        # Create slow operations (2 slow calls)
        for i in range(2):
            entries.append(
                LogEntry(
                    timestamp=datetime.now() - timedelta(minutes=i + 10),
                    level="INFO",
                    logger="tour_guide.agents.history",
                    message="Generated narrative",
                    module="history",
                    function="generate",
                    line=67,
                    agent="history",
                    execution_time=8.5,
                )
            )

        # Add some successful operations
        for i in range(5):
            entries.append(
                LogEntry(
                    timestamp=datetime.now() - timedelta(minutes=i + 15),
                    level="INFO",
                    logger="tour_guide.agents.history",
                    message="Success",
                    module="history",
                    function="run",
                    line=50,
                    agent="history",
                    execution_time=2.0,
                )
            )

        return entries

    def test_analyzer_initialization(self, analyzer):
        """Test that analyzer initializes correctly."""
        assert analyzer is not None

    def test_analyze_basic(self, analyzer, sample_entries_with_patterns):
        """Test basic analysis functionality."""
        report = analyzer.analyze(sample_entries_with_patterns)

        assert isinstance(report, DiagnosticReport)
        assert report.total_entries == len(sample_entries_with_patterns)
        assert report.error_count == 7  # 4 youtube + 3 spotify errors
        assert report.warning_count == 0
        assert len(report.patterns) > 0
        assert len(report.recommendations) > 0

    def test_detect_frequent_errors(self, analyzer, sample_entries_with_patterns):
        """Test detection of frequent errors."""
        report = analyzer.analyze(sample_entries_with_patterns)

        # Should detect the 4 "Connection refused" errors
        frequent_errors = [
            p for p in report.patterns if p.pattern_type == "frequent_error"
        ]
        assert len(frequent_errors) >= 1
        assert any(p.count >= 3 for p in frequent_errors)

    def test_detect_timeouts(self, analyzer, sample_entries_with_patterns):
        """Test detection of timeout patterns."""
        report = analyzer.analyze(sample_entries_with_patterns)

        # Should detect the 3 timeout errors
        timeout_patterns = [
            p for p in report.patterns if p.pattern_type == "timeout"
        ]
        assert len(timeout_patterns) >= 1
        assert any(p.agent == "spotify" for p in timeout_patterns)

    def test_detect_slow_operations(self, analyzer, sample_entries_with_patterns):
        """Test detection of slow operations."""
        report = analyzer.analyze(sample_entries_with_patterns)

        # Should detect slow operations in history agent
        slow_patterns = [
            p for p in report.patterns if p.pattern_type == "slow_operation"
        ]
        assert len(slow_patterns) >= 1
        assert any(p.agent == "history" for p in slow_patterns)

    def test_calculate_agent_stats(self, analyzer, sample_entries_with_patterns):
        """Test agent statistics calculation."""
        report = analyzer.analyze(sample_entries_with_patterns)

        assert len(report.agent_stats) == 3  # youtube, spotify, history

        # Check youtube stats
        youtube_stats = report.agent_stats.get("youtube")
        assert youtube_stats is not None
        assert youtube_stats.total_calls == 4
        assert youtube_stats.failure_count == 4
        assert youtube_stats.error_rate == 1.0  # 100% error rate

        # Check spotify stats
        spotify_stats = report.agent_stats.get("spotify")
        assert spotify_stats is not None
        assert spotify_stats.total_calls == 3
        assert spotify_stats.failure_count == 3

        # Check history stats
        history_stats = report.agent_stats.get("history")
        assert history_stats is not None
        assert history_stats.total_calls == 7  # 2 slow + 5 fast
        assert history_stats.failure_count == 0
        assert history_stats.avg_execution_time > 0

    def test_generate_recommendations(self, analyzer, sample_entries_with_patterns):
        """Test recommendation generation."""
        report = analyzer.analyze(sample_entries_with_patterns)

        assert len(report.recommendations) > 0

        # Should have recommendations about timeouts and errors
        recommendations_text = " ".join(report.recommendations).lower()
        assert "youtube" in recommendations_text or "spotify" in recommendations_text

    def test_analyze_agent_specific(self, analyzer, sample_entries_with_patterns):
        """Test analyzing specific agent."""
        youtube_stats = analyzer.analyze_agent("youtube", sample_entries_with_patterns)

        assert youtube_stats is not None
        assert youtube_stats.agent_name == "youtube"
        assert youtube_stats.total_calls == 4
        assert youtube_stats.failure_count == 4

    def test_analyze_agent_not_found(self, analyzer, sample_entries_with_patterns):
        """Test analyzing non-existent agent."""
        stats = analyzer.analyze_agent("nonexistent", sample_entries_with_patterns)
        assert stats is None

    def test_empty_entries(self, analyzer):
        """Test analyzing empty entry list."""
        report = analyzer.analyze([])

        assert report.total_entries == 0
        assert report.error_count == 0
        assert report.warning_count == 0
        assert len(report.patterns) == 0

    def test_high_error_rate_detection(self, analyzer):
        """Test detection of high error rate."""
        # Create entries with high error rate for one agent
        entries = []
        for i in range(10):
            level = "ERROR" if i < 4 else "INFO"  # 40% error rate
            entries.append(
                LogEntry(
                    timestamp=datetime.now() - timedelta(minutes=i),
                    level=level,
                    logger="tour_guide.agents.youtube",
                    message=f"Message {i}",
                    module="youtube",
                    function="run",
                    line=42,
                    agent="youtube",
                )
            )

        report = analyzer.analyze(entries)

        # Should detect high error rate
        high_error_patterns = [
            p for p in report.patterns if p.pattern_type == "high_error_rate"
        ]
        assert len(high_error_patterns) >= 1
        assert high_error_patterns[0].agent == "youtube"

"""Tests for agent classes."""

import pytest
from unittest.mock import Mock, patch, mock_open
from tour_guide.agents.base import BaseAgent, AgentError


class TestBaseAgent:
    """Tests for BaseAgent class."""

    @pytest.fixture
    def test_agent(self):
        """Create a concrete test agent."""

        class TestAgent(BaseAgent):
            def run(self, input_data):
                return f"Processed: {input_data}"

        return TestAgent("test_agent")

    def test_agent_initialization(self, test_agent):
        """Test that agent initializes with logger."""
        assert test_agent.agent_name == "test_agent"
        assert test_agent.logger is not None
        assert test_agent.settings is not None

    def test_run_with_timeout_success(self, test_agent):
        """Test successful execution with timeout."""
        result = test_agent.run_with_timeout("test_input", timeout_seconds=5)
        assert result == "Processed: test_input"

    def test_run_with_timeout_logs_execution_time(self, test_agent):
        """Test that execution time is logged."""
        with patch.object(test_agent.logger, "info") as mock_info:
            test_agent.run_with_timeout("test_input", timeout_seconds=5)

            # Check that completion was logged with time
            calls = [str(call) for call in mock_info.call_args_list]
            assert any("completed successfully" in str(call) for call in calls)

    def test_run_with_timeout_handles_errors(self, test_agent):
        """Test that errors are logged and re-raised."""

        class FailingAgent(BaseAgent):
            def run(self, input_data):
                raise ValueError("Test error")

        failing_agent = FailingAgent("failing_agent")

        with pytest.raises(ValueError):
            failing_agent.run_with_timeout("test_input")

    def test_read_recent_logs_no_file(self, test_agent):
        """Test reading logs when log file doesn't exist."""
        # Temporarily remove all handlers to simulate no log file
        import logging

        root_logger = logging.getLogger("tour_guide")
        original_handlers = root_logger.handlers.copy()
        root_logger.handlers.clear()

        try:
            result = test_agent._read_recent_logs(lines=10)
            assert "No log file found" in result
        finally:
            # Restore handlers
            for handler in original_handlers:
                root_logger.addHandler(handler)

    def test_read_recent_logs_success(self, test_agent):
        """Test reading logs successfully."""
        mock_log_content = """
{"level": "INFO", "message": "agents.test_agent: Starting"}
{"level": "INFO", "message": "agents.test_agent: Processing"}
{"level": "INFO", "message": "agents.other_agent: Other log"}
{"level": "INFO", "message": "agents.test_agent: Completed"}
"""
        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data=mock_log_content)
        ):
            result = test_agent._read_recent_logs(lines=10)

            # Should contain test_agent logs
            assert "agents.test_agent: Starting" in result
            assert "agents.test_agent: Completed" in result
            # Should NOT contain other agent's logs
            assert "agents.other_agent" not in result

    def test_diagnose_success(self, test_agent):
        """Test diagnose method with successful Claude response."""
        mock_log_content = """
{"level": "ERROR", "message": "agents.test_agent: Connection failed"}
"""
        mock_claude_response = """
1. Summary: Agent attempted connection but failed
2. Errors: Connection timeout error
3. Root cause: Network connectivity issue
4. Fix: Check network settings and retry
"""

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data=mock_log_content)
        ), patch("tour_guide.agents.base.call_claude") as mock_claude:
            mock_claude.return_value = mock_claude_response

            result = test_agent.diagnose()

            assert "Connection timeout error" in result
            assert "Fix:" in result
            mock_claude.assert_called_once()

    def test_diagnose_claude_error(self, test_agent):
        """Test diagnose handles Claude errors."""
        from tour_guide.utils.claude_cli import ClaudeError

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data="some logs")
        ), patch("tour_guide.agents.base.call_claude") as mock_claude:
            mock_claude.side_effect = ClaudeError("CLI failed")

            with pytest.raises(AgentError) as exc_info:
                test_agent.diagnose()

            assert "Failed to get diagnostic analysis" in str(exc_info.value)

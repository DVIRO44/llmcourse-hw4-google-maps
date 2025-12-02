"""Base agent class for all agents in the system."""

from abc import ABC, abstractmethod
from typing import Any
import time
from pathlib import Path
from tour_guide.logging import get_logger
from tour_guide.utils.claude_cli import call_claude, ClaudeError
from tour_guide.config import get_settings


class AgentError(Exception):
    """Base exception for agent errors."""

    pass


class AgentTimeoutError(AgentError):
    """Agent execution timed out."""

    pass


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, agent_name: str):
        """
        Initialize base agent.

        Args:
            agent_name: Name of the agent (used for logging)
        """
        self.agent_name = agent_name
        self.logger = get_logger(f"agents.{agent_name}")
        self.settings = get_settings()

    @abstractmethod
    def run(self, input_data: Any) -> Any:
        """
        Execute the agent's main task.

        Args:
            input_data: Input data for the agent

        Returns:
            Result of agent execution

        Raises:
            AgentError: If agent execution fails
        """
        pass

    def run_with_timeout(self, input_data: Any, timeout_seconds: int = None) -> Any:
        """
        Execute agent with timeout and execution time logging.

        Args:
            input_data: Input data for the agent
            timeout_seconds: Optional timeout in seconds (uses config default if not provided)

        Returns:
            Result of agent execution

        Raises:
            AgentTimeoutError: If execution exceeds timeout
            AgentError: If agent execution fails
        """
        if timeout_seconds is None:
            timeout_seconds = 60  # Default timeout

        self.logger.info(f"Starting {self.agent_name} with timeout={timeout_seconds}s")
        start_time = time.time()

        try:
            result = self.run(input_data)
            execution_time = time.time() - start_time

            self.logger.info(
                f"{self.agent_name} completed successfully in {execution_time:.2f}s"
            )
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(
                f"{self.agent_name} failed after {execution_time:.2f}s: {e}"
            )
            raise

    def diagnose(self) -> str:
        """
        Read recent logs and use Claude to analyze any issues.

        Returns:
            Diagnostic analysis from Claude

        Raises:
            AgentError: If diagnosis fails
        """
        self.logger.info(f"Running diagnostics for {self.agent_name}")

        try:
            # Read recent logs
            recent_logs = self._read_recent_logs(lines=50)

            # Ask Claude to analyze
            prompt = f"""Analyze the following logs from the {self.agent_name} agent and identify any issues or problems.

Logs:
{recent_logs}

Provide:
1. Summary of what the agent was doing
2. Any errors or warnings found
3. Root cause analysis if errors present
4. Recommended fixes

Be concise and actionable."""

            analysis = call_claude(prompt, timeout=30)

            self.logger.info(f"Diagnostics completed for {self.agent_name}")
            return analysis

        except ClaudeError as e:
            error_msg = f"Failed to get diagnostic analysis from Claude: {e}"
            self.logger.error(error_msg)
            raise AgentError(error_msg)

        except Exception as e:
            error_msg = f"Diagnostic analysis failed: {e}"
            self.logger.error(error_msg)
            raise AgentError(error_msg)

    def _read_recent_logs(self, lines: int = 50) -> str:
        """
        Read recent log entries for this agent.

        Args:
            lines: Number of recent lines to read

        Returns:
            Recent log content as string
        """
        try:
            # Get log file from root logger's file handler
            import logging
            from logging.handlers import RotatingFileHandler

            root_logger = logging.getLogger("tour_guide")
            log_file = None

            for handler in root_logger.handlers:
                if isinstance(handler, RotatingFileHandler):
                    log_file = Path(handler.baseFilename)
                    break

            if log_file is None or not log_file.exists():
                return f"No log file found"

            # Read last N lines from log file
            with open(log_file, "r") as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:]

                # Filter for this agent's logs
                agent_logs = [
                    line
                    for line in recent_lines
                    if f"agents.{self.agent_name}" in line
                ]

                if not agent_logs:
                    return f"No recent logs found for {self.agent_name}"

                return "".join(agent_logs)

        except Exception as e:
            self.logger.warning(f"Failed to read logs: {e}")
            return f"Failed to read logs: {e}"

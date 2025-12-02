"""Base agent class for all agents in the system."""

from abc import ABC, abstractmethod
from typing import Any
import time
from pathlib import Path
from tour_guide.logging import get_logger
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

    def diagnose(self, last_lines: int = 50) -> str:
        """
        Analyze recent logs for this agent and identify issues.

        Uses the diagnostic analyzer to detect patterns, calculate statistics,
        and provide actionable recommendations.

        Args:
            last_lines: Number of recent log lines to analyze

        Returns:
            Human-readable diagnostic report

        Raises:
            AgentError: If diagnosis fails
        """
        self.logger.info(f"Running diagnostics for {self.agent_name}")

        try:
            from tour_guide.diagnosis import LogParser, DiagnosticAnalyzer

            # Get log directory
            import logging
            from logging.handlers import RotatingFileHandler

            root_logger = logging.getLogger("tour_guide")
            log_dir = None

            for handler in root_logger.handlers:
                if isinstance(handler, RotatingFileHandler):
                    log_file = Path(handler.baseFilename)
                    log_dir = log_file.parent
                    break

            if log_dir is None:
                return "No log directory found. Unable to run diagnostics."

            # Parse recent logs
            parser = LogParser()
            all_entries = parser.parse_recent(log_dir, hours=24)

            # Filter to this agent's logs
            agent_entries = parser.filter_by_agent(all_entries, self.agent_name)

            # Limit to last N entries
            agent_entries = agent_entries[-last_lines:] if len(agent_entries) > last_lines else agent_entries

            if not agent_entries:
                return f"No recent log entries found for {self.agent_name} agent."

            # Analyze logs
            analyzer = DiagnosticAnalyzer()
            report = analyzer.analyze(agent_entries)

            # Format report as human-readable text
            diagnosis = self._format_diagnostic_report(report)

            self.logger.info(f"Diagnostics completed for {self.agent_name}")
            return diagnosis

        except Exception as e:
            error_msg = f"Diagnostic analysis failed: {e}"
            self.logger.error(error_msg)
            raise AgentError(error_msg)

    def _format_diagnostic_report(self, report) -> str:
        """
        Format diagnostic report as human-readable text.

        Args:
            report: DiagnosticReport object

        Returns:
            Formatted report string
        """
        lines = []
        lines.append(f"\n🔍 Diagnostic Report for {self.agent_name.upper()} Agent")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        lines.append("📊 Summary:")
        lines.append(f"   Total log entries: {report.total_entries}")
        lines.append(f"   Errors: {report.error_count}")
        lines.append(f"   Warnings: {report.warning_count}")
        lines.append("")

        # Agent statistics
        if self.agent_name.lower() in report.agent_stats:
            stats = report.agent_stats[self.agent_name.lower()]
            lines.append("📈 Statistics:")
            lines.append(f"   Total calls: {stats.total_calls}")
            lines.append(f"   Successful: {stats.success_count}")
            lines.append(f"   Failed: {stats.failure_count}")
            lines.append(f"   Error rate: {stats.error_rate:.1%}")
            if stats.avg_execution_time > 0:
                lines.append(f"   Avg execution time: {stats.avg_execution_time:.2f}s")
            lines.append("")

        # Patterns detected
        if report.patterns:
            lines.append("⚠️  Patterns Detected:")
            for pattern in report.patterns:
                severity_emoji = "🔴" if pattern.severity == "high" else "🟡"
                lines.append(f"   {severity_emoji} {pattern.description}")
            lines.append("")

        # Recommendations
        if report.recommendations:
            lines.append("💡 Recommendations:")
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"   {i}. {rec}")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

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
                return "No log file found"

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

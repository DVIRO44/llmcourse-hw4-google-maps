"""Log parser for analyzing Tour Guide logs."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """Represents a single log entry."""

    timestamp: datetime
    level: str
    logger: str
    message: str
    module: str
    function: str
    line: int
    agent: Optional[str] = None
    poi: Optional[str] = None
    execution_time: Optional[float] = None
    exception: Optional[str] = None


class LogParser:
    """
    Parser for JSON log files.

    Reads and parses JSON-formatted log files (one JSON object per line),
    with filtering capabilities by agent, level, and time range.
    """

    def parse_file(self, log_path: Path) -> List[LogEntry]:
        """
        Parse a single log file.

        Args:
            log_path: Path to the log file

        Returns:
            List of LogEntry objects, sorted by timestamp
        """
        entries = []

        if not log_path.exists():
            logger.warning(f"Log file not found: {log_path}")
            return entries

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        entry = self._parse_line(line)
                        if entry:
                            entries.append(entry)
                    except Exception as e:
                        logger.debug(
                            f"Failed to parse line {line_num} in {log_path}: {e}"
                        )
                        continue

        except Exception as e:
            logger.error(f"Failed to read log file {log_path}: {e}")
            return []

        # Sort by timestamp
        entries.sort(key=lambda x: x.timestamp)
        return entries

    def parse_recent(self, log_dir: Path, hours: int = 24) -> List[LogEntry]:
        """
        Parse recent log files from a directory.

        Args:
            log_dir: Directory containing log files
            hours: Number of hours to look back (default 24)

        Returns:
            List of LogEntry objects from the last N hours, sorted by timestamp
        """
        if not log_dir.exists() or not log_dir.is_dir():
            logger.warning(f"Log directory not found: {log_dir}")
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        all_entries = []

        # Find all log files matching pattern
        log_files = sorted(log_dir.glob("tour_guide_*.log"))

        for log_file in log_files:
            entries = self.parse_file(log_file)
            # Filter by time
            recent_entries = [e for e in entries if e.timestamp >= cutoff_time]
            all_entries.extend(recent_entries)

        # Sort all entries by timestamp
        all_entries.sort(key=lambda x: x.timestamp)
        return all_entries

    def filter_by_agent(
        self, entries: List[LogEntry], agent: str
    ) -> List[LogEntry]:
        """
        Filter entries by agent name.

        Args:
            entries: List of log entries
            agent: Agent name to filter by (e.g., "youtube", "spotify")

        Returns:
            Filtered list of entries
        """
        # Filter by agent field if present, or by logger name
        return [
            e
            for e in entries
            if (e.agent and agent.lower() in e.agent.lower())
            or (agent.lower() in e.logger.lower())
        ]

    def filter_by_level(
        self, entries: List[LogEntry], level: str
    ) -> List[LogEntry]:
        """
        Filter entries by log level.

        Args:
            entries: List of log entries
            level: Log level to filter by (e.g., "ERROR", "WARNING")

        Returns:
            Filtered list of entries
        """
        level_upper = level.upper()
        return [e for e in entries if e.level == level_upper]

    def get_errors(self, entries: List[LogEntry]) -> List[LogEntry]:
        """
        Get all error-level entries.

        Args:
            entries: List of log entries

        Returns:
            List of error entries
        """
        return self.filter_by_level(entries, "ERROR")

    def _parse_line(self, line: str) -> Optional[LogEntry]:
        """
        Parse a single JSON log line.

        Args:
            line: JSON string

        Returns:
            LogEntry object or None if parsing fails
        """
        try:
            data = json.loads(line)

            # Parse timestamp
            timestamp_str = data.get("timestamp", "")
            try:
                # Handle both ISO format with and without 'Z'
                if timestamp_str.endswith("Z"):
                    timestamp = datetime.fromisoformat(timestamp_str[:-1])
                else:
                    timestamp = datetime.fromisoformat(timestamp_str)
            except (ValueError, AttributeError):
                # Fallback to current time if parsing fails
                timestamp = datetime.now()

            # Extract agent name from logger if present
            agent = None
            logger_name = data.get("logger", "")
            if "agents." in logger_name:
                # Extract agent name from logger like "tour_guide.agents.youtube"
                parts = logger_name.split(".")
                if len(parts) >= 3:
                    agent = parts[-1]

            # Try to extract from message if not in logger
            if not agent:
                message = data.get("message", "")
                if "youtube" in message.lower():
                    agent = "youtube"
                elif "spotify" in message.lower():
                    agent = "spotify"
                elif "history" in message.lower():
                    agent = "history"
                elif "judge" in message.lower():
                    agent = "judge"

            # Extract POI name from message if present
            poi = None
            message = data.get("message", "")
            if "POI:" in message:
                # Extract POI name
                try:
                    poi_start = message.index("POI:") + 4
                    poi_end = message.find(",", poi_start)
                    if poi_end == -1:
                        poi_end = message.find(")", poi_start)
                    if poi_end == -1:
                        poi_end = len(message)
                    poi = message[poi_start:poi_end].strip()
                except ValueError:
                    pass

            # Extract execution time if present
            execution_time = None
            if "execution_time" in data:
                try:
                    execution_time = float(data["execution_time"])
                except (ValueError, TypeError):
                    pass

            # Extract exception if present
            exception = data.get("exception") or data.get("exc_info")

            return LogEntry(
                timestamp=timestamp,
                level=data.get("level", "INFO"),
                logger=logger_name,
                message=message,
                module=data.get("module", ""),
                function=data.get("function", ""),
                line=int(data.get("line", 0)),
                agent=agent,
                poi=poi,
                execution_time=execution_time,
                exception=exception,
            )

        except json.JSONDecodeError:
            logger.debug(f"Failed to parse JSON line: {line[:100]}")
            return None
        except Exception as e:
            logger.debug(f"Failed to create LogEntry: {e}")
            return None

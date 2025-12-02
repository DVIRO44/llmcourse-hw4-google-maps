"""Diagnostic analyzer for log analysis."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from collections import Counter, defaultdict

from tour_guide.diagnosis.parser import LogEntry

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """Represents a detected pattern in logs."""

    pattern_type: str  # "frequent_error", "slow_operation", "timeout", etc.
    description: str
    count: int
    agent: Optional[str] = None
    severity: str = "medium"  # low, medium, high
    examples: List[str] = field(default_factory=list)


@dataclass
class AgentStats:
    """Statistics for a single agent."""

    agent_name: str
    total_calls: int
    success_count: int
    failure_count: int
    avg_execution_time: float = 0.0
    error_rate: float = 0.0


@dataclass
class DiagnosticReport:
    """Complete diagnostic report."""

    generated_at: datetime
    total_entries: int
    error_count: int
    warning_count: int
    patterns: List[Pattern]
    agent_stats: Dict[str, AgentStats]
    recommendations: List[str]
    claude_analysis: str = ""


class DiagnosticAnalyzer:
    """
    Analyzes log entries to detect patterns and generate recommendations.

    Uses pattern detection algorithms to identify:
    - Frequent errors (same error >3 times)
    - Performance degradation (slow operations)
    - Agent reliability issues
    - Timeout patterns
    """

    def __init__(self):
        """Initialize diagnostic analyzer."""
        self.logger = logger

    def analyze(self, entries: List[LogEntry]) -> DiagnosticReport:
        """
        Analyze log entries and generate diagnostic report.

        Args:
            entries: List of log entries to analyze

        Returns:
            Complete diagnostic report with patterns and recommendations
        """
        self.logger.info(f"Analyzing {len(entries)} log entries")

        # Count by level
        level_counts = Counter(e.level for e in entries)

        # Detect patterns
        patterns = self._detect_patterns(entries)

        # Calculate agent statistics
        agent_stats = self._calculate_agent_stats(entries)

        # Generate recommendations
        recommendations = self._generate_recommendations(patterns, agent_stats)

        # Create report
        report = DiagnosticReport(
            generated_at=datetime.now(),
            total_entries=len(entries),
            error_count=level_counts.get("ERROR", 0),
            warning_count=level_counts.get("WARNING", 0),
            patterns=patterns,
            agent_stats=agent_stats,
            recommendations=recommendations,
        )

        self.logger.info(
            f"Analysis complete: {len(patterns)} patterns, "
            f"{report.error_count} errors, {report.warning_count} warnings"
        )

        return report

    def analyze_agent(
        self, agent: str, entries: List[LogEntry]
    ) -> Optional[AgentStats]:
        """
        Analyze specific agent's performance.

        Args:
            agent: Agent name to analyze
            entries: All log entries

        Returns:
            AgentStats for the specified agent, or None if not found
        """
        agent_entries = [
            e
            for e in entries
            if e.agent and e.agent.lower() == agent.lower()
        ]

        if not agent_entries:
            return None

        stats = self._calculate_agent_stats(agent_entries)
        return stats.get(agent.lower())

    def _detect_patterns(self, entries: List[LogEntry]) -> List[Pattern]:
        """
        Detect patterns in log entries.

        Args:
            entries: List of log entries

        Returns:
            List of detected patterns
        """
        patterns = []

        # 1. Detect frequent errors
        error_entries = [e for e in entries if e.level == "ERROR"]
        if error_entries:
            error_messages = Counter(e.message for e in error_entries)
            for msg, count in error_messages.most_common():
                if count >= 3:  # Threshold for "frequent"
                    # Find which agent(s) have this error
                    agents_with_error = set(
                        e.agent
                        for e in error_entries
                        if e.message == msg and e.agent
                    )
                    agent_str = (
                        ", ".join(agents_with_error)
                        if agents_with_error
                        else "unknown"
                    )

                    patterns.append(
                        Pattern(
                            pattern_type="frequent_error",
                            description=f"Error occurred {count} times: {msg[:100]}",
                            count=count,
                            agent=agent_str,
                            severity="high" if count >= 5 else "medium",
                            examples=[msg],
                        )
                    )

        # 2. Detect timeout patterns
        timeout_entries = [
            e
            for e in entries
            if "timeout" in e.message.lower() or "timed out" in e.message.lower()
        ]
        if len(timeout_entries) >= 2:
            agents_with_timeouts = Counter(
                e.agent for e in timeout_entries if e.agent
            )
            for agent, count in agents_with_timeouts.items():
                patterns.append(
                    Pattern(
                        pattern_type="timeout",
                        description=f"Timeout errors in {agent} agent ({count} times)",
                        count=count,
                        agent=agent,
                        severity="high" if count >= 3 else "medium",
                        examples=[
                            e.message
                            for e in timeout_entries
                            if e.agent == agent
                        ][:3],
                    )
                )

        # 3. Detect slow operations
        slow_entries = [e for e in entries if e.execution_time and e.execution_time > 5.0]
        if len(slow_entries) >= 2:
            agents_with_slow = Counter(e.agent for e in slow_entries if e.agent)
            for agent, count in agents_with_slow.items():
                avg_time = sum(
                    e.execution_time
                    for e in slow_entries
                    if e.agent == agent and e.execution_time
                ) / count
                patterns.append(
                    Pattern(
                        pattern_type="slow_operation",
                        description=f"Slow operations in {agent} agent (avg {avg_time:.1f}s)",
                        count=count,
                        agent=agent,
                        severity="medium",
                        examples=[],
                    )
                )

        # 4. Detect high error rate by agent
        agent_entries_by_name = defaultdict(list)
        for e in entries:
            if e.agent:
                agent_entries_by_name[e.agent].append(e)

        for agent, agent_entries in agent_entries_by_name.items():
            error_count = sum(1 for e in agent_entries if e.level == "ERROR")
            error_rate = error_count / len(agent_entries) if agent_entries else 0

            if error_rate >= 0.3 and error_count >= 3:  # 30% error rate threshold
                patterns.append(
                    Pattern(
                        pattern_type="high_error_rate",
                        description=f"{agent} agent has high error rate ({error_rate:.0%})",
                        count=error_count,
                        agent=agent,
                        severity="high",
                        examples=[],
                    )
                )

        return patterns

    def _calculate_agent_stats(
        self, entries: List[LogEntry]
    ) -> Dict[str, AgentStats]:
        """
        Calculate statistics for each agent.

        Args:
            entries: List of log entries

        Returns:
            Dictionary mapping agent names to their statistics
        """
        agent_stats = {}

        # Group entries by agent
        agent_entries = defaultdict(list)
        for e in entries:
            if e.agent:
                agent_entries[e.agent.lower()].append(e)

        # Calculate stats for each agent
        for agent, entries_list in agent_entries.items():
            total_calls = len(entries_list)
            error_count = sum(1 for e in entries_list if e.level == "ERROR")
            success_count = total_calls - error_count

            # Calculate average execution time
            exec_times = [
                e.execution_time for e in entries_list if e.execution_time
            ]
            avg_time = sum(exec_times) / len(exec_times) if exec_times else 0.0

            # Calculate error rate
            error_rate = error_count / total_calls if total_calls > 0 else 0.0

            agent_stats[agent] = AgentStats(
                agent_name=agent,
                total_calls=total_calls,
                success_count=success_count,
                failure_count=error_count,
                avg_execution_time=avg_time,
                error_rate=error_rate,
            )

        return agent_stats

    def _generate_recommendations(
        self, patterns: List[Pattern], agent_stats: Dict[str, AgentStats]
    ) -> List[str]:
        """
        Generate recommendations based on patterns and statistics.

        Args:
            patterns: Detected patterns
            agent_stats: Agent statistics

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Recommendations based on patterns
        for pattern in patterns:
            if pattern.pattern_type == "timeout" and pattern.count >= 3:
                recommendations.append(
                    f"Increase timeout for {pattern.agent} agent (experiencing {pattern.count} timeouts)"
                )

            elif pattern.pattern_type == "slow_operation":
                recommendations.append(
                    f"Optimize {pattern.agent} agent performance or increase timeout threshold"
                )

            elif pattern.pattern_type == "frequent_error":
                recommendations.append(
                    f"Investigate recurring error in {pattern.agent}: {pattern.examples[0][:80]}..."
                    if pattern.examples
                    else f"Investigate recurring error in {pattern.agent}"
                )

            elif pattern.pattern_type == "high_error_rate":
                recommendations.append(
                    f"Critical: {pattern.agent} agent failing at high rate, review implementation"
                )

        # Recommendations based on agent stats
        for agent, stats in agent_stats.items():
            if stats.error_rate >= 0.5:
                recommendations.append(
                    f"{agent} agent has 50%+ failure rate, needs immediate attention"
                )

            if stats.avg_execution_time > 10.0:
                recommendations.append(
                    f"{agent} agent averaging {stats.avg_execution_time:.1f}s per call, consider optimization"
                )

        # General recommendations if no specific issues
        if not recommendations:
            recommendations.append(
                "System operating normally, no critical issues detected"
            )

        return recommendations

    def _claude_analysis(self, report: DiagnosticReport) -> str:
        """
        Use Claude to analyze patterns and provide insights.

        This would integrate with Claude CLI in a real implementation.
        For now, returns a formatted summary.

        Args:
            report: Diagnostic report to analyze

        Returns:
            Claude's analysis as a string
        """
        # In a real implementation, this would call Claude CLI
        # For now, return a summary
        summary = f"""
Analyzed {report.total_entries} log entries.
Found {len(report.patterns)} patterns and {report.error_count} errors.

Key findings:
"""
        for pattern in report.patterns[:3]:  # Top 3 patterns
            summary += f"- {pattern.description}\n"

        summary += "\nRecommended actions:\n"
        for rec in report.recommendations[:3]:  # Top 3 recommendations
            summary += f"- {rec}\n"

        return summary.strip()

"""CLI entry point for Tour Guide."""

import click


@click.group()
@click.version_option()
def main():
    """Tour Guide - AI-powered tour guide system."""
    pass


@main.command()
@click.argument("origin")
@click.argument("destination")
@click.option("--json-output", type=click.Path(), help="Export to JSON")
@click.option("--markdown-output", type=click.Path(), help="Export to Markdown")
@click.option("--no-delay", is_flag=True, help="Skip journey delays")
def run(origin, destination, json_output, markdown_output, no_delay):
    """Run tour guide for a route."""
    click.echo(f"Planning route: {origin} → {destination}")
    click.echo("Not implemented yet")


@main.command()
def demo():
    """Run demo with Tel Aviv to Jerusalem."""
    click.echo("Demo mode - not implemented yet")


@main.command()
@click.option("--agent", type=str, help="Specific agent to diagnose")
@click.option("--last", type=int, default=100, help="Number of log lines to analyze")
@click.option("--hours", type=int, default=24, help="Hours of logs to analyze")
def diagnose(agent, last, hours):
    """Analyze logs and identify issues."""
    from pathlib import Path
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    from tour_guide.diagnosis import LogParser, DiagnosticAnalyzer
    from tour_guide.logging import get_log_dir

    console = Console()

    try:
        # Get log directory
        log_dir = get_log_dir()
        if not log_dir or not log_dir.exists():
            console.print("[red]❌ Error:[/red] No log directory found")
            return

        # Parse logs
        parser = LogParser()
        console.print(f"[cyan]🔍 Analyzing logs from last {hours} hours...[/cyan]")
        entries = parser.parse_recent(log_dir, hours=hours)

        if not entries:
            console.print("[yellow]⚠️  No log entries found[/yellow]")
            return

        # Filter by agent if specified
        if agent:
            entries = parser.filter_by_agent(entries, agent)
            if not entries:
                console.print(f"[yellow]⚠️  No log entries found for {agent} agent[/yellow]")
                return

        # Limit entries
        if len(entries) > last:
            entries = entries[-last:]

        # Analyze
        analyzer = DiagnosticAnalyzer()
        report = analyzer.analyze(entries)

        # Display report with Rich formatting
        console.print()

        # Title
        title = f"🔍 Diagnostic Report"
        if agent:
            title += f" - {agent.upper()} Agent"
        console.print(Panel(title, style="bold cyan", box=box.DOUBLE))
        console.print()

        # Summary
        console.print("[bold]📊 Summary[/bold]")
        summary_table = Table(show_header=False, box=None, padding=(0, 2))
        summary_table.add_row("Total entries:", f"[cyan]{report.total_entries}[/cyan]")
        summary_table.add_row("Errors:", f"[red]{report.error_count}[/red]" if report.error_count > 0 else f"[green]{report.error_count}[/green]")
        summary_table.add_row("Warnings:", f"[yellow]{report.warning_count}[/yellow]" if report.warning_count > 0 else f"[green]{report.warning_count}[/green]")
        console.print(summary_table)
        console.print()

        # Agent Statistics
        if report.agent_stats:
            console.print("[bold]🤖 Agent Statistics[/bold]")
            stats_table = Table(box=box.ROUNDED, border_style="cyan")
            stats_table.add_column("Agent", style="bold")
            stats_table.add_column("Success", justify="right")
            stats_table.add_column("Failures", justify="right")
            stats_table.add_column("Error Rate", justify="right")
            stats_table.add_column("Avg Time", justify="right")

            for agent_name, stats in sorted(report.agent_stats.items()):
                error_rate_str = f"{stats.error_rate:.0%}"
                error_rate_color = "red" if stats.error_rate >= 0.3 else "yellow" if stats.error_rate >= 0.1 else "green"

                avg_time_str = f"{stats.avg_execution_time:.2f}s" if stats.avg_execution_time > 0 else "-"

                stats_table.add_row(
                    agent_name,
                    f"[green]{stats.success_count}[/green]",
                    f"[red]{stats.failure_count}[/red]" if stats.failure_count > 0 else "0",
                    f"[{error_rate_color}]{error_rate_str}[/{error_rate_color}]",
                    avg_time_str
                )

            console.print(stats_table)
            console.print()

        # Patterns
        if report.patterns:
            console.print("[bold]⚠️  Patterns Detected[/bold]")
            for pattern in report.patterns:
                severity_emoji = "🔴" if pattern.severity == "high" else "🟡" if pattern.severity == "medium" else "🟢"
                console.print(f"   {severity_emoji} {pattern.description}")
            console.print()

        # Recommendations
        if report.recommendations:
            console.print("[bold]💡 Recommendations[/bold]")
            for i, rec in enumerate(report.recommendations, 1):
                console.print(f"   {i}. {rec}")
            console.print()

        console.print(Panel("✅ Diagnosis complete", style="green"))

    except Exception as e:
        console.print(f"[red]❌ Error during diagnosis:[/red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


if __name__ == "__main__":
    main()

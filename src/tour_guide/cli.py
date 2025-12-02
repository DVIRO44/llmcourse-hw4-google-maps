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
    import json
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    from tour_guide.orchestrator import TourGuideOrchestrator
    from tour_guide.logging import setup_logging

    console = Console()
    setup_logging()

    try:
        # Display journey start
        console.print()
        console.print(Panel(
            f"🗺️  Planning journey from [bold cyan]{origin}[/bold cyan] to [bold cyan]{destination}[/bold cyan]",
            style="bold blue",
            box=box.DOUBLE
        ))
        console.print()

        # Create orchestrator and run journey
        orchestrator = TourGuideOrchestrator()
        result = orchestrator.run(origin, destination)

        # Display route information
        console.print("[bold]📍 Route Information[/bold]")
        route_table = Table(show_header=False, box=None, padding=(0, 2))
        route_table.add_row("Distance:", f"[cyan]{result.route.total_distance_km:.1f} km[/cyan]")
        route_table.add_row("Duration:", f"[cyan]{result.route.total_duration_min:.1f} minutes[/cyan]")
        route_table.add_row("POIs found:", f"[cyan]{len(result.pois)}[/cyan]")
        console.print(route_table)
        console.print()

        # Display POIs and judgments
        if result.pois:
            console.print("[bold]📍 Points of Interest[/bold]")
            for i, poi in enumerate(result.pois, 1):
                console.print(f"  {i}. [bold]{poi.name}[/bold] ({poi.category.value})")
                console.print(f"     {poi.description}")
                console.print(f"     Distance from start: [cyan]{poi.distance_from_start_km:.1f} km[/cyan]")

                # Find matching judgment
                judgment = next((j for j in result.judgments if j.poi_name == poi.name), None)
                if judgment:
                    content_emoji = {"youtube": "🎥", "spotify": "🎵", "history": "📜"}
                    emoji = content_emoji.get(judgment.selected_type, "📄")
                    console.print(f"     {emoji} Selected: [green]{judgment.selected_type}[/green]")
                    console.print(f"     Reasoning: {judgment.reasoning}")

                console.print()
        else:
            console.print("[yellow]⚠️  No POIs found along this route[/yellow]")
            console.print()

        # Display statistics
        console.print("[bold]📊 Journey Statistics[/bold]")
        stats_table = Table(show_header=False, box=None, padding=(0, 2))
        stats_table.add_row("Total POIs:", f"[cyan]{result.stats['total_pois']}[/cyan]")
        stats_table.add_row("Judgments:", f"[cyan]{result.stats['total_judgments']}[/cyan]")
        stats_table.add_row("Success rate:", f"[cyan]{result.stats['success_rate']:.0%}[/cyan]")
        stats_table.add_row("Execution time:", f"[cyan]{result.execution_time:.2f}s[/cyan]")
        console.print(stats_table)
        console.print()

        # Content distribution
        if result.stats["content_distribution"]:
            console.print("[bold]📊 Content Distribution[/bold]")
            for content_type, count in result.stats["content_distribution"].items():
                console.print(f"  {content_type}: [cyan]{count}[/cyan]")
            console.print()

        # Export to JSON if requested
        if json_output:
            export_data = {
                "origin": origin,
                "destination": destination,
                "route": {
                    "distance_km": result.route.total_distance_km,
                    "duration_min": result.route.total_duration_min,
                },
                "pois": [
                    {
                        "name": poi.name,
                        "category": poi.category.value,
                        "description": poi.description,
                        "lat": poi.lat,
                        "lon": poi.lon,
                        "distance_from_start_km": poi.distance_from_start_km,
                    }
                    for poi in result.pois
                ],
                "judgments": [
                    {
                        "poi_name": j.poi_name,
                        "selected_type": j.selected_type,
                        "reasoning": j.reasoning,
                        "scores": j.scores,
                    }
                    for j in result.judgments
                ],
                "stats": result.stats,
                "execution_time": result.execution_time,
            }

            with open(json_output, "w") as f:
                json.dump(export_data, f, indent=2)
            console.print(f"[green]✅ Exported to {json_output}[/green]")
            console.print()

        # Export to Markdown if requested
        if markdown_output:
            lines = []
            lines.append(f"# Journey: {origin} → {destination}\n")
            lines.append(f"## Route Information\n")
            lines.append(f"- **Distance**: {result.route.total_distance_km:.1f} km")
            lines.append(f"- **Duration**: {result.route.total_duration_min:.1f} minutes")
            lines.append(f"- **POIs Found**: {len(result.pois)}\n")

            if result.pois:
                lines.append(f"## Points of Interest\n")
                for i, poi in enumerate(result.pois, 1):
                    lines.append(f"### {i}. {poi.name}")
                    lines.append(f"**Category**: {poi.category.value}")
                    lines.append(f"**Description**: {poi.description}")
                    lines.append(f"**Distance from start**: {poi.distance_from_start_km:.1f} km\n")

                    judgment = next((j for j in result.judgments if j.poi_name == poi.name), None)
                    if judgment:
                        lines.append(f"**Selected Content**: {judgment.selected_type}")
                        lines.append(f"**Reasoning**: {judgment.reasoning}\n")

            lines.append(f"## Statistics\n")
            lines.append(f"- **Total POIs**: {result.stats['total_pois']}")
            lines.append(f"- **Judgments**: {result.stats['total_judgments']}")
            lines.append(f"- **Success Rate**: {result.stats['success_rate']:.0%}")
            lines.append(f"- **Execution Time**: {result.execution_time:.2f}s\n")

            with open(markdown_output, "w") as f:
                f.write("\n".join(lines))
            console.print(f"[green]✅ Exported to {markdown_output}[/green]")
            console.print()

        console.print(Panel("✅ Journey complete!", style="green"))

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise click.Abort()


@main.command()
def demo():
    """Run demo with Tel Aviv to Jerusalem."""
    from rich.console import Console
    from rich.panel import Panel
    from rich import box
    from tour_guide.orchestrator import TourGuideOrchestrator
    from tour_guide.logging import setup_logging

    console = Console()
    setup_logging()

    try:
        console.print()
        console.print(Panel(
            "🎬 Demo Mode: Tel Aviv → Jerusalem",
            style="bold magenta",
            box=box.DOUBLE
        ))
        console.print()
        console.print("[dim]This is a demonstration of the Tour Guide system.[/dim]")
        console.print("[dim]Running a full journey from Tel Aviv to Jerusalem...[/dim]")
        console.print()

        # Create orchestrator and run journey
        orchestrator = TourGuideOrchestrator()
        result = orchestrator.run("Tel Aviv", "Jerusalem")

        # Display route information
        console.print("[bold]📍 Route Information[/bold]")
        console.print(f"  Distance: [cyan]{result.route.total_distance_km:.1f} km[/cyan]")
        console.print(f"  Duration: [cyan]{result.route.total_duration_min:.1f} minutes[/cyan]")
        console.print(f"  POIs found: [cyan]{len(result.pois)}[/cyan]")
        console.print()

        # Display POIs and judgments
        if result.pois:
            console.print("[bold]📍 Discovered Points of Interest[/bold]")
            for i, poi in enumerate(result.pois, 1):
                console.print(f"\n  {i}. [bold cyan]{poi.name}[/bold cyan]")
                console.print(f"     Category: {poi.category.value}")
                console.print(f"     {poi.description}")
                console.print(f"     Distance from start: {poi.distance_from_start_km:.1f} km")

                # Find matching judgment
                judgment = next((j for j in result.judgments if j.poi_name == poi.name), None)
                if judgment:
                    content_emoji = {"youtube": "🎥", "spotify": "🎵", "history": "📜"}
                    emoji = content_emoji.get(judgment.selected_type, "📄")
                    console.print(f"     {emoji} Recommended: [green]{judgment.selected_type}[/green]")
                    console.print(f"     Why: [dim]{judgment.reasoning}[/dim]")

            console.print()

        # Display statistics
        console.print("[bold]📊 Demo Statistics[/bold]")
        console.print(f"  Total POIs: [cyan]{result.stats['total_pois']}[/cyan]")
        console.print(f"  Judgments: [cyan]{result.stats['total_judgments']}[/cyan]")
        console.print(f"  Success rate: [cyan]{result.stats['success_rate']:.0%}[/cyan]")
        console.print(f"  Execution time: [cyan]{result.execution_time:.2f}s[/cyan]")
        console.print()

        # Content distribution
        if result.stats["content_distribution"]:
            console.print("[bold]📊 Content Types Selected[/bold]")
            for content_type, count in result.stats["content_distribution"].items():
                console.print(f"  {content_type}: [cyan]{count}[/cyan]")
            console.print()

        console.print(Panel("✅ Demo complete!", style="green"))
        console.print()
        console.print("[dim]Try running with custom routes:[/dim]")
        console.print("[dim]  tour-guide run 'Tel Aviv' 'Haifa'[/dim]")
        console.print("[dim]  tour-guide run 'Jerusalem' 'Eilat' --json-output journey.json[/dim]")
        console.print()

    except Exception as e:
        console.print(f"[red]❌ Demo failed:[/red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise click.Abort()


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

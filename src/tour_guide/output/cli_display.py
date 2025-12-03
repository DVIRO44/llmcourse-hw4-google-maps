"""Rich CLI display for Tour Guide output."""

import time
from typing import List, Dict
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from tour_guide.routing.models import Route
from tour_guide.models.poi import POI
from tour_guide.models.judgment import JudgmentResult


class CLIDisplay:
    """
    Beautiful terminal output using Rich library.

    Displays progress bars, POI information, journey simulation,
    and summary statistics with color coding and emojis.
    """

    # Emoji mapping for content types
    EMOJI_MAP = {
        "youtube": "🎬",
        "spotify": "🎵",
        "history": "📖",
        "selected": "⭐",
    }

    # Color mapping for content types
    COLOR_MAP = {
        "youtube": "red",
        "spotify": "green",
        "history": "blue",
    }

    def __init__(self):
        """Initialize CLI display with Rich console."""
        self.console = Console()

    def show_progress(self, stage: str, percent: int) -> None:
        """
        Show progress bar for a processing stage.

        Args:
            stage: Name of the current stage (e.g., "Routing", "Analyzing")
            percent: Progress percentage (0-100)
        """
        # Create a simple progress display
        bar_width = 40
        filled = int(bar_width * percent / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        self.console.print(f"[bold cyan]{stage}[/bold cyan] {bar} {percent}%")

    def show_route_info(self, route: Route) -> None:
        """
        Display route summary information.

        Args:
            route: Route object with origin, destination, distance, duration
        """
        # Get coordinates
        origin_coords = f"({route.origin[0]:.4f}, {route.origin[1]:.4f})"
        dest_coords = f"({route.destination[0]:.4f}, {route.destination[1]:.4f})"

        # Format duration
        hours = int(route.total_duration_min // 60)
        mins = int(route.total_duration_min % 60)
        duration_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"

        # Create route info panel
        route_text = Text()
        route_text.append(f"🚗 Tour: ", style="bold")
        route_text.append(f"{origin_coords} → {dest_coords}\n", style="bold cyan")
        route_text.append(f"📏 Distance: ", style="bold")
        route_text.append(f"{route.total_distance_km:.1f} km\n")
        route_text.append(f"⏱️  Duration: ", style="bold")
        route_text.append(f"~{duration_str}")

        panel = Panel(
            route_text,
            title="[bold]Route Overview[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )

        self.console.print(panel)
        self.console.print()

    def show_poi(self, poi: POI, judgment: JudgmentResult) -> None:
        """
        Display a single POI with its selected content and all options.

        Args:
            poi: POI object
            judgment: JudgmentResult with selected content and all options
        """
        # Create content display with all options
        content_text = Text()

        # Show all content options
        for content in judgment.all_content:
            emoji = self.EMOJI_MAP.get(content.content_type, "📄")
            color = self.COLOR_MAP.get(content.content_type, "white")

            content_text.append(f"{emoji} ", style=color)
            content_text.append(f"{content.content_type.title()}: ", style=f"bold {color}")
            content_text.append(f'"{content.title}"\n', style=color)

            # Add clickable URL if available
            if content.url:
                content_text.append("   🔗 ", style="dim")
                content_text.append(content.url, style=f"link {content.url} dim")
                content_text.append("\n")

        content_text.append("\n")

        # Show selected content
        selected_emoji = self.EMOJI_MAP.get(judgment.selected_type, "📄")
        selected_color = self.COLOR_MAP.get(judgment.selected_type, "white")

        content_text.append(f"{self.EMOJI_MAP['selected']} ", style="bold yellow")
        content_text.append("Selected: ", style="bold yellow")
        content_text.append(f"{selected_emoji} {judgment.selected_type.title()}", style=f"bold {selected_color}")
        content_text.append(f" (Score: {judgment.selected_content.relevance_score})\n", style="yellow")

        # Add clickable URL for selected content
        if judgment.selected_content.url:
            content_text.append("   🔗 ", style="yellow")
            content_text.append(judgment.selected_content.url, style=f"link {judgment.selected_content.url} yellow")
            content_text.append("\n")

        # Show reasoning (truncated if too long)
        reasoning = judgment.reasoning
        if len(reasoning) > 150:
            reasoning = reasoning[:147] + "..."
        content_text.append(f'"{reasoning}"', style="italic")

        # Create panel
        panel = Panel(
            content_text,
            title=f"[bold]📍 {poi.name}[/bold]",
            subtitle=f"[italic]{poi.category.value} | {poi.distance_from_start_km:.1f} km from start[/italic]",
            border_style=selected_color,
            box=box.ROUNDED,
        )

        self.console.print(panel)

    def show_journey(self, judgments: List[JudgmentResult], delay: int = 5) -> None:
        """
        Simulate a journey by showing POIs one by one with delays.

        Args:
            judgments: List of JudgmentResult objects
            delay: Delay in seconds between POIs (default 5, 0 to skip)
        """
        self.console.print("[bold cyan]🗺️  Starting Your Journey...[/bold cyan]\n")

        for i, judgment in enumerate(judgments, 1):
            # Show POI number
            self.console.print(f"\n[bold]Stop {i}/{len(judgments)}[/bold]")

            # Find corresponding POI (reconstruct from judgment data)
            poi = self._judgment_to_poi(judgment)

            # Display POI
            self.show_poi(poi, judgment)

            # Show delay message and wait (unless it's the last POI)
            if i < len(judgments) and delay > 0:
                self.console.print(f"\n[dim]⏳ Next stop in {delay} seconds...[/dim]")
                time.sleep(delay)

        self.console.print("\n[bold green]✅ Journey Complete![/bold green]\n")

    def show_summary(self, stats: Dict) -> None:
        """
        Display final statistics and summary.

        Args:
            stats: Dictionary with statistics (total_pois, content_distribution, execution_time, etc.)
        """
        # Create summary table
        table = Table(title="[bold]📊 Journey Summary[/bold]", box=box.ROUNDED, border_style="cyan")

        table.add_column("Metric", style="bold", no_wrap=True)
        table.add_column("Value", justify="right")

        # Add rows
        table.add_row("Total POIs", str(stats.get("total_pois", 0)))

        # Content distribution
        content_dist = stats.get("content_distribution", {})
        for content_type, count in content_dist.items():
            emoji = self.EMOJI_MAP.get(content_type, "📄")
            color = self.COLOR_MAP.get(content_type, "white")
            table.add_row(
                f"{emoji} {content_type.title()} Selected",
                f"[{color}]{count}[/{color}]",
            )

        # Execution time
        if "execution_time" in stats:
            exec_time = stats["execution_time"]
            table.add_row("Execution Time", f"{exec_time:.1f}s")

        # Average time per POI
        if "total_pois" in stats and "execution_time" in stats and stats["total_pois"] > 0:
            avg_time = stats["execution_time"] / stats["total_pois"]
            table.add_row("Avg Time per POI", f"{avg_time:.1f}s")

        self.console.print(table)
        self.console.print()

        # Success message
        self.console.print("[bold green]🎉 Tour guide generation complete![/bold green]")
        self.console.print("[dim]Journey data saved to output files.[/dim]\n")

    def _judgment_to_poi(self, judgment: JudgmentResult) -> POI:
        """
        Convert JudgmentResult back to POI for display.

        This is a helper method to reconstruct POI information from judgment data.

        Args:
            judgment: JudgmentResult object

        Returns:
            POI object (may have limited information)
        """
        # Try to extract POI information from the judgment's content
        # This is best-effort reconstruction
        from tour_guide.models.poi import POI, POICategory

        # Get category from first content item if available
        category = POICategory.HISTORICAL  # Default

        # Try to parse category from content metadata if available
        if judgment.all_content:
            # Check if any content has category info in metadata
            for content in judgment.all_content:
                if "category" in content.metadata:
                    try:
                        category = POICategory(content.metadata["category"])
                        break
                    except:
                        pass

        # Create POI with available information
        poi = POI(
            name=judgment.poi_name,
            lat=0.0,  # Not available from judgment
            lon=0.0,  # Not available from judgment
            description="",  # Not available from judgment
            category=category,
            distance_from_start_km=0.0,  # Not available from judgment
        )

        return poi

    def print_error(self, message: str) -> None:
        """
        Print an error message.

        Args:
            message: Error message to display
        """
        self.console.print(f"[bold red]❌ Error:[/bold red] {message}")

    def print_warning(self, message: str) -> None:
        """
        Print a warning message.

        Args:
            message: Warning message to display
        """
        self.console.print(f"[bold yellow]⚠️  Warning:[/bold yellow] {message}")

    def print_info(self, message: str) -> None:
        """
        Print an info message.

        Args:
            message: Info message to display
        """
        self.console.print(f"[bold cyan]ℹ️  Info:[/bold cyan] {message}")

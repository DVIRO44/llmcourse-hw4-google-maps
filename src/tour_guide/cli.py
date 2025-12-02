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
@click.option("--last", type=int, default=50, help="Number of log lines")
def diagnose(agent, last):
    """Analyze logs and find issues."""
    click.echo(f"Diagnosing {agent or 'all agents'}...")
    click.echo("Not implemented yet")


if __name__ == "__main__":
    main()

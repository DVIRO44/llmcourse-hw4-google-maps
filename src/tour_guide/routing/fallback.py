"""Claude fallback router for when OSRM fails."""

import json
from typing import Tuple
from tour_guide.routing.models import Route, Waypoint, RouteStep
from tour_guide.utils.claude_cli import call_claude, ClaudeError
from tour_guide.logging import get_logger

logger = get_logger("routing.fallback")


class ClaudeRouterError(Exception):
    """Claude router error."""

    pass


def get_route_from_claude(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    origin_name: str = None,
    destination_name: str = None,
) -> Route:
    """
    Generate route using Claude CLI.

    Args:
        origin: (lat, lon) tuple
        destination: (lat, lon) tuple
        origin_name: Optional name of origin
        destination_name: Optional name of destination

    Returns:
        Route object

    Raises:
        ClaudeRouterError: If Claude fails to generate route
    """
    origin_str = origin_name or f"{origin[0]:.4f},{origin[1]:.4f}"
    dest_str = destination_name or f"{destination[0]:.4f},{destination[1]:.4f}"

    prompt = f"""Generate a realistic driving route from {origin_str} to {dest_str}.

Provide a plausible route with 15-20 waypoints along the way.

Consider:
- Typical roads and highways between these locations
- Realistic driving distance and time
- Major landmarks or cities along the route

Return ONLY a JSON object in this exact format (no markdown, no explanation):
{{
  "distance_km": 65.0,
  "duration_minutes": 75.0,
  "waypoints": [
    {{"lat": {origin[0]}, "lon": {origin[1]}, "distance_from_start_km": 0.0}},
    ...
  ],
  "steps": [
    {{"instruction": "Head east on Highway 1", "distance_km": 30.0, "duration_min": 25.0}},
    ...
  ]
}}
"""

    logger.info(f"Requesting Claude fallback route: {origin_str} -> {dest_str}")

    try:
        response = call_claude(prompt, timeout=30)

        # Parse JSON response
        # Claude might wrap in ```json ... ```, so extract
        json_str = response
        if "```json" in response:
            start = response.index("```json") + 7
            end = response.index("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.index("```") + 3
            end = response.index("```", start)
            json_str = response[start:end].strip()

        data = json.loads(json_str)

        # Convert to Route object
        waypoints = [
            Waypoint(
                lat=w["lat"],
                lon=w["lon"],
                distance_from_start_km=w.get("distance_from_start_km", 0.0),
            )
            for w in data["waypoints"]
        ]

        steps = [
            RouteStep(
                instruction=s["instruction"],
                distance_km=s["distance_km"],
                duration_min=s["duration_min"],
            )
            for s in data.get("steps", [])
        ]

        logger.info(
            f"Claude route generated: {data['distance_km']:.1f} km, "
            f"{len(waypoints)} waypoints, {len(steps)} steps"
        )

        return Route(
            origin=origin,
            destination=destination,
            total_distance_km=data["distance_km"],
            total_duration_min=data["duration_minutes"],
            waypoints=waypoints,
            steps=steps,
            source="claude",
        )

    except ClaudeError as e:
        logger.error(f"Claude CLI error: {e}")
        raise ClaudeRouterError(f"Claude CLI error: {e}")

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Failed to parse Claude response: {e}")
        raise ClaudeRouterError(f"Invalid Claude response: {e}")

    except Exception as e:
        logger.error(f"Unexpected error in Claude router: {e}")
        raise ClaudeRouterError(f"Unexpected error: {e}")

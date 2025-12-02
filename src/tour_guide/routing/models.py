"""Data models for routing."""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Waypoint:
    """A point along the route."""

    lat: float
    lon: float
    distance_from_start_km: float = 0.0


@dataclass
class RouteStep:
    """A step in the route directions."""

    instruction: str
    distance_km: float
    duration_min: float


@dataclass
class Route:
    """Complete route information."""

    origin: Tuple[float, float]  # (lat, lon)
    destination: Tuple[float, float]  # (lat, lon)
    total_distance_km: float
    total_duration_min: float
    waypoints: List[Waypoint]
    steps: List[RouteStep]
    source: str  # "osrm" or "claude"

    def get_sampled_waypoints(self, max_points: int = 30) -> List[Waypoint]:
        """
        Sample waypoints for long routes to reduce Claude API payload size.

        For routes with many waypoints, this returns an evenly distributed
        subset to prevent timeouts during POI analysis.

        Args:
            max_points: Maximum number of waypoints to return (default: 30)

        Returns:
            List of sampled waypoints, always including start and end points
        """
        if len(self.waypoints) <= max_points:
            return self.waypoints

        # Always include start and end
        sampled = [self.waypoints[0]]

        # Calculate step size for even distribution
        step = len(self.waypoints) / (max_points - 1)

        for i in range(1, max_points - 1):
            index = int(i * step)
            sampled.append(self.waypoints[index])

        sampled.append(self.waypoints[-1])
        return sampled

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

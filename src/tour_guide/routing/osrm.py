"""OSRM routing client."""

import requests
from typing import Tuple
from tour_guide.routing.models import Route, Waypoint, RouteStep
from tour_guide.config import get_settings
from tour_guide.logging import get_logger

logger = get_logger("routing.osrm")


class OSRMError(Exception):
    """OSRM API error."""

    pass


class OSRMClient:
    """Client for OSRM routing API."""

    def __init__(self, base_url: str = None):
        settings = get_settings()
        self.base_url = base_url or settings.routing.osrm_url
        self.timeout = settings.routing.timeout_seconds

    def get_route(
        self, origin: Tuple[float, float], destination: Tuple[float, float]
    ) -> Route:
        """
        Get route from OSRM API.

        Args:
            origin: (lat, lon) tuple
            destination: (lat, lon) tuple

        Returns:
            Route object

        Raises:
            OSRMError: If OSRM request fails
        """
        # OSRM uses lon,lat format (opposite of lat,lon)
        origin_str = f"{origin[1]},{origin[0]}"
        dest_str = f"{destination[1]},{destination[0]}"

        url = f"{self.base_url}/route/v1/driving/{origin_str};{dest_str}"
        params = {"overview": "full", "steps": "true", "geometries": "geojson"}

        logger.info(f"Requesting OSRM route: {origin} -> {destination}")

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "Ok":
                raise OSRMError(
                    f"OSRM returned error: {data.get('message', 'Unknown error')}"
                )

            return self._parse_response(data, origin, destination)

        except requests.Timeout:
            raise OSRMError(f"OSRM request timed out after {self.timeout}s")
        except requests.RequestException as e:
            raise OSRMError(f"OSRM request failed: {e}")
        except (KeyError, ValueError, IndexError) as e:
            raise OSRMError(f"Invalid OSRM response format: {e}")

    def _parse_response(
        self, data: dict, origin: Tuple[float, float], destination: Tuple[float, float]
    ) -> Route:
        """Parse OSRM JSON response into Route object."""
        route = data["routes"][0]

        # Extract waypoints from geometry
        coordinates = route["geometry"]["coordinates"]
        waypoints = []

        cumulative_distance = 0.0
        for i, coord in enumerate(coordinates):
            if i > 0:
                # Calculate distance increment (rough estimate)
                prev = coordinates[i - 1]
                distance_increment = self._haversine(
                    prev[1], prev[0], coord[1], coord[0]
                )
                cumulative_distance += distance_increment

            waypoints.append(
                Waypoint(lat=coord[1], lon=coord[0], distance_from_start_km=cumulative_distance)
            )

        # Extract steps
        steps = []
        if "legs" in route:
            for leg in route["legs"]:
                if "steps" in leg:
                    for step in leg["steps"]:
                        instruction = step.get("name", "Continue")
                        if step.get("maneuver"):
                            instruction = (
                                f"{step['maneuver'].get('type', 'turn')} {instruction}"
                            )

                        steps.append(
                            RouteStep(
                                instruction=instruction,
                                distance_km=step["distance"] / 1000,
                                duration_min=step["duration"] / 60,
                            )
                        )

        logger.info(
            f"OSRM route parsed: {route['distance']/1000:.1f} km, "
            f"{len(waypoints)} waypoints, {len(steps)} steps"
        )

        return Route(
            origin=origin,
            destination=destination,
            total_distance_km=route["distance"] / 1000,  # meters to km
            total_duration_min=route["duration"] / 60,  # seconds to minutes
            waypoints=waypoints,
            steps=steps,
            source="osrm",
        )

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula (km)."""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Earth radius in km

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

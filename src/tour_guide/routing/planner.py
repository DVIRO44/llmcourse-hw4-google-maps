"""Main routing interface with OSRM and Claude fallback."""

from typing import Union, Tuple
from tour_guide.routing.models import Route
from tour_guide.routing.osrm import OSRMClient, OSRMError
from tour_guide.routing.fallback import get_route_from_claude, ClaudeRouterError
from tour_guide.routing.geocoder import geocode
from tour_guide.config import get_settings
from tour_guide.logging import get_logger

logger = get_logger("routing.planner")


class RoutingError(Exception):
    """General routing error."""

    pass


class RoutePlanner:
    """Main routing interface with OSRM and Claude fallback."""

    def __init__(self):
        settings = get_settings()
        self.config = settings.routing
        self.osrm_client = OSRMClient()

    def plan_route(
        self,
        origin: Union[str, Tuple[float, float]],
        destination: Union[str, Tuple[float, float]],
    ) -> Route:
        """
        Plan route from origin to destination.

        Args:
            origin: Place name or (lat, lon) tuple
            destination: Place name or (lat, lon) tuple

        Returns:
            Route object

        Raises:
            RoutingError: If both OSRM and Claude fail
        """
        # Convert place names to coordinates if needed
        origin_coords, origin_name = self._resolve_location(origin)
        dest_coords, dest_name = self._resolve_location(destination)

        logger.info(f"Planning route: {origin_name} → {dest_name}")

        # Try OSRM first
        try:
            logger.debug("Attempting OSRM routing")
            route = self.osrm_client.get_route(origin_coords, dest_coords)
            logger.info(
                f"OSRM routing successful: {route.total_distance_km:.1f} km, "
                f"{route.total_duration_min:.1f} min"
            )
            return route

        except OSRMError as e:
            logger.warning(f"OSRM failed: {e}")

            if not self.config.fallback_to_claude:
                raise RoutingError(f"OSRM failed and Claude fallback disabled: {e}")

        # Fallback to Claude
        try:
            logger.debug("Falling back to Claude routing")
            route = get_route_from_claude(
                origin_coords, dest_coords, origin_name, dest_name
            )
            logger.info(
                f"Claude routing successful: {route.total_distance_km:.1f} km, "
                f"{route.total_duration_min:.1f} min"
            )
            return route

        except ClaudeRouterError as e:
            logger.error(f"Claude fallback also failed: {e}")
            raise RoutingError(f"Both OSRM and Claude routing failed: {e}")

    def _resolve_location(
        self, location: Union[str, Tuple[float, float]]
    ) -> Tuple[Tuple[float, float], str]:
        """
        Convert location to (coordinates, name) tuple.

        Args:
            location: Place name or (lat, lon) tuple

        Returns:
            Tuple of ((lat, lon), name)
        """
        if isinstance(location, tuple):
            # Already coordinates
            return location, f"{location[0]:.4f},{location[1]:.4f}"
        else:
            # Place name - need to geocode
            coords = geocode(location)
            return coords, location

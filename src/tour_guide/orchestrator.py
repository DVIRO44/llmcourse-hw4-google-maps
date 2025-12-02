"""Main orchestrator for Tour Guide system."""

import time
from dataclasses import dataclass
from typing import List, Dict, Optional

from tour_guide.routing.osrm import OSRMClient
from tour_guide.routing.models import Route
from tour_guide.models.poi import POI
from tour_guide.models.judgment import JudgmentResult
from tour_guide.agents.route_analyzer import RouteAnalyzerAgent
from tour_guide.parallel.pipeline import ContentPipeline
from tour_guide.logging import get_logger

logger = get_logger("orchestrator")


@dataclass
class JourneyResult:
    """Complete journey result with all data."""

    route: Route
    pois: List[POI]
    judgments: List[JudgmentResult]
    execution_time: float
    stats: Dict[str, any]


class TourGuideOrchestrator:
    """
    Main orchestrator that coordinates the entire tour guide system.

    Orchestrates the flow:
    1. Route planning (OSRM)
    2. POI discovery (RouteAnalyzerAgent)
    3. Content generation (ContentPipeline with parallel agents)
    4. Result compilation
    """

    def __init__(self):
        """Initialize orchestrator with all components."""
        self.logger = logger
        self.osrm_client = OSRMClient()
        self.route_analyzer = RouteAnalyzerAgent()
        self.content_pipeline = ContentPipeline()

    def run(
        self,
        origin: str,
        destination: str,
        options: Optional[Dict] = None,
    ) -> JourneyResult:
        """
        Run complete tour guide journey.

        Args:
            origin: Starting location name
            destination: Ending location name
            options: Optional configuration dict

        Returns:
            JourneyResult with complete journey data

        Raises:
            Exception: If critical steps fail
        """
        options = options or {}
        start_time = time.time()

        self.logger.info(f"Starting journey: {origin} → {destination}")

        try:
            # Step 1: Get route
            self.logger.info("Step 1: Planning route...")
            route = self._get_route(origin, destination)
            self.logger.info(
                f"Route planned: {route.total_distance_km:.1f} km, "
                f"{route.total_duration_min:.1f} min"
            )

            # Step 2: Analyze route for POIs
            self.logger.info("Step 2: Analyzing route for POIs...")
            pois = self._analyze_route(route)
            self.logger.info(f"Found {len(pois)} POIs along route")

            if not pois:
                self.logger.warning("No POIs found. Journey incomplete.")
                execution_time = time.time() - start_time
                return JourneyResult(
                    route=route,
                    pois=[],
                    judgments=[],
                    execution_time=execution_time,
                    stats=self._calculate_stats([], []),
                )

            # Step 3: Process POIs in parallel (content + judgment)
            self.logger.info("Step 3: Processing POIs with parallel agents...")
            judgments = self._process_pois(pois)
            self.logger.info(f"Generated {len(judgments)} judgments")

            # Step 4: Calculate stats
            execution_time = time.time() - start_time
            stats = self._calculate_stats(pois, judgments)

            self.logger.info(
                f"Journey complete in {execution_time:.2f}s: "
                f"{len(pois)} POIs, {len(judgments)} judgments"
            )

            return JourneyResult(
                route=route,
                pois=pois,
                judgments=judgments,
                execution_time=execution_time,
                stats=stats,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Journey failed after {execution_time:.2f}s: {e}")
            raise

    def _get_route(self, origin: str, destination: str) -> Route:
        """
        Get route from OSRM.

        Args:
            origin: Starting location
            destination: Ending location

        Returns:
            Route object
        """
        try:
            # For now, use hardcoded coordinates for common Israeli cities
            # In production, would use geocoding service
            coords_map = {
                "tel aviv": (32.0853, 34.7818),
                "jerusalem": (31.7683, 35.2137),
                "haifa": (32.7940, 34.9896),
                "eilat": (29.5577, 34.9519),
                "beer sheva": (31.2518, 34.7913),
                "akko": (32.9266, 35.0838),
                "jaffa": (32.0543, 34.7516),
                "dead sea": (31.5590, 35.4732),
                "nazareth": (32.7046, 35.2978),
                "tiberias": (32.7940, 35.5308),
                "caesarea": (32.5015, 34.8937),
                "masada": (31.3159, 35.3539),
                "rosh hanikra": (33.0894, 35.1075),
                "bethlehem": (31.7054, 35.2024),
                "holon": (32.0117, 34.7750),
                "kiryat shmona": (33.2074, 35.5697),
                "qiryat shmona": (33.2074, 35.5697),  # Alternative spelling
                "ashdod": (31.8044, 34.6553),
                "netanya": (32.3215, 34.8532),
                "rishon lezion": (31.9730, 34.7925),
                "petah tikva": (32.0878, 34.8878),
                "rehovot": (31.8969, 34.8186),
            }

            origin_lower = origin.lower()
            dest_lower = destination.lower()

            origin_coords = coords_map.get(origin_lower)
            dest_coords = coords_map.get(dest_lower)

            if not origin_coords or not dest_coords:
                raise ValueError(
                    f"Unknown location: {origin if not origin_coords else destination}"
                )

            route = self.osrm_client.get_route(origin_coords, dest_coords)
            return route

        except Exception as e:
            self.logger.error(f"Failed to get route: {e}")
            raise

    def _analyze_route(self, route: Route) -> List[POI]:
        """
        Analyze route to find POIs.

        Args:
            route: Route object

        Returns:
            List of POI objects
        """
        try:
            pois = self.route_analyzer.run(route)
            return pois

        except Exception as e:
            self.logger.error(f"Failed to analyze route: {e}")
            # Return empty list to allow journey to continue
            return []

    def _process_pois(self, pois: List[POI]) -> List[JudgmentResult]:
        """
        Process POIs through content pipeline.

        Args:
            pois: List of POI objects

        Returns:
            List of JudgmentResult objects
        """
        try:
            judgments = self.content_pipeline.run(pois)
            return judgments

        except Exception as e:
            self.logger.error(f"Failed to process POIs: {e}")
            # Return empty list to allow journey to continue
            return []

    def _calculate_stats(
        self, pois: List[POI], judgments: List[JudgmentResult]
    ) -> Dict[str, any]:
        """
        Calculate journey statistics.

        Args:
            pois: List of POIs
            judgments: List of judgments

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_pois": len(pois),
            "total_judgments": len(judgments),
            "content_distribution": {},
            "success_rate": 0.0,
        }

        if judgments:
            # Count content types
            for judgment in judgments:
                content_type = judgment.selected_type
                stats["content_distribution"][content_type] = (
                    stats["content_distribution"].get(content_type, 0) + 1
                )

            # Calculate success rate
            stats["success_rate"] = len(judgments) / len(pois) if pois else 0.0

        return stats

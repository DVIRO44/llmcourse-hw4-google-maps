"""Route analyzer agent for identifying points of interest along a route."""

import json
from typing import List
from tour_guide.agents.base import BaseAgent, AgentError
from tour_guide.routing.models import Route
from tour_guide.models import POI, POICategory
from tour_guide.utils.claude_cli import call_claude, ClaudeError
from tour_guide.skills.route_analyzer_skill import format_route_analyzer_prompt


class RouteAnalyzerAgent(BaseAgent):
    """Agent that analyzes routes and identifies interesting points of interest."""

    def __init__(self):
        """Initialize route analyzer agent."""
        super().__init__("route_analyzer")
        self.poi_count = self.settings.poi.count

    def run(self, input_data: Route) -> List[POI]:
        """
        Analyze route and identify points of interest.

        Args:
            input_data: Route object to analyze

        Returns:
            List of POI objects (up to self.poi_count POIs)

        Raises:
            AgentError: If route analysis fails
        """
        if not isinstance(input_data, Route):
            raise AgentError(f"Expected Route object, got {type(input_data)}")

        route = input_data

        self.logger.info(
            f"Analyzing route: {route.total_distance_km:.1f} km, "
            f"{len(route.waypoints)} waypoints"
        )

        # Determine appropriate POI count based on route length
        poi_count = self._determine_poi_count(route.total_distance_km)

        # Create prompt
        origin_str = f"{route.origin[0]:.4f},{route.origin[1]:.4f}"
        dest_str = f"{route.destination[0]:.4f},{route.destination[1]:.4f}"

        prompt = format_route_analyzer_prompt(
            origin=origin_str,
            destination=dest_str,
            distance_km=route.total_distance_km,
            duration_min=route.total_duration_min,
            waypoints_count=len(route.waypoints),
            poi_count=poi_count,
        )

        try:
            # Call Claude
            self.logger.debug(f"Requesting {poi_count} POIs from Claude")
            response = call_claude(prompt, timeout=30)

            # Parse response
            pois = self._parse_response(response)

            self.logger.info(f"Successfully identified {len(pois)} POIs")
            return pois

        except ClaudeError as e:
            error_msg = f"Claude CLI failed during route analysis: {e}"
            self.logger.error(error_msg)
            raise AgentError(error_msg)

        except Exception as e:
            error_msg = f"Route analysis failed: {e}"
            self.logger.error(error_msg)
            raise AgentError(error_msg)

    def _determine_poi_count(self, distance_km: float) -> int:
        """
        Determine appropriate number of POIs based on route length.

        Args:
            distance_km: Route distance in kilometers

        Returns:
            Number of POIs to request
        """
        if distance_km < 20:
            return min(3, self.poi_count)
        elif distance_km < 50:
            return min(5, self.poi_count)
        else:
            return self.poi_count

    def _parse_response(self, response: str) -> List[POI]:
        """
        Parse Claude's JSON response into POI objects.

        Args:
            response: Raw response from Claude

        Returns:
            List of POI objects

        Raises:
            AgentError: If response parsing fails
        """
        try:
            # Extract JSON from response (Claude might wrap in ```json ... ```)
            json_str = response.strip()

            if "```json" in json_str:
                start = json_str.index("```json") + 7
                end = json_str.index("```", start)
                json_str = json_str[start:end].strip()
            elif "```" in json_str:
                start = json_str.index("```") + 3
                end = json_str.index("```", start)
                json_str = json_str[start:end].strip()

            # Parse JSON
            data = json.loads(json_str)

            if "pois" not in data:
                raise AgentError("Response missing 'pois' field")

            # Convert to POI objects
            pois = []
            for poi_data in data["pois"]:
                try:
                    poi = POI(
                        name=poi_data["name"],
                        lat=poi_data["lat"],
                        lon=poi_data["lon"],
                        description=poi_data["description"],
                        category=poi_data["category"],
                        distance_from_start_km=poi_data["distance_from_start_km"],
                    )
                    pois.append(poi)
                except (KeyError, ValueError) as e:
                    self.logger.warning(f"Skipping invalid POI: {e}")
                    continue

            if not pois:
                raise AgentError("No valid POIs found in response")

            return pois

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse Claude response as JSON: {e}"
            self.logger.error(error_msg)
            raise AgentError(error_msg)

        except Exception as e:
            error_msg = f"Failed to parse Claude response: {e}"
            self.logger.error(error_msg)
            raise AgentError(error_msg)

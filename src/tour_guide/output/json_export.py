"""JSON export for Tour Guide journey data."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from tour_guide.routing.models import Route
from tour_guide.models.poi import POI
from tour_guide.models.judgment import JudgmentResult


class JSONExporter:
    """
    Export journey data to JSON format with schema validation.

    Creates structured JSON output with metadata, route information,
    POIs with selected content, and summary statistics.
    """

    def __init__(self, version: str = "0.1.0"):
        """
        Initialize JSON exporter.

        Args:
            version: Version number for the output format
        """
        self.version = version

    def to_dict(
        self,
        route: Route,
        pois: List[POI],
        judgments: List[JudgmentResult],
        execution_time: float = None,
    ) -> Dict[str, Any]:
        """
        Convert journey data to dictionary structure.

        Args:
            route: Route object with journey information
            pois: List of POI objects
            judgments: List of JudgmentResult objects
            execution_time: Optional execution time in seconds

        Returns:
            Dictionary with structured journey data
        """
        # Create metadata
        metadata = {
            "version": self.version,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

        if execution_time is not None:
            metadata["execution_time_seconds"] = round(execution_time, 2)

        # Create route data
        route_data = {
            "origin": {"lat": route.origin[0], "lon": route.origin[1]},
            "destination": {"lat": route.destination[0], "lon": route.destination[1]},
            "distance_km": round(route.total_distance_km, 2),
            "duration_min": round(route.total_duration_min, 1),
        }

        # Create POI data with judgments
        pois_data = []
        for poi, judgment in zip(pois, judgments):
            poi_data = {
                "name": poi.name,
                "coordinates": {
                    "lat": poi.lat,
                    "lon": poi.lon,
                },
                "category": poi.category.value,
                "distance_from_start_km": round(poi.distance_from_start_km, 2),
                "description": poi.description,
                "selected_content": {
                    "type": judgment.selected_type,
                    "title": judgment.selected_content.title,
                    "description": judgment.selected_content.description,
                    "score": judgment.selected_content.relevance_score,
                    "url": judgment.selected_content.url,
                    "metadata": judgment.selected_content.metadata,
                },
                "all_options": [
                    {
                        "type": content.content_type,
                        "title": content.title,
                        "description": content.description,
                        "score": content.relevance_score,
                        "url": content.url,
                    }
                    for content in judgment.all_content
                ],
                "judge_reasoning": judgment.reasoning,
                "judge_scores": judgment.scores,
            }
            pois_data.append(poi_data)

        # Create summary
        content_distribution = {}
        for judgment in judgments:
            content_type = judgment.selected_type
            content_distribution[content_type] = content_distribution.get(content_type, 0) + 1

        summary = {
            "total_pois": len(pois),
            "content_distribution": content_distribution,
        }

        # Combine all data
        journey_data = {
            "metadata": metadata,
            "route": route_data,
            "pois": pois_data,
            "summary": summary,
        }

        return journey_data

    def export(
        self,
        journey_data: Dict[str, Any],
        output_path: Path,
        indent: int = 2,
    ) -> None:
        """
        Export journey data to JSON file.

        Args:
            journey_data: Dictionary with journey data (from to_dict)
            output_path: Path where JSON file will be written
            indent: JSON indentation level (default 2)
        """
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(journey_data, f, indent=indent, ensure_ascii=False)

    def export_journey(
        self,
        route: Route,
        pois: List[POI],
        judgments: List[JudgmentResult],
        output_path: Path,
        execution_time: float = None,
    ) -> None:
        """
        Convenience method to convert and export journey data in one step.

        Args:
            route: Route object
            pois: List of POI objects
            judgments: List of JudgmentResult objects
            output_path: Path where JSON file will be written
            execution_time: Optional execution time in seconds
        """
        journey_data = self.to_dict(route, pois, judgments, execution_time)
        self.export(journey_data, output_path)

    def validate_structure(self, journey_data: Dict[str, Any]) -> bool:
        """
        Validate that journey data has required structure.

        Args:
            journey_data: Dictionary with journey data

        Returns:
            True if valid, False otherwise
        """
        # Check required top-level keys
        required_keys = ["metadata", "route", "pois", "summary"]
        if not all(key in journey_data for key in required_keys):
            return False

        # Check metadata
        metadata = journey_data["metadata"]
        if not all(key in metadata for key in ["version", "generated_at"]):
            return False

        # Check route
        route = journey_data["route"]
        if not all(
            key in route
            for key in ["origin", "destination", "distance_km", "duration_min"]
        ):
            return False

        # Check POIs (at least basic structure)
        pois = journey_data["pois"]
        if not isinstance(pois, list):
            return False

        for poi in pois:
            if not all(
                key in poi
                for key in [
                    "name",
                    "coordinates",
                    "category",
                    "selected_content",
                    "judge_reasoning",
                ]
            ):
                return False

        # Check summary
        summary = journey_data["summary"]
        if not all(key in summary for key in ["total_pois", "content_distribution"]):
            return False

        return True

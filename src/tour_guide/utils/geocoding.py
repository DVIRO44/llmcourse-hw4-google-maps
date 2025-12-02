"""Geocoding utilities using Claude for location resolution."""

import json
import re
from typing import Tuple, Optional
from tour_guide.utils.claude_cli import call_claude, ClaudeError
from tour_guide.logging import get_logger

logger = get_logger("geocoding")


GEOCODING_PROMPT = """You are a geocoding assistant. Given a location name, return its latitude and longitude coordinates.

Location: {location}

Return ONLY a JSON object in this exact format (no markdown, no explanation):
{{
  "lat": 31.7683,
  "lon": 35.2137,
  "confidence": "high"
}}

Requirements:
- Use the most commonly known coordinates for the location
- For cities, use the city center coordinates
- For countries, use the capital city coordinates
- Set confidence to "high" if certain, "medium" if approximate, "low" if guessing
- Ensure coordinates are valid: latitude between -90 and 90, longitude between -180 and 180
"""


def geocode_location(location: str) -> Optional[Tuple[float, float]]:
    """
    Geocode a location name to coordinates using Claude.

    Args:
        location: Location name to geocode

    Returns:
        Tuple of (lat, lon) coordinates, or None if geocoding fails

    Raises:
        ValueError: If coordinates are invalid
    """
    logger.info(f"Geocoding location: {location}")

    try:
        # Call Claude to geocode
        prompt = GEOCODING_PROMPT.format(location=location)
        response = call_claude(prompt, timeout=20)

        # Parse response
        coords = _parse_geocoding_response(response)

        if coords:
            lat, lon = coords
            logger.info(
                f"Successfully geocoded '{location}' to ({lat:.4f}, {lon:.4f})"
            )
            return coords
        else:
            logger.warning(f"Failed to geocode location: {location}")
            return None

    except ClaudeError as e:
        logger.error(f"Claude CLI error during geocoding: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error during geocoding: {e}")
        return None


def _parse_geocoding_response(response: str) -> Optional[Tuple[float, float]]:
    """
    Parse Claude's geocoding response.

    Args:
        response: Raw response from Claude

    Returns:
        Tuple of (lat, lon) or None if parsing fails
    """
    try:
        # Extract JSON from response
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

        if "lat" not in data or "lon" not in data:
            logger.warning("Geocoding response missing lat or lon fields")
            return None

        lat = float(data["lat"])
        lon = float(data["lon"])

        # Validate coordinates
        if not (-90 <= lat <= 90):
            logger.warning(f"Invalid latitude: {lat}")
            return None

        if not (-180 <= lon <= 180):
            logger.warning(f"Invalid longitude: {lon}")
            return None

        return (lat, lon)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse geocoding response as JSON: {e}")
        return None

    except (KeyError, ValueError) as e:
        logger.error(f"Failed to extract coordinates from response: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error parsing geocoding response: {e}")
        return None

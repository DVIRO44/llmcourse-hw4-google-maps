"""Simple geocoder for known locations."""

from typing import Tuple
from tour_guide.logging import get_logger

logger = get_logger("routing.geocoder")

# Simple hardcoded geocoding for Israeli cities
KNOWN_LOCATIONS = {
    "tel aviv": (32.0853, 34.7818),
    "jerusalem": (31.7683, 35.2137),
    "haifa": (32.7940, 34.9896),
    "eilat": (29.5577, 34.9519),
    "beer sheva": (31.2518, 34.7913),
    "nazareth": (32.7008, 35.2978),
    "akko": (32.9276, 35.0833),
    "caesarea": (32.5014, 34.8939),
    "masada": (31.3157, 35.3540),
    "dead sea": (31.5590, 35.4732),
    "tiberias": (32.7956, 35.5317),
    "rosh hanikra": (33.0891, 35.1064),
    "bethlehem": (31.7054, 35.2024),
    "jaffa": (32.0543, 34.7516),
}


def geocode(place_name: str) -> Tuple[float, float]:
    """
    Simple geocoder for known locations.

    Args:
        place_name: Name of place

    Returns:
        (lat, lon) tuple

    Raises:
        ValueError: If place not found
    """
    normalized = place_name.lower().strip()

    if normalized in KNOWN_LOCATIONS:
        coords = KNOWN_LOCATIONS[normalized]
        logger.debug(f"Geocoded '{place_name}' to {coords}")
        return coords

    # TODO: Use Claude CLI for geocoding unknown places
    raise ValueError(
        f"Unknown location: {place_name}. Add to KNOWN_LOCATIONS or implement Claude geocoding."
    )

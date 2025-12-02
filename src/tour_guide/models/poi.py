"""Point of Interest (POI) data model."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class POICategory(Enum):
    """Categories for points of interest."""

    HISTORICAL = "historical"
    CULTURAL = "cultural"
    NATURAL = "natural"
    RELIGIOUS = "religious"
    ENTERTAINMENT = "entertainment"


@dataclass
class POI:
    """
    Point of Interest along a route.

    Attributes:
        name: Name of the POI
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        description: Description of the POI (2-3 sentences)
        category: Category of the POI
        distance_from_start_km: Distance from route start in kilometers
    """

    name: str
    lat: float
    lon: float
    description: str
    category: POICategory
    distance_from_start_km: float

    def __post_init__(self):
        """Validate POI data after initialization."""
        # Validate coordinates
        if not -90 <= self.lat <= 90:
            raise ValueError(f"Invalid latitude: {self.lat}. Must be between -90 and 90.")

        if not -180 <= self.lon <= 180:
            raise ValueError(
                f"Invalid longitude: {self.lon}. Must be between -180 and 180."
            )

        # Validate distance
        if self.distance_from_start_km < 0:
            raise ValueError(
                f"Invalid distance: {self.distance_from_start_km}. Must be >= 0."
            )

        # Convert category string to enum if needed
        if isinstance(self.category, str):
            try:
                self.category = POICategory(self.category.lower())
            except ValueError:
                valid_categories = [c.value for c in POICategory]
                raise ValueError(
                    f"Invalid category: {self.category}. Must be one of {valid_categories}"
                )

    @property
    def coordinates(self) -> tuple[float, float]:
        """Get coordinates as (lat, lon) tuple."""
        return (self.lat, self.lon)

"""Skill prompt for route analyzer agent."""

ROUTE_ANALYZER_PROMPT = """Analyze this driving route and identify the {poi_count} most interesting points of interest.

Route: {origin} to {destination}
Total Distance: {distance_km:.1f} km
Total Duration: {duration_min:.0f} minutes
Waypoints: {waypoints_count} waypoints along the route

For each POI, provide:
- name: The place name
- lat: Latitude
- lon: Longitude
- description: 2-3 sentence description
- category: One of (historical, cultural, natural, religious, entertainment)
- distance_from_start_km: Approximate distance from route start in kilometers

Selection criteria:
- Historical significance (UNESCO sites, monuments, battlefields, ancient ruins)
- Cultural importance (museums, religious sites, traditional markets, cultural centers)
- Natural beauty (national parks, viewpoints, beaches, geological formations)
- Tourist popularity (highly rated attractions, famous locations)
- Even distribution along the route (not clustered)

Requirements:
- Select exactly {poi_count} POIs (or fewer if route is very short < 20 km)
- Distribute POIs evenly along the route (minimum 5 km apart when possible)
- Ensure each POI is actually near the route (within 5 km)
- Provide complete metadata for each POI

Return ONLY a JSON array in this exact format (no markdown, no explanation):
{{
  "pois": [
    {{
      "name": "Example Site",
      "lat": 31.3157,
      "lon": 35.3540,
      "description": "Brief description here.",
      "category": "historical",
      "distance_from_start_km": 45.2
    }}
  ]
}}
"""


def format_route_analyzer_prompt(
    origin: str,
    destination: str,
    distance_km: float,
    duration_min: float,
    waypoints_count: int,
    poi_count: int = 10,
) -> str:
    """
    Format the route analyzer prompt with route data.

    Args:
        origin: Origin location name
        destination: Destination location name
        distance_km: Total route distance in km
        duration_min: Total route duration in minutes
        waypoints_count: Number of waypoints
        poi_count: Number of POIs to select (default: 10)

    Returns:
        Formatted prompt string
    """
    return ROUTE_ANALYZER_PROMPT.format(
        origin=origin,
        destination=destination,
        distance_km=distance_km,
        duration_min=duration_min,
        waypoints_count=waypoints_count,
        poi_count=poi_count,
    )

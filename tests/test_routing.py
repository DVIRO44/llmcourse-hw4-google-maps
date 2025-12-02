"""Tests for routing system."""

import pytest
import subprocess
from unittest.mock import Mock, patch
from tour_guide.routing.osrm import OSRMClient, OSRMError
from tour_guide.routing.fallback import get_route_from_claude, ClaudeRouterError
from tour_guide.routing.models import Route
from tour_guide.utils.claude_cli import call_claude, ClaudeError


class TestOSRMClient:
    """Tests for OSRM client."""

    @pytest.fixture
    def osrm_client(self):
        """Create OSRM client instance."""
        return OSRMClient()

    @pytest.fixture
    def mock_osrm_response(self):
        """Mock successful OSRM response."""
        return {
            "code": "Ok",
            "routes": [
                {
                    "distance": 65000,  # 65 km in meters
                    "duration": 4500,  # 75 minutes in seconds
                    "geometry": {
                        "coordinates": [
                            [34.7818, 32.0853],  # Tel Aviv (lon, lat)
                            [35.0, 32.0],  # Intermediate
                            [35.2137, 31.7683],  # Jerusalem (lon, lat)
                        ]
                    },
                    "legs": [
                        {
                            "steps": [
                                {
                                    "name": "Highway 1",
                                    "distance": 30000,
                                    "duration": 2000,
                                    "maneuver": {"type": "turn"},
                                },
                                {
                                    "name": "Road 443",
                                    "distance": 35000,
                                    "duration": 2500,
                                },
                            ]
                        }
                    ],
                }
            ],
        }

    def test_get_route_success(self, osrm_client, mock_osrm_response):
        """Test successful route retrieval."""
        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = mock_osrm_response
            mock_get.return_value.raise_for_status = Mock()

            origin = (32.0853, 34.7818)  # Tel Aviv
            destination = (31.7683, 35.2137)  # Jerusalem

            route = osrm_client.get_route(origin, destination)

            assert isinstance(route, Route)
            assert route.origin == origin
            assert route.destination == destination
            assert route.total_distance_km == 65.0
            assert route.total_duration_min == 75.0
            assert len(route.waypoints) == 3
            assert len(route.steps) == 2
            assert route.source == "osrm"

    def test_get_route_timeout(self, osrm_client):
        """Test timeout handling."""
        with patch("requests.get") as mock_get:
            import requests

            mock_get.side_effect = requests.Timeout()

            origin = (32.0853, 34.7818)
            destination = (31.7683, 35.2137)

            with pytest.raises(OSRMError) as exc_info:
                osrm_client.get_route(origin, destination)

            assert "timed out" in str(exc_info.value)

    def test_get_route_invalid_response(self, osrm_client):
        """Test handling of invalid OSRM response."""
        with patch("requests.get") as mock_get:
            # Missing required fields
            mock_get.return_value.json.return_value = {"code": "Ok", "routes": [{}]}
            mock_get.return_value.raise_for_status = Mock()

            origin = (32.0853, 34.7818)
            destination = (31.7683, 35.2137)

            with pytest.raises(OSRMError) as exc_info:
                osrm_client.get_route(origin, destination)

            assert "Invalid OSRM response" in str(exc_info.value)

    def test_get_route_osrm_error(self, osrm_client):
        """Test handling of OSRM error response."""
        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = {
                "code": "InvalidInput",
                "message": "Invalid coordinates",
            }
            mock_get.return_value.raise_for_status = Mock()

            origin = (200.0, 200.0)  # Invalid coordinates
            destination = (31.7683, 35.2137)

            with pytest.raises(OSRMError) as exc_info:
                osrm_client.get_route(origin, destination)

            assert "OSRM returned error" in str(exc_info.value)

    def test_haversine_distance(self):
        """Test haversine distance calculation."""
        from tour_guide.routing.osrm import OSRMClient

        # Tel Aviv to Jerusalem is approximately 54 km (straight line)
        distance = OSRMClient._haversine(32.0853, 34.7818, 31.7683, 35.2137)
        assert 50 < distance < 60  # Rough check


class TestClaudeCLI:
    """Tests for Claude CLI wrapper."""

    def test_call_claude_success(self):
        """Test successful Claude CLI call."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "Test response"
            mock_run.return_value.returncode = 0

            response = call_claude("Test prompt")

            assert response == "Test response"
            mock_run.assert_called_once()

    def test_call_claude_timeout(self):
        """Test Claude CLI timeout."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("claude", 30)

            with pytest.raises(ClaudeError) as exc_info:
                call_claude("Test prompt", timeout=30)

            assert "timed out" in str(exc_info.value)

    def test_call_claude_not_found(self):
        """Test Claude CLI not found."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            with pytest.raises(ClaudeError) as exc_info:
                call_claude("Test prompt")

            assert "not found" in str(exc_info.value)


class TestClaudeFallbackRouter:
    """Tests for Claude fallback router."""

    @pytest.fixture
    def mock_claude_response(self):
        """Mock Claude response with route data."""
        return """```json
{
  "distance_km": 65.0,
  "duration_minutes": 75.0,
  "waypoints": [
    {"lat": 32.0853, "lon": 34.7818, "distance_from_start_km": 0.0},
    {"lat": 32.0, "lon": 35.0, "distance_from_start_km": 30.0},
    {"lat": 31.7683, "lon": 35.2137, "distance_from_start_km": 65.0}
  ],
  "steps": [
    {"instruction": "Head east on Highway 1", "distance_km": 30.0, "duration_min": 25.0},
    {"instruction": "Continue on Road 443", "distance_km": 35.0, "duration_min": 50.0}
  ]
}
```"""

    def test_get_route_from_claude_success(self, mock_claude_response):
        """Test successful Claude fallback routing."""
        with patch(
            "tour_guide.routing.fallback.call_claude"
        ) as mock_call:
            mock_call.return_value = mock_claude_response

            origin = (32.0853, 34.7818)
            destination = (31.7683, 35.2137)

            route = get_route_from_claude(
                origin, destination, "Tel Aviv", "Jerusalem"
            )

            assert isinstance(route, Route)
            assert route.origin == origin
            assert route.destination == destination
            assert route.total_distance_km == 65.0
            assert route.total_duration_min == 75.0
            assert len(route.waypoints) == 3
            assert len(route.steps) == 2
            assert route.source == "claude"

    def test_get_route_from_claude_invalid_json(self):
        """Test handling of invalid JSON from Claude."""
        with patch(
            "tour_guide.routing.fallback.call_claude"
        ) as mock_call:
            mock_call.return_value = "Invalid JSON response"

            origin = (32.0853, 34.7818)
            destination = (31.7683, 35.2137)

            with pytest.raises(ClaudeRouterError) as exc_info:
                get_route_from_claude(origin, destination)

            assert "Invalid Claude response" in str(exc_info.value)

    def test_get_route_from_claude_cli_error(self):
        """Test handling of Claude CLI error."""
        with patch(
            "tour_guide.routing.fallback.call_claude"
        ) as mock_call:
            mock_call.side_effect = ClaudeError("CLI error")

            origin = (32.0853, 34.7818)
            destination = (31.7683, 35.2137)

            with pytest.raises(ClaudeRouterError) as exc_info:
                get_route_from_claude(origin, destination)

            assert "Claude CLI error" in str(exc_info.value)


class TestGeocoder:
    """Tests for geocoding."""

    def test_geocode_known_location(self):
        """Test geocoding a known location."""
        from tour_guide.routing.geocoder import geocode

        coords = geocode("Tel Aviv")
        assert coords == (32.0853, 34.7818)

    def test_geocode_case_insensitive(self):
        """Test that geocoding is case-insensitive."""
        from tour_guide.routing.geocoder import geocode

        coords1 = geocode("jerusalem")
        coords2 = geocode("Jerusalem")
        coords3 = geocode("JERUSALEM")

        assert coords1 == coords2 == coords3

    def test_geocode_unknown_location(self):
        """Test that unknown locations raise ValueError."""
        from tour_guide.routing.geocoder import geocode

        with pytest.raises(ValueError) as exc_info:
            geocode("Unknown City")

        assert "Unknown location" in str(exc_info.value)


class TestRoutePlanner:
    """Tests for route planner."""

    @pytest.fixture
    def planner(self):
        """Create route planner instance."""
        from tour_guide.routing.planner import RoutePlanner

        return RoutePlanner()

    @pytest.fixture
    def mock_osrm_response(self):
        """Mock successful OSRM response."""
        return {
            "code": "Ok",
            "routes": [
                {
                    "distance": 65000,
                    "duration": 4500,
                    "geometry": {
                        "coordinates": [
                            [34.7818, 32.0853],
                            [35.0, 32.0],
                            [35.2137, 31.7683],
                        ]
                    },
                    "legs": [
                        {
                            "steps": [
                                {
                                    "name": "Highway 1",
                                    "distance": 30000,
                                    "duration": 2000,
                                    "maneuver": {"type": "turn"},
                                },
                                {
                                    "name": "Road 443",
                                    "distance": 35000,
                                    "duration": 2500,
                                },
                            ]
                        }
                    ],
                }
            ],
        }

    def test_plan_route_with_coordinates(self, planner, mock_osrm_response):
        """Test planning route with coordinate tuples."""
        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = mock_osrm_response
            mock_get.return_value.raise_for_status = Mock()

            origin = (32.0853, 34.7818)
            destination = (31.7683, 35.2137)

            route = planner.plan_route(origin, destination)

            assert isinstance(route, Route)
            assert route.origin == origin
            assert route.destination == destination
            assert route.source == "osrm"

    def test_plan_route_with_place_names(self, planner, mock_osrm_response):
        """Test planning route with place names."""
        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = mock_osrm_response
            mock_get.return_value.raise_for_status = Mock()

            route = planner.plan_route("Tel Aviv", "Jerusalem")

            assert isinstance(route, Route)
            assert route.origin == (32.0853, 34.7818)
            assert route.destination == (31.7683, 35.2137)
            assert route.source == "osrm"

    def test_plan_route_osrm_fails_fallback_to_claude(self, planner):
        """Test that planner falls back to Claude when OSRM fails."""
        claude_response = """```json
{
  "distance_km": 65.0,
  "duration_minutes": 75.0,
  "waypoints": [
    {"lat": 32.0853, "lon": 34.7818, "distance_from_start_km": 0.0},
    {"lat": 31.7683, "lon": 35.2137, "distance_from_start_km": 65.0}
  ],
  "steps": [
    {"instruction": "Head east on Highway 1", "distance_km": 65.0, "duration_min": 75.0}
  ]
}
```"""

        with patch("requests.get") as mock_get, patch(
            "tour_guide.routing.fallback.call_claude"
        ) as mock_claude:
            # OSRM fails
            import requests

            mock_get.side_effect = requests.Timeout()

            # Claude succeeds
            mock_claude.return_value = claude_response

            origin = (32.0853, 34.7818)
            destination = (31.7683, 35.2137)

            route = planner.plan_route(origin, destination)

            assert isinstance(route, Route)
            assert route.source == "claude"
            assert route.total_distance_km == 65.0

    def test_plan_route_both_fail(self, planner):
        """Test that planner raises RoutingError when both OSRM and Claude fail."""
        from tour_guide.routing.planner import RoutingError

        with patch("requests.get") as mock_get, patch(
            "tour_guide.routing.fallback.call_claude"
        ) as mock_claude:
            # OSRM fails
            import requests

            mock_get.side_effect = requests.Timeout()

            # Claude fails
            mock_claude.return_value = "Invalid response"

            origin = (32.0853, 34.7818)
            destination = (31.7683, 35.2137)

            with pytest.raises(RoutingError) as exc_info:
                planner.plan_route(origin, destination)

            assert "Both OSRM and Claude routing failed" in str(exc_info.value)

    def test_plan_route_fallback_disabled(self, planner, mock_osrm_response):
        """Test that planner respects fallback_to_claude setting."""
        from tour_guide.routing.planner import RoutingError

        # Disable fallback
        planner.config.fallback_to_claude = False

        with patch("requests.get") as mock_get:
            # OSRM fails
            import requests

            mock_get.side_effect = requests.Timeout()

            origin = (32.0853, 34.7818)
            destination = (31.7683, 35.2137)

            with pytest.raises(RoutingError) as exc_info:
                planner.plan_route(origin, destination)

            assert "Claude fallback disabled" in str(exc_info.value)

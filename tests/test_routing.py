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

"""Tests for routing system."""

import pytest
from unittest.mock import Mock, patch
from tour_guide.routing.osrm import OSRMClient, OSRMError
from tour_guide.routing.models import Route


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

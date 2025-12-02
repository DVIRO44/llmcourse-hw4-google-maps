"""Test fixtures for 10 different Israeli routes.

This module provides test fixtures for comprehensive route testing.
Each fixture represents a different route across Israel with expected characteristics.
"""

import pytest
from tour_guide.routing.models import Route, Waypoint, RouteStep
from tour_guide.models.poi import POI, POICategory


@pytest.fixture
def route_tel_aviv_jerusalem():
    """Tel Aviv to Jerusalem - Classic central route."""
    return Route(
        origin=(32.0853, 34.7818),
        destination=(31.7683, 35.2137),
        total_distance_km=65.0,
        total_duration_min=55.0,
        waypoints=[
            Waypoint(lat=32.0853, lon=34.7818, distance_from_start_km=0.0),
            Waypoint(lat=31.8356, lon=34.9869, distance_from_start_km=30.0),
            Waypoint(lat=31.7683, lon=35.2137, distance_from_start_km=65.0),
        ],
        steps=[
            RouteStep(instruction="Head east on Route 1", distance_km=30.0, duration_min=25.0),
            RouteStep(instruction="Continue to Jerusalem", distance_km=35.0, duration_min=30.0),
        ],
        source="osrm",
    )


@pytest.fixture
def route_haifa_tel_aviv():
    """Haifa to Tel Aviv - Northern coastal route."""
    return Route(
        origin=(32.7940, 34.9896),
        destination=(32.0853, 34.7818),
        total_distance_km=95.0,
        total_duration_min=75.0,
        waypoints=[
            Waypoint(lat=32.7940, lon=34.9896, distance_from_start_km=0.0),
            Waypoint(lat=32.5015, lon=34.8937, distance_from_start_km=40.0),
            Waypoint(lat=32.0853, lon=34.7818, distance_from_start_km=95.0),
        ],
        steps=[
            RouteStep(instruction="Head south on Route 2", distance_km=40.0, duration_min=35.0),
            RouteStep(instruction="Continue to Tel Aviv", distance_km=55.0, duration_min=40.0),
        ],
        source="osrm",
    )


@pytest.fixture
def route_jerusalem_eilat():
    """Jerusalem to Eilat - Long desert route south."""
    return Route(
        origin=(31.7683, 35.2137),
        destination=(29.5577, 34.9519),
        total_distance_km=310.0,
        total_duration_min=240.0,
        waypoints=[
            Waypoint(lat=31.7683, lon=35.2137, distance_from_start_km=0.0),
            Waypoint(lat=31.3159, lon=35.3539, distance_from_start_km=60.0),  # Masada area
            Waypoint(lat=30.8, lon=35.1, distance_from_start_km=140.0),
            Waypoint(lat=29.5577, lon=34.9519, distance_from_start_km=310.0),
        ],
        steps=[
            RouteStep(instruction="Head south on Route 90", distance_km=140.0, duration_min=105.0),
            RouteStep(instruction="Continue south to Eilat", distance_km=170.0, duration_min=135.0),
        ],
        source="osrm",
    )


@pytest.fixture
def route_tel_aviv_haifa():
    """Tel Aviv to Haifa - Northern coastal route."""
    return Route(
        origin=(32.0853, 34.7818),
        destination=(32.7940, 34.9896),
        total_distance_km=95.0,
        total_duration_min=75.0,
        waypoints=[
            Waypoint(lat=32.0853, lon=34.7818, distance_from_start_km=0.0),
            Waypoint(lat=32.5015, lon=34.8937, distance_from_start_km=55.0),  # Caesarea
            Waypoint(lat=32.7940, lon=34.9896, distance_from_start_km=95.0),
        ],
        steps=[
            RouteStep(instruction="Head north on Route 2", distance_km=55.0, duration_min=40.0),
            RouteStep(instruction="Continue to Haifa", distance_km=40.0, duration_min=35.0),
        ],
        source="osrm",
    )


@pytest.fixture
def route_haifa_akko():
    """Haifa to Akko - Short northern coastal route."""
    return Route(
        origin=(32.7940, 34.9896),
        destination=(32.9266, 35.0838),
        total_distance_km=22.0,
        total_duration_min=20.0,
        waypoints=[
            Waypoint(lat=32.7940, lon=34.9896, distance_from_start_km=0.0),
            Waypoint(lat=32.9266, lon=35.0838, distance_from_start_km=22.0),
        ],
        steps=[
            RouteStep(instruction="Head north on Route 4", distance_km=22.0, duration_min=20.0),
        ],
        source="osrm",
    )


@pytest.fixture
def route_tel_aviv_beer_sheva():
    """Tel Aviv to Beer Sheva - Southern route."""
    return Route(
        origin=(32.0853, 34.7818),
        destination=(31.2518, 34.7913),
        total_distance_km=110.0,
        total_duration_min=85.0,
        waypoints=[
            Waypoint(lat=32.0853, lon=34.7818, distance_from_start_km=0.0),
            Waypoint(lat=31.6, lon=34.79, distance_from_start_km=55.0),
            Waypoint(lat=31.2518, lon=34.7913, distance_from_start_km=110.0),
        ],
        steps=[
            RouteStep(instruction="Head south on Route 4", distance_km=55.0, duration_min=40.0),
            RouteStep(instruction="Continue to Beer Sheva", distance_km=55.0, duration_min=45.0),
        ],
        source="osrm",
    )


@pytest.fixture
def route_jerusalem_dead_sea():
    """Jerusalem to Dead Sea - Eastern descent."""
    return Route(
        origin=(31.7683, 35.2137),
        destination=(31.5590, 35.4732),
        total_distance_km=55.0,
        total_duration_min=50.0,
        waypoints=[
            Waypoint(lat=31.7683, lon=35.2137, distance_from_start_km=0.0),
            Waypoint(lat=31.6, lon=35.35, distance_from_start_km=25.0),
            Waypoint(lat=31.5590, lon=35.4732, distance_from_start_km=55.0),
        ],
        steps=[
            RouteStep(instruction="Head east on Route 1", distance_km=25.0, duration_min=20.0),
            RouteStep(instruction="Descend to Dead Sea", distance_km=30.0, duration_min=30.0),
        ],
        source="osrm",
    )


@pytest.fixture
def route_tel_aviv_nazareth():
    """Tel Aviv to Nazareth - Northern inland route."""
    return Route(
        origin=(32.0853, 34.7818),
        destination=(32.7046, 35.2978),
        total_distance_km=120.0,
        total_duration_min=95.0,
        waypoints=[
            Waypoint(lat=32.0853, lon=34.7818, distance_from_start_km=0.0),
            Waypoint(lat=32.4, lon=35.0, distance_from_start_km=60.0),
            Waypoint(lat=32.7046, lon=35.2978, distance_from_start_km=120.0),
        ],
        steps=[
            RouteStep(instruction="Head north on Route 6", distance_km=60.0, duration_min=45.0),
            RouteStep(instruction="Continue to Nazareth", distance_km=60.0, duration_min=50.0),
        ],
        source="osrm",
    )


@pytest.fixture
def route_haifa_tiberias():
    """Haifa to Tiberias - Eastern route to Sea of Galilee."""
    return Route(
        origin=(32.7940, 34.9896),
        destination=(32.7940, 35.5308),
        total_distance_km=65.0,
        total_duration_min=55.0,
        waypoints=[
            Waypoint(lat=32.7940, lon=34.9896, distance_from_start_km=0.0),
            Waypoint(lat=32.7046, lon=35.2978, distance_from_start_km=35.0),  # Near Nazareth
            Waypoint(lat=32.7940, lon=35.5308, distance_from_start_km=65.0),
        ],
        steps=[
            RouteStep(instruction="Head east on Route 75", distance_km=35.0, duration_min=28.0),
            RouteStep(instruction="Continue to Tiberias", distance_km=30.0, duration_min=27.0),
        ],
        source="osrm",
    )


@pytest.fixture
def route_akko_rosh_hanikra():
    """Akko to Rosh Hanikra - Northern border route."""
    return Route(
        origin=(32.9266, 35.0838),
        destination=(33.0894, 35.1075),
        total_distance_km=18.0,
        total_duration_min=16.0,
        waypoints=[
            Waypoint(lat=32.9266, lon=35.0838, distance_from_start_km=0.0),
            Waypoint(lat=33.0894, lon=35.1075, distance_from_start_km=18.0),
        ],
        steps=[
            RouteStep(instruction="Head north on Route 4", distance_km=18.0, duration_min=16.0),
        ],
        source="osrm",
    )


# Sample POIs for each route
@pytest.fixture
def pois_tel_aviv_jerusalem():
    """Sample POIs for Tel Aviv to Jerusalem route."""
    return [
        POI(
            name="Latrun Monastery",
            lat=31.8356,
            lon=34.9869,
            description="Historic Trappist monastery with scenic views and museum",
            category=POICategory.RELIGIOUS,
            distance_from_start_km=30.0,
        ),
        POI(
            name="Mini Israel",
            lat=31.8514,
            lon=34.9891,
            description="Miniature park featuring models of Israeli landmarks",
            category=POICategory.CULTURAL,
            distance_from_start_km=32.0,
        ),
    ]


@pytest.fixture
def pois_haifa_tel_aviv():
    """Sample POIs for Haifa to Tel Aviv route."""
    return [
        POI(
            name="Caesarea National Park",
            lat=32.5015,
            lon=34.8937,
            description="Ancient Roman port city with impressive ruins",
            category=POICategory.HISTORICAL,
            distance_from_start_km=40.0,
        ),
    ]


@pytest.fixture
def pois_jerusalem_eilat():
    """Sample POIs for Jerusalem to Eilat route."""
    return [
        POI(
            name="Masada",
            lat=31.3159,
            lon=35.3539,
            description="Ancient fortress with stunning desert views",
            category=POICategory.HISTORICAL,
            distance_from_start_km=60.0,
        ),
        POI(
            name="Timna Park",
            lat=29.7833,
            lon=34.9500,
            description="Unique geological formations and ancient copper mines",
            category=POICategory.NATURAL,
            distance_from_start_km=280.0,
        ),
    ]


@pytest.fixture
def all_routes(
    route_tel_aviv_jerusalem,
    route_haifa_tel_aviv,
    route_jerusalem_eilat,
    route_tel_aviv_haifa,
    route_haifa_akko,
    route_tel_aviv_beer_sheva,
    route_jerusalem_dead_sea,
    route_tel_aviv_nazareth,
    route_haifa_tiberias,
    route_akko_rosh_hanikra,
):
    """All 10 test routes as a list."""
    return [
        ("Tel Aviv to Jerusalem", route_tel_aviv_jerusalem),
        ("Haifa to Tel Aviv", route_haifa_tel_aviv),
        ("Jerusalem to Eilat", route_jerusalem_eilat),
        ("Tel Aviv to Haifa", route_tel_aviv_haifa),
        ("Haifa to Akko", route_haifa_akko),
        ("Tel Aviv to Beer Sheva", route_tel_aviv_beer_sheva),
        ("Jerusalem to Dead Sea", route_jerusalem_dead_sea),
        ("Tel Aviv to Nazareth", route_tel_aviv_nazareth),
        ("Haifa to Tiberias", route_haifa_tiberias),
        ("Akko to Rosh Hanikra", route_akko_rosh_hanikra),
    ]


class TestRouteFixtures:
    """Tests to verify route fixtures are valid."""

    def test_all_routes_have_correct_structure(self, all_routes):
        """Test that all route fixtures have valid structure."""
        assert len(all_routes) == 10, "Should have exactly 10 routes"

        for name, route in all_routes:
            assert isinstance(name, str)
            assert isinstance(route, Route)
            assert route.total_distance_km > 0
            assert route.total_duration_min > 0
            assert len(route.waypoints) >= 2
            assert len(route.steps) >= 1
            assert route.source == "osrm"

    def test_route_distances(self, all_routes):
        """Test that route distances are realistic."""
        for name, route in all_routes:
            # All routes should be between 10 km and 500 km
            assert 10 <= route.total_distance_km <= 500, f"{name} has unrealistic distance"

    def test_route_durations(self, all_routes):
        """Test that route durations are realistic."""
        for name, route in all_routes:
            # Duration should be reasonable (10 min to 5 hours)
            assert 10 <= route.total_duration_min <= 300, f"{name} has unrealistic duration"

    def test_waypoints_are_ordered(self, all_routes):
        """Test that waypoints are ordered by distance."""
        for name, route in all_routes:
            distances = [wp.distance_from_start_km for wp in route.waypoints]
            assert distances == sorted(distances), f"{name} waypoints not ordered"
            assert distances[0] == 0.0, f"{name} first waypoint should be at 0 km"

    def test_route_variety(self, all_routes):
        """Test that routes cover variety of distances."""
        distances = [route.total_distance_km for _, route in all_routes]

        # Should have at least one short route (< 50 km)
        assert any(d < 50 for d in distances), "No short routes"

        # Should have at least one medium route (50-150 km)
        assert any(50 <= d <= 150 for d in distances), "No medium routes"

        # Should have at least one long route (> 150 km)
        assert any(d > 150 for d in distances), "No long routes"

    def test_sample_pois_structure(
        self, pois_tel_aviv_jerusalem, pois_haifa_tel_aviv, pois_jerusalem_eilat
    ):
        """Test that sample POIs have valid structure."""
        all_poi_sets = [
            pois_tel_aviv_jerusalem,
            pois_haifa_tel_aviv,
            pois_jerusalem_eilat,
        ]

        for pois in all_poi_sets:
            assert isinstance(pois, list)
            assert len(pois) > 0

            for poi in pois:
                assert isinstance(poi, POI)
                assert poi.name
                assert poi.description
                assert poi.distance_from_start_km >= 0
                assert isinstance(poi.category, POICategory)

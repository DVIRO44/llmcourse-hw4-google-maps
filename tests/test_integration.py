"""Integration tests for queue-based pipeline."""

import pytest
import time
from unittest.mock import patch, MagicMock
from tour_guide.parallel.pipeline import ContentPipeline
from tour_guide.queue.manager import QueueManager
from tour_guide.models.poi import POI, POICategory
from tour_guide.models.judgment import JudgmentResult
from tour_guide.models.content import ContentResult
from tour_guide.orchestrator import TourGuideOrchestrator, JourneyResult
from tour_guide.routing.models import Route, Waypoint, RouteStep


class TestQueuePipeline:
    """Integration tests for ContentPipeline with queue communication."""

    @pytest.fixture
    def sample_pois(self):
        """Create sample POIs for testing."""
        return [
            POI(
                name="Latrun Monastery",
                lat=31.8356,
                lon=34.9869,
                description="Historic Trappist monastery with scenic views",
                category=POICategory.RELIGIOUS,
                distance_from_start_km=25.0,
            ),
            POI(
                name="Mini Israel",
                lat=31.8514,
                lon=34.9891,
                description="Miniature park with models of Israeli landmarks",
                category=POICategory.CULTURAL,
                distance_from_start_km=28.0,
            ),
            POI(
                name="Emmaus Nicopolis",
                lat=31.8402,
                lon=34.9875,
                description="Ancient Roman and Byzantine archaeological site",
                category=POICategory.HISTORICAL,
                distance_from_start_km=26.5,
            ),
        ]

    def test_pipeline_initialization(self):
        """Test that pipeline initializes with default components."""
        pipeline = ContentPipeline()

        assert pipeline.queue_manager is not None
        assert pipeline.parallel_executor is not None
        assert pipeline.judge_agent is not None

    def test_pipeline_with_custom_components(self):
        """Test pipeline with custom queue manager."""
        queue_manager = QueueManager(poi_queue_size=20)
        pipeline = ContentPipeline(queue_manager=queue_manager)

        assert pipeline.queue_manager.poi_queue_size == 20

    def test_pipeline_empty_pois(self):
        """Test pipeline with empty POI list."""
        pipeline = ContentPipeline()
        judgments = pipeline.run([])

        assert len(judgments) == 0

    def test_queue_pipeline_full_flow(self, sample_pois):
        """Test full pipeline with 3 sample POIs.

        This test verifies:
        - Parallel execution of content agents
        - Queue communication
        - Judge agent evaluation
        - All judgments returned
        """
        pipeline = ContentPipeline()

        # Measure execution time
        start_time = time.time()

        # Run pipeline
        judgments = pipeline.run(sample_pois)

        execution_time = time.time() - start_time

        # Verify results
        assert len(judgments) == 3, "Should have one judgment per POI"

        # All judgments should be JudgmentResult objects
        assert all(isinstance(j, JudgmentResult) for j in judgments)

        # Each judgment should have a selected type
        for judgment in judgments:
            assert judgment.selected_type in ["youtube", "spotify", "history"]
            assert judgment.poi_name in [poi.name for poi in sample_pois]
            assert judgment.selected_content is not None
            assert judgment.reasoning is not None and len(judgment.reasoning) > 0
            assert len(judgment.all_content) == 3  # Should have all 3 content options

        # Log execution time
        print(f"\nPipeline execution time: {execution_time:.2f}s")
        print(f"Average time per POI: {execution_time / len(sample_pois):.2f}s")

        # Verify parallel execution by checking it's not too slow
        # With 3 POIs and 3 agents per POI, if truly sequential it would take much longer
        # But agents run in parallel per POI, so should be reasonable
        # Allow generous timeout for CI environments
        assert execution_time < 180, f"Pipeline took {execution_time}s, expected < 180s"

    def test_pipeline_with_single_poi(self):
        """Test pipeline with a single POI."""
        pipeline = ContentPipeline()

        poi = POI(
            name="Test Single POI",
            lat=31.5,
            lon=35.5,
            description="Single POI test",
            category=POICategory.NATURAL,
            distance_from_start_km=10.0,
        )

        judgments = pipeline.run([poi])

        assert len(judgments) == 1
        assert judgments[0].poi_name == "Test Single POI"
        assert judgments[0].selected_type in ["youtube", "spotify", "history"]

    def test_pipeline_queue_communication(self, sample_pois):
        """Test that pipeline uses queues for communication."""
        queue_manager = QueueManager()
        pipeline = ContentPipeline(queue_manager=queue_manager)

        # Enqueue POIs manually
        for poi in sample_pois:
            queue_manager.put_poi(poi)

        # Run queue-only pipeline
        judgments = pipeline.run_with_queue_only(len(sample_pois))

        # Verify results
        assert len(judgments) == 3

        # Get stats to verify queue usage
        stats = pipeline.get_stats()
        assert "queue_stats" in stats
        assert "executor_timeout" in stats

    def test_pipeline_clear(self, sample_pois):
        """Test clearing pipeline queues."""
        pipeline = ContentPipeline()

        # Add some POIs to queue
        for poi in sample_pois:
            pipeline.queue_manager.put_poi(poi)

        # Clear pipeline
        pipeline.clear()

        # Verify queue is empty
        from queue import Empty

        with pytest.raises(Empty):
            pipeline.queue_manager.get_poi(block=False)

    def test_pipeline_handles_partial_failures(self):
        """Test that pipeline continues even if some agents fail."""
        pipeline = ContentPipeline()

        # Create POIs that might cause some agents to fail
        pois = [
            POI(
                name="Test POI 1",
                lat=31.5,
                lon=35.5,
                description="Test",
                category=POICategory.HISTORICAL,
                distance_from_start_km=10.0,
            ),
        ]

        judgments = pipeline.run(pois)

        # Should still get a judgment even if some agents failed
        assert len(judgments) == 1
        assert isinstance(judgments[0], JudgmentResult)

    def test_pipeline_stats(self, sample_pois):
        """Test getting pipeline statistics."""
        pipeline = ContentPipeline()

        # Run pipeline
        judgments = pipeline.run(sample_pois)

        # Get stats
        stats = pipeline.get_stats()

        assert "queue_stats" in stats
        assert "executor_timeout" in stats
        assert isinstance(stats["executor_timeout"], int)


class TestPipelinePerformance:
    """Performance tests for pipeline."""

    def test_parallel_vs_sequential_speedup(self):
        """Test that parallel execution provides speedup."""
        # Skip in CI
        import os

        if os.environ.get("CI"):
            pytest.skip("Skipping performance test in CI")

        # This is more of a sanity check than a precise benchmark
        pipeline = ContentPipeline()

        poi = POI(
            name="Performance Test POI",
            lat=31.5,
            lon=35.5,
            description="Performance test",
            category=POICategory.HISTORICAL,
            distance_from_start_km=10.0,
        )

        # Time one POI (3 agents in parallel)
        start = time.time()
        pipeline.run([poi])
        parallel_time = time.time() - start

        # With parallel execution, 3 agents should run concurrently
        # So time should be close to the time of the slowest agent, not 3x
        # This is a rough check - we just verify it completes in reasonable time
        assert parallel_time < 60, f"Single POI took {parallel_time}s, expected < 60s"


class TestOrchestrator:
    """Integration tests for TourGuideOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        return TourGuideOrchestrator()

    @pytest.fixture
    def mock_route(self):
        """Create a mock route."""
        return Route(
            origin=(32.0853, 34.7818),  # Tel Aviv
            destination=(31.7683, 35.2137),  # Jerusalem
            total_distance_km=65.0,
            total_duration_min=55.0,
            waypoints=[
                Waypoint(lat=32.0853, lon=34.7818, distance_from_start_km=0.0),
                Waypoint(lat=31.8356, lon=34.9869, distance_from_start_km=30.0),
                Waypoint(lat=31.7683, lon=35.2137, distance_from_start_km=65.0),
            ],
            steps=[
                RouteStep(instruction="Head east", distance_km=30.0, duration_min=25.0),
                RouteStep(instruction="Continue to Jerusalem", distance_km=35.0, duration_min=30.0),
            ],
            source="osrm",
        )

    @pytest.fixture
    def mock_pois(self):
        """Create mock POIs."""
        return [
            POI(
                name="Latrun Monastery",
                lat=31.8356,
                lon=34.9869,
                description="Historic Trappist monastery",
                category=POICategory.RELIGIOUS,
                distance_from_start_km=25.0,
            ),
            POI(
                name="Mini Israel",
                lat=31.8514,
                lon=34.9891,
                description="Miniature park",
                category=POICategory.CULTURAL,
                distance_from_start_km=28.0,
            ),
        ]

    @pytest.fixture
    def mock_judgments(self, mock_pois):
        """Create mock judgments."""
        judgments = []
        for poi in mock_pois:
            # Create content options
            youtube_content = ContentResult(
                content_type="youtube",
                title=f"Video about {poi.name}",
                description="Great video",
                relevance_score=90,
                metadata={"url": "https://youtube.com/test"},
                agent_name="youtube_agent",
                poi_name=poi.name,
            )
            spotify_content = ContentResult(
                content_type="spotify",
                title=f"Song about {poi.name}",
                description="Great song",
                relevance_score=80,
                metadata={"url": "https://spotify.com/test"},
                agent_name="spotify_agent",
                poi_name=poi.name,
            )
            history_content = ContentResult(
                content_type="history",
                title=f"History of {poi.name}",
                description="Historical info",
                relevance_score=70,
                agent_name="history_agent",
                poi_name=poi.name,
            )

            judgment = JudgmentResult(
                poi_name=poi.name,
                selected_type="youtube",
                selected_content=youtube_content,
                reasoning="Great video content",
                scores={"youtube": 90, "spotify": 80, "history": 70},
                all_content=[youtube_content, spotify_content, history_content],
            )
            judgments.append(judgment)
        return judgments

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes all components."""
        assert orchestrator.osrm_client is not None
        assert orchestrator.route_analyzer is not None
        assert orchestrator.content_pipeline is not None
        assert orchestrator.logger is not None

    def test_full_flow_tel_aviv_to_jerusalem(self, orchestrator, mock_route, mock_pois, mock_judgments):
        """Test complete flow from Tel Aviv to Jerusalem."""
        # Mock all the components
        with patch.object(orchestrator.osrm_client, "get_route", return_value=mock_route):
            with patch.object(orchestrator.route_analyzer, "run", return_value=mock_pois):
                with patch.object(orchestrator.content_pipeline, "run", return_value=mock_judgments):
                    # Run journey
                    result = orchestrator.run("Tel Aviv", "Jerusalem")

                    # Verify result structure
                    assert isinstance(result, JourneyResult)
                    assert result.route == mock_route
                    assert len(result.pois) == 2
                    assert len(result.judgments) == 2
                    assert result.execution_time > 0

                    # Verify stats
                    assert result.stats["total_pois"] == 2
                    assert result.stats["total_judgments"] == 2
                    assert result.stats["success_rate"] == 1.0
                    assert "content_distribution" in result.stats

    def test_run_with_no_pois(self, orchestrator, mock_route):
        """Test journey when no POIs are found."""
        with patch.object(orchestrator.osrm_client, "get_route", return_value=mock_route):
            with patch.object(orchestrator.route_analyzer, "run", return_value=[]):
                result = orchestrator.run("Tel Aviv", "Jerusalem")

                # Should still return valid result with empty data
                assert isinstance(result, JourneyResult)
                assert result.route == mock_route
                assert len(result.pois) == 0
                assert len(result.judgments) == 0
                assert result.stats["total_pois"] == 0
                assert result.stats["success_rate"] == 0.0

    def test_error_handling_route_failure(self, orchestrator):
        """Test error handling when route planning fails."""
        with patch.object(orchestrator.osrm_client, "get_route", side_effect=Exception("Route error")):
            with pytest.raises(Exception, match="Route error"):
                orchestrator.run("Tel Aviv", "Jerusalem")

    def test_error_handling_unknown_location(self, orchestrator):
        """Test error handling with unknown location."""
        # Should raise ValueError for unknown location (tries geocoding first)
        with pytest.raises(ValueError, match="Could not geocode"):
            orchestrator.run("Unknown City", "Jerusalem")

    def test_error_handling_poi_analysis_failure(self, orchestrator, mock_route):
        """Test graceful degradation when POI analysis fails."""
        with patch.object(orchestrator.osrm_client, "get_route", return_value=mock_route):
            with patch.object(orchestrator.route_analyzer, "run", side_effect=Exception("Analysis error")):
                result = orchestrator.run("Tel Aviv", "Jerusalem")

                # Should continue with empty POIs
                assert isinstance(result, JourneyResult)
                assert len(result.pois) == 0
                assert len(result.judgments) == 0

    def test_error_handling_content_pipeline_failure(self, orchestrator, mock_route, mock_pois):
        """Test graceful degradation when content pipeline fails."""
        with patch.object(orchestrator.osrm_client, "get_route", return_value=mock_route):
            with patch.object(orchestrator.route_analyzer, "run", return_value=mock_pois):
                with patch.object(orchestrator.content_pipeline, "run", side_effect=Exception("Pipeline error")):
                    result = orchestrator.run("Tel Aviv", "Jerusalem")

                    # Should continue with POIs but empty judgments
                    assert isinstance(result, JourneyResult)
                    assert len(result.pois) == 2
                    assert len(result.judgments) == 0

    def test_stats_calculation(self, orchestrator, mock_route, mock_pois):
        """Test statistics calculation."""
        youtube_content = ContentResult(
            content_type="youtube",
            title="Test video",
            description="Test",
            relevance_score=90,
        )
        spotify_content = ContentResult(
            content_type="spotify",
            title="Test song",
            description="Test",
            relevance_score=80,
        )

        judgments = [
            JudgmentResult(
                poi_name="POI 1",
                selected_type="youtube",
                selected_content=youtube_content,
                reasoning="test",
                scores={},
                all_content=[youtube_content],
            ),
            JudgmentResult(
                poi_name="POI 2",
                selected_type="spotify",
                selected_content=spotify_content,
                reasoning="test",
                scores={},
                all_content=[spotify_content],
            ),
        ]

        with patch.object(orchestrator.osrm_client, "get_route", return_value=mock_route):
            with patch.object(orchestrator.route_analyzer, "run", return_value=mock_pois):
                with patch.object(orchestrator.content_pipeline, "run", return_value=judgments):
                    result = orchestrator.run("Tel Aviv", "Jerusalem")

                    # Verify stats
                    assert result.stats["total_pois"] == 2
                    assert result.stats["total_judgments"] == 2
                    assert result.stats["success_rate"] == 1.0

                    # Verify content distribution
                    assert result.stats["content_distribution"]["youtube"] == 1
                    assert result.stats["content_distribution"]["spotify"] == 1

    def test_coordinates_map_coverage(self, orchestrator):
        """Test that all major Israeli cities are in the coordinates map."""
        # This tests the internal coordinates map indirectly
        cities = [
            ("Tel Aviv", "Jerusalem"),
            ("Haifa", "Eilat"),
            ("Beer Sheva", "Akko"),
            ("Jaffa", "Dead Sea"),
            ("Nazareth", "Tiberias"),
            ("Caesarea", "Masada"),
        ]

        for origin, destination in cities:
            with patch.object(orchestrator.route_analyzer, "run", return_value=[]):
                with patch.object(orchestrator.content_pipeline, "run", return_value=[]):
                    # Should not raise ValueError for these cities
                    result = orchestrator.run(origin, destination)
                    assert isinstance(result, JourneyResult)

    def test_journey_with_options(self, orchestrator, mock_route, mock_pois, mock_judgments):
        """Test journey with custom options."""
        options = {"max_pois": 5, "categories": ["religious", "historical"]}

        with patch.object(orchestrator.osrm_client, "get_route", return_value=mock_route):
            with patch.object(orchestrator.route_analyzer, "run", return_value=mock_pois):
                with patch.object(orchestrator.content_pipeline, "run", return_value=mock_judgments):
                    result = orchestrator.run("Tel Aviv", "Jerusalem", options=options)

                    # Options are passed through but not currently used
                    # This test just verifies they don't cause errors
                    assert isinstance(result, JourneyResult)

    def test_case_insensitive_location_names(self, orchestrator, mock_route):
        """Test that location names are case-insensitive."""
        with patch.object(orchestrator.route_analyzer, "run", return_value=[]):
            with patch.object(orchestrator.content_pipeline, "run", return_value=[]):
                # Should work with different cases
                result1 = orchestrator.run("tel aviv", "jerusalem")
                result2 = orchestrator.run("Tel Aviv", "Jerusalem")
                result3 = orchestrator.run("TEL AVIV", "JERUSALEM")

                assert all(isinstance(r, JourneyResult) for r in [result1, result2, result3])

    def test_long_route_with_waypoint_sampling(self, orchestrator):
        """Test that long routes with many waypoints use sampling."""
        # Create a long route with many waypoints (like Holon to Kiryat Shmona)
        waypoints = []
        num_waypoints = 2457  # Realistic number from actual route
        for i in range(num_waypoints):
            waypoints.append(
                Waypoint(
                    lat=32.0 + (i / num_waypoints),
                    lon=34.8 + (i / num_waypoints) * 0.5,
                    distance_from_start_km=(i / num_waypoints) * 200.0,
                )
            )

        long_route = Route(
            origin=(32.0117, 34.7750),  # Holon
            destination=(33.2074, 35.5697),  # Kiryat Shmona
            total_distance_km=200.0,
            total_duration_min=150.0,
            waypoints=waypoints,
            steps=[
                RouteStep(instruction="Head north on Route 4", distance_km=100.0, duration_min=75.0),
                RouteStep(instruction="Continue to Kiryat Shmona", distance_km=100.0, duration_min=75.0),
            ],
            source="osrm",
        )

        # Mock the route analyzer to capture the route it receives
        with patch.object(orchestrator.route_analyzer, "run", return_value=[]) as mock_analyzer:
            with patch.object(orchestrator.content_pipeline, "run", return_value=[]):
                with patch.object(orchestrator.osrm_client, "get_route", return_value=long_route):
                    result = orchestrator.run("holon", "kiryat shmona")

                    # Verify orchestrator completed successfully
                    assert isinstance(result, JourneyResult)

                    # Verify route analyzer was called with the long route
                    assert mock_analyzer.called
                    route_arg = mock_analyzer.call_args[0][0]
                    assert isinstance(route_arg, Route)
                    assert len(route_arg.waypoints) == num_waypoints

                    # The route should have a method to sample waypoints
                    sampled = route_arg.get_sampled_waypoints(max_points=30)
                    assert len(sampled) == 30
                    assert sampled[0] == route_arg.waypoints[0]  # Start
                    assert sampled[-1] == route_arg.waypoints[-1]  # End

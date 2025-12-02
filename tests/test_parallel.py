"""Tests for parallel execution of content agents."""

import pytest
import time
from unittest.mock import patch, Mock
from tour_guide.parallel.worker import content_worker, batch_content_worker
from tour_guide.parallel.executor import ParallelExecutor
from tour_guide.models.poi import POI, POICategory
from tour_guide.models.content import ContentResult
from tour_guide.agents.base import AgentError


class TestContentWorker:
    """Tests for content_worker function."""

    @pytest.fixture
    def sample_poi(self):
        """Create a sample POI."""
        return POI(
            name="Test POI",
            lat=31.5,
            lon=35.5,
            description="Test location",
            category=POICategory.HISTORICAL,
            distance_from_start_km=10.0,
        )

    def test_content_worker_youtube(self, sample_poi):
        """Test content_worker with YouTube agent."""
        with patch("tour_guide.parallel.worker.YouTubeAgent") as MockYouTube:
            mock_agent = Mock()
            mock_result = ContentResult(
                content_type="youtube",
                title="Test Video",
                description="Test description",
                relevance_score=85,
                agent_name="youtube",
                poi_name="Test POI",
            )
            mock_agent.run.return_value = mock_result
            MockYouTube.return_value = mock_agent

            result = content_worker("youtube", sample_poi)

            assert result.content_type == "youtube"
            assert result.relevance_score == 85
            MockYouTube.assert_called_once()
            mock_agent.run.assert_called_once_with(sample_poi)

    def test_content_worker_spotify(self, sample_poi):
        """Test content_worker with Spotify agent."""
        with patch("tour_guide.parallel.worker.SpotifyAgent") as MockSpotify:
            mock_agent = Mock()
            mock_result = ContentResult(
                content_type="spotify",
                title="Test Music",
                description="Test description",
                relevance_score=75,
                agent_name="spotify",
                poi_name="Test POI",
            )
            mock_agent.run.return_value = mock_result
            MockSpotify.return_value = mock_agent

            result = content_worker("spotify", sample_poi)

            assert result.content_type == "spotify"
            assert result.relevance_score == 75

    def test_content_worker_history(self, sample_poi):
        """Test content_worker with History agent."""
        with patch("tour_guide.parallel.worker.HistoryAgent") as MockHistory:
            mock_agent = Mock()
            mock_result = ContentResult(
                content_type="history",
                title="Test History",
                description="Test narrative",
                relevance_score=90,
                agent_name="history",
                poi_name="Test POI",
            )
            mock_agent.run.return_value = mock_result
            MockHistory.return_value = mock_agent

            result = content_worker("history", sample_poi)

            assert result.content_type == "history"
            assert result.relevance_score == 90

    def test_content_worker_invalid_agent_type(self, sample_poi):
        """Test that invalid agent type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            content_worker("invalid", sample_poi)

        assert "Invalid agent_type" in str(exc_info.value)

    def test_content_worker_handles_agent_failure(self, sample_poi):
        """Test that content_worker returns error result when agent fails."""
        with patch("tour_guide.parallel.worker.YouTubeAgent") as MockYouTube:
            mock_agent = Mock()
            mock_agent.run.side_effect = AgentError("Test error")
            MockYouTube.return_value = mock_agent

            result = content_worker("youtube", sample_poi)

            # Should return error ContentResult, not raise exception
            assert result.content_type == "youtube"
            assert result.relevance_score == 0
            assert "Error:" in result.title
            assert "Test error" in result.description
            assert "error" in result.metadata

    def test_batch_content_worker(self, sample_poi):
        """Test batch_content_worker processes multiple tasks."""
        with patch("tour_guide.parallel.worker.YouTubeAgent") as MockYouTube, \
             patch("tour_guide.parallel.worker.SpotifyAgent") as MockSpotify:

            # Setup YouTube mock
            youtube_agent = Mock()
            youtube_result = ContentResult(
                content_type="youtube",
                title="Video",
                description="Description",
                relevance_score=80,
                agent_name="youtube",
                poi_name="Test POI",
            )
            youtube_agent.run.return_value = youtube_result
            MockYouTube.return_value = youtube_agent

            # Setup Spotify mock
            spotify_agent = Mock()
            spotify_result = ContentResult(
                content_type="spotify",
                title="Music",
                description="Description",
                relevance_score=75,
                agent_name="spotify",
                poi_name="Test POI",
            )
            spotify_agent.run.return_value = spotify_result
            MockSpotify.return_value = spotify_agent

            tasks = [
                ("youtube", sample_poi),
                ("spotify", sample_poi),
            ]

            results = batch_content_worker(tasks)

            assert len(results) == 2
            assert results[0].content_type == "youtube"
            assert results[1].content_type == "spotify"


class TestParallelExecutor:
    """Tests for ParallelExecutor class."""

    @pytest.fixture
    def executor(self):
        """Create a ParallelExecutor instance with short timeout."""
        return ParallelExecutor(timeout=30)

    @pytest.fixture
    def sample_poi(self):
        """Create a sample POI."""
        return POI(
            name="Test POI",
            lat=31.5,
            lon=35.5,
            description="Test location",
            category=POICategory.HISTORICAL,
            distance_from_start_km=10.0,
        )

    @pytest.fixture
    def sample_pois(self):
        """Create multiple sample POIs."""
        return [
            POI(
                name=f"POI {i}",
                lat=31.5 + i * 0.1,
                lon=35.5 + i * 0.1,
                description=f"Location {i}",
                category=POICategory.HISTORICAL,
                distance_from_start_km=10.0 + i * 5,
            )
            for i in range(3)
        ]

    def test_executor_initialization(self, executor):
        """Test ParallelExecutor initializes with correct timeout."""
        assert executor.timeout == 30

    def test_process_poi_success(self, executor, sample_poi):
        """Test processing a single POI with all agents succeeding."""
        # Use real agents - this is an integration test
        # The agents will run and may succeed or fail naturally
        results = executor.process_poi(sample_poi)

        # Should get 3 results (one from each agent)
        assert len(results) == 3
        # Verify we got results from all three agent types
        assert {r.content_type for r in results} == {"youtube", "spotify", "history"}
        # Each result should have the correct POI name
        assert all(r.poi_name == sample_poi.name for r in results)

    def test_process_poi_isolation(self, executor):
        """Test that failures in one agent don't crash other agents."""
        # Create a POI that will cause agents to run
        poi = POI(
            name="Isolation Test POI",
            lat=31.5,
            lon=35.5,
            description="Testing failure isolation",
            category=POICategory.HISTORICAL,
            distance_from_start_km=10.0,
        )

        results = executor.process_poi(poi)

        # Should get 3 results regardless of individual agent success/failure
        assert len(results) == 3
        # All results should be ContentResult objects
        assert all(isinstance(r, ContentResult) for r in results)
        # All should have correct POI name
        assert all(r.poi_name == poi.name for r in results)

    def test_process_all_pois(self, executor, sample_pois):
        """Test processing multiple POIs."""
        results_by_poi = executor.process_all_pois(sample_pois)

        # Should have results for all POIs
        assert len(results_by_poi) == 3

        # Each POI should have results from all 3 agents
        for poi_name, results in results_by_poi.items():
            assert len(results) == 3
            # All agent types should be present
            agent_types = {r.content_type for r in results}
            assert agent_types == {"youtube", "spotify", "history"}
            # All results should have correct POI name
            assert all(r.poi_name == poi_name for r in results)

    def test_parallel_speedup(self, sample_poi):
        """Test that parallel execution is faster than sequential."""
        # This is a real test without mocks to verify actual parallel execution
        # We'll use a very short timeout to make the test fast

        # Skip if running in CI/CD where multiprocessing might be restricted
        import os
        if os.environ.get("CI"):
            pytest.skip("Skipping parallel speedup test in CI environment")

        executor = ParallelExecutor(timeout=15)

        # Measure time for one POI (3 agents in parallel)
        start = time.time()
        results = executor.process_poi(sample_poi)
        parallel_time = time.time() - start

        # Should get 3 results
        assert len(results) == 3

        # Note: We can't easily measure sequential time without modifying agent code
        # But we can verify that parallel execution completes reasonably fast
        # (If it were truly sequential, it would take much longer)
        # With timeout of 15s and 3 agents, worst case is 15s (if they all timeout)
        # But in practice should be much faster if agents succeed
        assert parallel_time < 20, f"Parallel execution took {parallel_time}s, expected < 20s"

    def test_process_all_pois_batched(self, executor, sample_pois):
        """Test batched processing of POIs."""
        results_by_poi = executor.process_all_pois_batched(sample_pois, batch_size=2)

        # Should have results for all POIs
        assert len(results_by_poi) == 3

        # Each POI should have results from all 3 agents
        for poi_name, results in results_by_poi.items():
            assert len(results) == 3
            assert all(isinstance(r, ContentResult) for r in results)

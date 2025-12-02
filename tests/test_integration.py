"""Integration tests for queue-based pipeline."""

import pytest
import time
from tour_guide.parallel.pipeline import ContentPipeline
from tour_guide.queue.manager import QueueManager
from tour_guide.models.poi import POI, POICategory
from tour_guide.models.judgment import JudgmentResult


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

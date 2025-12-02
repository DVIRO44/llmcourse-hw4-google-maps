"""Tests for queue management."""

import pytest
import multiprocessing as mp
from queue import Empty, Full
import time

from tour_guide.queue.manager import QueueManager
from tour_guide.models.poi import POI, POICategory
from tour_guide.models.content import ContentResult
from tour_guide.models.judgment import JudgmentResult


class TestQueueManager:
    """Tests for QueueManager class."""

    @pytest.fixture
    def queue_manager(self):
        """Create a QueueManager instance."""
        return QueueManager(poi_queue_size=5, results_queue_size=10, judgment_queue_size=5)

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
    def sample_result(self):
        """Create a sample ContentResult."""
        return ContentResult(
            content_type="youtube",
            title="Test Video",
            description="Test description",
            relevance_score=85,
            agent_name="youtube",
            poi_name="Test POI",
        )

    @pytest.fixture
    def sample_judgment(self, sample_result):
        """Create a sample JudgmentResult."""
        return JudgmentResult(
            poi_name="Test POI",
            selected_content=sample_result,
            selected_type="youtube",
            reasoning="Test reasoning",
            scores={"youtube": 85},
            all_content=[sample_result],
        )

    def test_queue_manager_initialization(self, queue_manager):
        """Test QueueManager initializes with correct queue sizes."""
        assert queue_manager.poi_queue_size == 5
        assert queue_manager.results_queue_size == 10
        assert queue_manager.judgment_queue_size == 5

    def test_put_and_get_poi(self, queue_manager, sample_poi):
        """Test putting and getting POI from queue."""
        queue_manager.put_poi(sample_poi)
        retrieved_poi = queue_manager.get_poi()

        assert retrieved_poi.name == sample_poi.name
        assert retrieved_poi.lat == sample_poi.lat
        assert retrieved_poi.lon == sample_poi.lon

    def test_put_and_get_result(self, queue_manager, sample_result):
        """Test putting and getting ContentResult from queue."""
        queue_manager.put_result(sample_result)
        retrieved_result = queue_manager.get_result()

        assert retrieved_result.content_type == sample_result.content_type
        assert retrieved_result.title == sample_result.title
        assert retrieved_result.relevance_score == sample_result.relevance_score

    def test_put_and_get_judgment(self, queue_manager, sample_judgment):
        """Test putting and getting JudgmentResult from queue."""
        queue_manager.put_judgment(sample_judgment)
        retrieved_judgment = queue_manager.get_judgment()

        assert retrieved_judgment.poi_name == sample_judgment.poi_name
        assert retrieved_judgment.selected_type == sample_judgment.selected_type
        assert retrieved_judgment.reasoning == sample_judgment.reasoning

    def test_bounded_poi_queue_blocks(self, queue_manager, sample_poi):
        """Test that poi_queue blocks when full."""
        # Fill the queue to capacity (size=5)
        for i in range(5):
            poi = POI(
                name=f"POI {i}",
                lat=31.5 + i,
                lon=35.5 + i,
                description=f"POI {i}",
                category=POICategory.HISTORICAL,
                distance_from_start_km=10.0 + i,
            )
            queue_manager.put_poi(poi)

        # Queue should be full now, non-blocking put should raise Full
        with pytest.raises(Full):
            queue_manager.put_poi(sample_poi, block=False)

    def test_empty_poi_queue_blocks(self, queue_manager):
        """Test that get_poi blocks when queue is empty."""
        # Queue is empty, non-blocking get should raise Empty
        with pytest.raises(Empty):
            queue_manager.get_poi(block=False)

    def test_put_with_timeout(self, queue_manager, sample_poi):
        """Test put operation with timeout."""
        # Fill the queue
        for i in range(5):
            poi = POI(
                name=f"POI {i}",
                lat=31.5 + i,
                lon=35.5 + i,
                description=f"POI {i}",
                category=POICategory.HISTORICAL,
                distance_from_start_km=10.0 + i,
            )
            queue_manager.put_poi(poi)

        # Try to put with short timeout, should raise Full
        with pytest.raises(Full):
            queue_manager.put_poi(sample_poi, block=True, timeout=0.1)

    def test_get_with_timeout(self, queue_manager):
        """Test get operation with timeout."""
        # Queue is empty, get with timeout should raise Empty
        with pytest.raises(Empty):
            queue_manager.get_poi(block=True, timeout=0.1)

    def test_clear_all_empty_queues(self, queue_manager):
        """Test clearing empty queues."""
        queue_manager.clear_all()
        # Should not raise any errors

    def test_clear_all_with_data(self, queue_manager, sample_poi, sample_result, sample_judgment):
        """Test clearing queues with data."""
        # Add items to all queues
        queue_manager.put_poi(sample_poi)
        queue_manager.put_result(sample_result)
        queue_manager.put_judgment(sample_judgment)

        # Clear all queues
        queue_manager.clear_all()

        # Queues should be empty now
        with pytest.raises(Empty):
            queue_manager.get_poi(block=False)

        with pytest.raises(Empty):
            queue_manager.get_result(block=False)

        with pytest.raises(Empty):
            queue_manager.get_judgment(block=False)

    def test_get_stats(self, queue_manager):
        """Test getting queue statistics."""
        stats = queue_manager.get_stats()

        assert "poi_queue" in stats
        assert "results_queue" in stats
        assert "judgment_queue" in stats

        # Stats should be integers (could be -1 if not supported on platform)
        assert isinstance(stats["poi_queue"], int)
        assert isinstance(stats["results_queue"], int)
        assert isinstance(stats["judgment_queue"], int)

    def test_repr(self, queue_manager):
        """Test string representation of QueueManager."""
        repr_str = repr(queue_manager)
        assert "QueueManager" in repr_str
        assert "poi=" in repr_str
        assert "results=" in repr_str
        assert "judgment=" in repr_str


def worker_put_poi(queue_manager, poi):
    """Worker function that puts POI into queue from another process."""
    try:
        queue_manager.put_poi(poi)
        return True
    except Exception as e:
        return False


def worker_get_poi(queue_manager):
    """Worker function that gets POI from queue in another process."""
    try:
        poi = queue_manager.get_poi(timeout=2)
        return poi
    except Exception as e:
        return None


class TestCrossProcessCommunication:
    """Tests for cross-process queue communication."""

    def test_cross_process_put_and_get(self):
        """Test that queues work across processes."""
        queue_manager = QueueManager(poi_queue_size=5)

        # Create test POI
        test_poi = POI(
            name="Cross Process POI",
            lat=32.0,
            lon=35.0,
            description="Test cross-process",
            category=POICategory.NATURAL,
            distance_from_start_km=15.0,
        )

        # Put POI in main process
        queue_manager.put_poi(test_poi)

        # Get POI from child process
        ctx = mp.get_context("spawn")
        process = ctx.Process(target=worker_get_poi, args=(queue_manager,))
        process.start()
        process.join(timeout=3)

        # Process should complete successfully
        assert process.exitcode == 0

    def test_multiple_processes_put(self):
        """Test multiple processes putting items into queue."""
        queue_manager = QueueManager(poi_queue_size=10)

        # Create POIs for each process
        pois = [
            POI(
                name=f"POI {i}",
                lat=31.0 + i,
                lon=35.0 + i,
                description=f"POI {i}",
                category=POICategory.HISTORICAL,
                distance_from_start_km=10.0 * i,
            )
            for i in range(3)
        ]

        # Spawn processes to put POIs
        ctx = mp.get_context("spawn")
        processes = []
        for poi in pois:
            p = ctx.Process(target=worker_put_poi, args=(queue_manager, poi))
            p.start()
            processes.append(p)

        # Wait for all processes to complete
        for p in processes:
            p.join(timeout=3)

        # All processes should complete successfully
        for p in processes:
            assert p.exitcode == 0

        # Should be able to get 3 POIs from queue
        retrieved_pois = []
        for _ in range(3):
            poi = queue_manager.get_poi(timeout=1)
            retrieved_pois.append(poi)

        assert len(retrieved_pois) == 3
        # POI names should match (order may vary)
        retrieved_names = {poi.name for poi in retrieved_pois}
        expected_names = {f"POI {i}" for i in range(3)}
        assert retrieved_names == expected_names

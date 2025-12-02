"""Queue manager for inter-agent communication using multiprocessing."""

import logging
from multiprocessing import Queue
from typing import Dict, Optional
from tour_guide.models.poi import POI
from tour_guide.models.content import ContentResult
from tour_guide.models.judgment import JudgmentResult

logger = logging.getLogger(__name__)


class QueueManager:
    """
    Manages multiple queues for inter-agent communication.

    Uses multiprocessing.Queue for cross-process communication with bounded sizes
    to prevent memory issues.

    Queue types:
    - poi_queue: POIs waiting to be processed by content agents
    - results_queue: Content results from agents (YouTube, Spotify, History)
    - judgment_queue: Final judgments from Judge agent
    """

    def __init__(
        self,
        poi_queue_size: int = 10,
        results_queue_size: int = 30,
        judgment_queue_size: int = 10,
    ):
        """
        Initialize queue manager with bounded queues.

        Args:
            poi_queue_size: Max POIs in queue (default 10)
            results_queue_size: Max content results in queue (default 30, 3 per POI)
            judgment_queue_size: Max judgments in queue (default 10)
        """
        self.poi_queue: Queue = Queue(maxsize=poi_queue_size)
        self.results_queue: Queue = Queue(maxsize=results_queue_size)
        self.judgment_queue: Queue = Queue(maxsize=judgment_queue_size)

        self.poi_queue_size = poi_queue_size
        self.results_queue_size = results_queue_size
        self.judgment_queue_size = judgment_queue_size

        logger.info(
            f"QueueManager initialized with sizes: poi={poi_queue_size}, "
            f"results={results_queue_size}, judgment={judgment_queue_size}"
        )

    def put_poi(self, poi: POI, block: bool = True, timeout: Optional[float] = None) -> None:
        """
        Put a POI into the poi_queue.

        Args:
            poi: POI object to enqueue
            block: Whether to block if queue is full (default True)
            timeout: Timeout in seconds for blocking put (None = wait forever)

        Raises:
            queue.Full: If queue is full and block=False or timeout expires
        """
        self.poi_queue.put(poi, block=block, timeout=timeout)
        logger.debug(f"POI enqueued: {poi.name}")

    def get_poi(self, block: bool = True, timeout: Optional[float] = None) -> POI:
        """
        Get a POI from the poi_queue.

        Args:
            block: Whether to block if queue is empty (default True)
            timeout: Timeout in seconds for blocking get (None = wait forever)

        Returns:
            POI object

        Raises:
            queue.Empty: If queue is empty and block=False or timeout expires
        """
        poi = self.poi_queue.get(block=block, timeout=timeout)
        logger.debug(f"POI dequeued: {poi.name}")
        return poi

    def put_result(
        self, result: ContentResult, block: bool = True, timeout: Optional[float] = None
    ) -> None:
        """
        Put a ContentResult into the results_queue.

        Args:
            result: ContentResult object to enqueue
            block: Whether to block if queue is full (default True)
            timeout: Timeout in seconds for blocking put (None = wait forever)

        Raises:
            queue.Full: If queue is full and block=False or timeout expires
        """
        self.results_queue.put(result, block=block, timeout=timeout)
        logger.debug(f"Result enqueued: {result.content_type} for {result.poi_name}")

    def get_result(self, block: bool = True, timeout: Optional[float] = None) -> ContentResult:
        """
        Get a ContentResult from the results_queue.

        Args:
            block: Whether to block if queue is empty (default True)
            timeout: Timeout in seconds for blocking get (None = wait forever)

        Returns:
            ContentResult object

        Raises:
            queue.Empty: If queue is empty and block=False or timeout expires
        """
        result = self.results_queue.get(block=block, timeout=timeout)
        logger.debug(f"Result dequeued: {result.content_type} for {result.poi_name}")
        return result

    def put_judgment(
        self, judgment: JudgmentResult, block: bool = True, timeout: Optional[float] = None
    ) -> None:
        """
        Put a JudgmentResult into the judgment_queue.

        Args:
            judgment: JudgmentResult object to enqueue
            block: Whether to block if queue is full (default True)
            timeout: Timeout in seconds for blocking put (None = wait forever)

        Raises:
            queue.Full: If queue is full and block=False or timeout expires
        """
        self.judgment_queue.put(judgment, block=block, timeout=timeout)
        logger.debug(f"Judgment enqueued: {judgment.selected_type} for {judgment.poi_name}")

    def get_judgment(
        self, block: bool = True, timeout: Optional[float] = None
    ) -> JudgmentResult:
        """
        Get a JudgmentResult from the judgment_queue.

        Args:
            block: Whether to block if queue is empty (default True)
            timeout: Timeout in seconds for blocking get (None = wait forever)

        Returns:
            JudgmentResult object

        Raises:
            queue.Empty: If queue is empty and block=False or timeout expires
        """
        judgment = self.judgment_queue.get(block=block, timeout=timeout)
        logger.debug(f"Judgment dequeued: {judgment.selected_type} for {judgment.poi_name}")
        return judgment

    def clear_all(self) -> None:
        """
        Drain all queues by removing all items.

        Note: This should only be called when no processes are actively using the queues
        to avoid race conditions.
        """
        # Clear POI queue
        cleared_pois = 0
        while not self.poi_queue.empty():
            try:
                self.poi_queue.get_nowait()
                cleared_pois += 1
            except:
                break

        # Clear results queue
        cleared_results = 0
        while not self.results_queue.empty():
            try:
                self.results_queue.get_nowait()
                cleared_results += 1
            except:
                break

        # Clear judgment queue
        cleared_judgments = 0
        while not self.judgment_queue.empty():
            try:
                self.judgment_queue.get_nowait()
                cleared_judgments += 1
            except:
                break

        logger.info(
            f"Queues cleared: {cleared_pois} POIs, {cleared_results} results, "
            f"{cleared_judgments} judgments"
        )

    def get_stats(self) -> Dict[str, int]:
        """
        Get approximate queue sizes.

        Returns:
            Dictionary with queue names and their approximate sizes

        Note: Queue.qsize() is approximate and may not be reliable on all platforms.
        """
        try:
            stats = {
                "poi_queue": self.poi_queue.qsize(),
                "results_queue": self.results_queue.qsize(),
                "judgment_queue": self.judgment_queue.qsize(),
            }
        except NotImplementedError:
            # qsize() not implemented on macOS for multiprocessing.Queue
            logger.warning("Queue.qsize() not available on this platform")
            stats = {
                "poi_queue": -1,  # Unknown
                "results_queue": -1,
                "judgment_queue": -1,
            }

        return stats

    def __repr__(self) -> str:
        """String representation of QueueManager."""
        stats = self.get_stats()
        return (
            f"QueueManager(poi={stats['poi_queue']}/{self.poi_queue_size}, "
            f"results={stats['results_queue']}/{self.results_queue_size}, "
            f"judgment={stats['judgment_queue']}/{self.judgment_queue_size})"
        )

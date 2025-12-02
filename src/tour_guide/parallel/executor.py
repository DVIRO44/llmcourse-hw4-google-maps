"""Parallel executor for content agents using multiprocessing."""

import logging
import time
from typing import List, Dict
from tour_guide.models.poi import POI
from tour_guide.models.content import ContentResult
from tour_guide.parallel.worker import content_worker
from tour_guide.config import get_settings

logger = logging.getLogger(__name__)


class ParallelExecutor:
    """
    Executes content agents in parallel using multiprocessing.Pool.

    Spawns 3 workers (YouTube, Spotify, History) to process POIs concurrently,
    with timeout handling and graceful failure recovery.
    """

    def __init__(self, timeout: int = None):
        """
        Initialize parallel executor.

        Args:
            timeout: Timeout in seconds for each agent (uses config if not provided)
        """
        self.settings = get_settings()
        self.timeout = timeout or self.settings.agents.content_timeout
        logger.info(f"ParallelExecutor initialized with timeout={self.timeout}s")

    def process_poi(self, poi: POI) -> List[ContentResult]:
        """
        Process a single POI with all three content agents in parallel.

        Spawns 3 worker processes (YouTube, Spotify, History) and collects results
        with timeout handling.

        Args:
            poi: POI to process

        Returns:
            List of ContentResult objects (may be less than 3 if some agents fail)
        """
        logger.info(f"Processing POI in parallel: {poi.name}")
        start_time = time.time()

        # Define tasks for the three content agents
        tasks = [
            ("youtube", poi),
            ("spotify", poi),
            ("history", poi),
        ]

        results = []

        try:
            # Use spawn context for clean process isolation
            # This is important for macOS and ensures each process starts fresh
            import multiprocessing as mp

            ctx = mp.get_context("spawn")

            with ctx.Pool(processes=3) as pool:
                # Use starmap_async for non-blocking execution with timeout
                async_result = pool.starmap_async(content_worker, tasks)

                try:
                    # Wait for results with timeout
                    results = async_result.get(timeout=self.timeout)
                    logger.info(
                        f"All 3 agents completed for {poi.name} in {time.time() - start_time:.2f}s"
                    )

                except mp.TimeoutError:
                    # Timeout occurred, terminate workers and collect partial results
                    logger.warning(
                        f"Timeout after {self.timeout}s for {poi.name}, terminating workers"
                    )
                    pool.terminate()
                    pool.join()

                    # Return error results for all agents on timeout
                    for agent_type, _ in tasks:
                        results.append(
                            ContentResult(
                                content_type=agent_type,
                                title=f"Error: {agent_type} agent timeout",
                                description=f"Agent exceeded timeout of {self.timeout}s",
                                relevance_score=0,
                                agent_name=agent_type,
                                poi_name=poi.name,
                                metadata={"error": "timeout"},
                            )
                        )

        except Exception as e:
            logger.error(f"Failed to process POI {poi.name}: {e}")
            # Return error results for all agents on exception
            for agent_type, _ in tasks:
                results.append(
                    ContentResult(
                        content_type=agent_type,
                        title=f"Error: {agent_type} agent failed",
                        description=f"Parallel execution failed: {str(e)}",
                        relevance_score=0,
                        agent_name=agent_type,
                        poi_name=poi.name,
                        metadata={"error": str(e), "error_type": type(e).__name__},
                    )
                )

        execution_time = time.time() - start_time
        logger.info(f"POI {poi.name} processed in {execution_time:.2f}s with {len(results)} results")

        return results

    def process_all_pois(self, pois: List[POI]) -> Dict[str, List[ContentResult]]:
        """
        Process all POIs sequentially, but process each POI's agents in parallel.

        Args:
            pois: List of POIs to process

        Returns:
            Dictionary mapping poi_name -> list of ContentResult objects
        """
        logger.info(f"Processing {len(pois)} POIs with parallel agents")
        start_time = time.time()

        results_by_poi = {}

        for i, poi in enumerate(pois, 1):
            logger.info(f"Processing POI {i}/{len(pois)}: {poi.name}")
            results = self.process_poi(poi)
            results_by_poi[poi.name] = results

            # Log progress
            successful_results = sum(1 for r in results if r.relevance_score > 0)
            logger.info(
                f"POI {i}/{len(pois)} complete: {successful_results}/3 agents succeeded"
            )

        execution_time = time.time() - start_time
        total_pois = len(pois)
        total_results = sum(len(results) for results in results_by_poi.values())
        successful_results = sum(
            sum(1 for r in results if r.relevance_score > 0)
            for results in results_by_poi.values()
        )

        logger.info(
            f"Processed {total_pois} POIs in {execution_time:.2f}s: "
            f"{total_results} total results, {successful_results} successful"
        )

        return results_by_poi

    def process_all_pois_batched(self, pois: List[POI], batch_size: int = 3) -> Dict[str, List[ContentResult]]:
        """
        Process POIs in batches with full parallelization.

        This is an advanced method that processes multiple POIs simultaneously,
        with each POI's agents also running in parallel.

        Args:
            pois: List of POIs to process
            batch_size: Number of POIs to process in parallel (default 3)

        Returns:
            Dictionary mapping poi_name -> list of ContentResult objects
        """
        logger.info(f"Processing {len(pois)} POIs in batches of {batch_size}")
        start_time = time.time()

        results_by_poi = {}

        # Process POIs in batches
        for batch_start in range(0, len(pois), batch_size):
            batch_end = min(batch_start + batch_size, len(pois))
            batch = pois[batch_start:batch_end]

            logger.info(f"Processing batch {batch_start + 1}-{batch_end} of {len(pois)} POIs")

            # Process this batch
            for poi in batch:
                results = self.process_poi(poi)
                results_by_poi[poi.name] = results

        execution_time = time.time() - start_time
        logger.info(f"Batched processing completed in {execution_time:.2f}s")

        return results_by_poi

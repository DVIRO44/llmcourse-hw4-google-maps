"""Content pipeline orchestrating queue-based parallel processing."""

import logging
from typing import List, Dict
from tour_guide.models.poi import POI
from tour_guide.models.judgment import JudgmentResult
from tour_guide.queue.manager import QueueManager
from tour_guide.parallel.executor import ParallelExecutor
from tour_guide.agents.judge import JudgeAgent

logger = logging.getLogger(__name__)


class ContentPipeline:
    """
    Orchestrates the full content generation and judgment flow.

    Pipeline steps:
    1. Receive POIs from RouteAnalyzer
    2. Put POIs in poi_queue
    3. ParallelExecutor processes POIs (3 content agents in parallel per POI)
    4. Results go to results_queue
    5. JudgeAgent evaluates each POI's results
    6. Judgments go to judgment_queue
    7. Return final list of JudgmentResults
    """

    def __init__(
        self,
        queue_manager: QueueManager = None,
        parallel_executor: ParallelExecutor = None,
        judge_agent: JudgeAgent = None,
    ):
        """
        Initialize content pipeline.

        Args:
            queue_manager: Queue manager for inter-agent communication (creates new if None)
            parallel_executor: Parallel executor for content agents (creates new if None)
            judge_agent: Judge agent for evaluating content (creates new if None)
        """
        self.queue_manager = queue_manager or QueueManager()
        self.parallel_executor = parallel_executor or ParallelExecutor()
        self.judge_agent = judge_agent or JudgeAgent()

        logger.info("ContentPipeline initialized")

    def run(self, pois: List[POI]) -> List[JudgmentResult]:
        """
        Run the full content pipeline for a list of POIs.

        This is the main orchestration method that:
        1. Enqueues POIs
        2. Processes them with parallel content agents
        3. Evaluates results with Judge agent
        4. Returns final judgments

        Args:
            pois: List of POI objects to process

        Returns:
            List of JudgmentResult objects, one per POI
        """
        logger.info(f"Starting pipeline for {len(pois)} POIs")

        if not pois:
            logger.warning("No POIs provided to pipeline")
            return []

        # Step 1: Put POIs in queue
        logger.info("Step 1: Enqueuing POIs")
        for poi in pois:
            self.queue_manager.put_poi(poi)
        logger.info(f"Enqueued {len(pois)} POIs")

        # Step 2 & 3: Process POIs with parallel executor
        logger.info("Step 2-3: Processing POIs with parallel content agents")
        results_by_poi = self.parallel_executor.process_all_pois(pois)

        # Step 4: Put results in results queue
        logger.info("Step 4: Enqueuing content results")
        total_results = 0
        for poi_name, results in results_by_poi.items():
            for result in results:
                self.queue_manager.put_result(result)
                total_results += 1
        logger.info(f"Enqueued {total_results} content results")

        # Step 5: Judge agent evaluates each POI's results
        logger.info("Step 5: Judging content for each POI")
        judgments = []
        for poi_name, results in results_by_poi.items():
            try:
                judgment = self.judge_agent.run(results)
                judgments.append(judgment)
                logger.info(f"Judged {poi_name}: selected {judgment.selected_type}")
            except Exception as e:
                logger.error(f"Failed to judge {poi_name}: {e}")
                # Create fallback judgment with first result
                if results:
                    fallback_judgment = JudgmentResult(
                        poi_name=poi_name,
                        selected_content=results[0],
                        selected_type=results[0].content_type,
                        reasoning=f"Judge agent failed, using fallback: {str(e)}",
                        scores={r.content_type: r.relevance_score for r in results},
                        all_content=results,
                    )
                    judgments.append(fallback_judgment)

        # Step 6: Put judgments in judgment queue
        logger.info("Step 6: Enqueuing judgments")
        for judgment in judgments:
            self.queue_manager.put_judgment(judgment)
        logger.info(f"Enqueued {len(judgments)} judgments")

        # Step 7: Return judgments
        logger.info(f"Pipeline complete: {len(judgments)} judgments generated")
        return judgments

    def run_with_queue_only(self, poi_count: int) -> List[JudgmentResult]:
        """
        Run pipeline using only queues for communication (no direct method calls).

        This is a more pure queue-based implementation where:
        - POIs are consumed from poi_queue
        - Results are consumed from results_queue
        - Judgments are returned from judgment_queue

        Args:
            poi_count: Number of POIs to process from queue

        Returns:
            List of JudgmentResult objects
        """
        logger.info(f"Starting queue-only pipeline for {poi_count} POIs")

        judgments = []

        # Process each POI from the queue
        for i in range(poi_count):
            try:
                # Get POI from queue
                poi = self.queue_manager.get_poi(timeout=5)
                logger.info(f"Processing POI {i + 1}/{poi_count}: {poi.name}")

                # Process with parallel executor
                results = self.parallel_executor.process_poi(poi)

                # Put results in queue
                for result in results:
                    self.queue_manager.put_result(result)

                # Judge the results
                judgment = self.judge_agent.run(results)

                # Put judgment in queue
                self.queue_manager.put_judgment(judgment)

                # Also collect for return value
                judgments.append(judgment)

                logger.info(f"POI {i + 1}/{poi_count} complete: {judgment.selected_type}")

            except Exception as e:
                logger.error(f"Failed to process POI {i + 1}: {e}")
                break

        logger.info(f"Queue-only pipeline complete: {len(judgments)} judgments")
        return judgments

    def get_stats(self) -> Dict[str, any]:
        """
        Get pipeline statistics.

        Returns:
            Dictionary with queue stats and other metrics
        """
        stats = {
            "queue_stats": self.queue_manager.get_stats(),
            "executor_timeout": self.parallel_executor.timeout,
        }
        return stats

    def clear(self) -> None:
        """Clear all queues in the pipeline."""
        logger.info("Clearing pipeline queues")
        self.queue_manager.clear_all()

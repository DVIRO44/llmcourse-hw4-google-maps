"""Worker functions for parallel content agent execution.

IMPORTANT: Worker functions must be at module level (not nested) for multiprocessing to work!
"""

import logging
from typing import Dict, Any
from tour_guide.models.poi import POI
from tour_guide.models.content import ContentResult
from tour_guide.agents.youtube import YouTubeAgent
from tour_guide.agents.spotify import SpotifyAgent
from tour_guide.agents.history import HistoryAgent

# Suppress agent logging in worker processes to avoid log contention
logging.getLogger("tour_guide.agents").setLevel(logging.WARNING)


def content_worker(agent_type: str, poi: POI) -> ContentResult:
    """
    Worker function that runs a content agent for a POI.

    This function is called by multiprocessing.Pool to run agents in parallel.
    Must be at module level for pickling to work.

    Args:
        agent_type: Type of agent to run ("youtube", "spotify", or "history")
        poi: POI object to process

    Returns:
        ContentResult from the agent, or error ContentResult if agent fails

    Raises:
        ValueError: If agent_type is invalid
    """
    # Map agent types to agent classes
    agent_classes = {
        "youtube": YouTubeAgent,
        "spotify": SpotifyAgent,
        "history": HistoryAgent,
    }

    if agent_type not in agent_classes:
        raise ValueError(
            f"Invalid agent_type: {agent_type}. Must be one of {list(agent_classes.keys())}"
        )

    try:
        # Instantiate the appropriate agent
        agent_class = agent_classes[agent_type]
        agent = agent_class()

        # Run the agent and return result
        result = agent.run(poi)
        return result

    except Exception as e:
        # If agent fails, return an error ContentResult
        error_result = ContentResult(
            content_type=agent_type,
            title=f"Error: {agent_type} agent failed",
            description=f"Agent failed with error: {str(e)}",
            relevance_score=0,
            agent_name=agent_type,
            poi_name=poi.name,
            metadata={"error": str(e), "error_type": type(e).__name__},
        )
        return error_result


def batch_content_worker(tasks: list) -> list:
    """
    Worker function that processes multiple POI-agent pairs.

    This is useful for processing a batch of tasks in a single worker process,
    reducing the overhead of process spawning.

    Args:
        tasks: List of (agent_type, poi) tuples

    Returns:
        List of ContentResult objects
    """
    results = []
    for agent_type, poi in tasks:
        result = content_worker(agent_type, poi)
        results.append(result)
    return results

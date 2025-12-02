"""Content result model for agent outputs."""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class ContentResult:
    """
    Result from a content agent.

    Attributes:
        content_type: Type of content (youtube, spotify, history)
        title: Title of the content
        description: Description or full text of the content
        relevance_score: Relevance score from 0-100
        metadata: Additional metadata specific to content type
        agent_name: Name of the agent that generated this
        poi_name: Name of the POI this content is for
    """

    content_type: str
    title: str
    description: str
    relevance_score: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_name: str = ""
    poi_name: str = ""

    def __post_init__(self):
        """Validate content result data."""
        # Validate relevance score
        if not 0 <= self.relevance_score <= 100:
            raise ValueError(
                f"Invalid relevance_score: {self.relevance_score}. Must be 0-100."
            )

        # Validate content type
        valid_types = ["youtube", "spotify", "history"]
        if self.content_type not in valid_types:
            raise ValueError(
                f"Invalid content_type: {self.content_type}. Must be one of {valid_types}"
            )

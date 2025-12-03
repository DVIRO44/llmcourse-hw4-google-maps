"""Content result model for agent outputs."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from urllib.parse import quote_plus


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
    url: Optional[str] = None

    def __post_init__(self):
        """Validate content result data and generate URL."""
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

        # Generate URL if not provided
        if self.url is None:
            self.url = self._generate_search_url()

    def _generate_search_url(self) -> str:
        """
        Generate a search URL based on content type.

        Returns:
            Search URL for the content
        """
        if self.content_type == "youtube":
            # YouTube search URL
            query = quote_plus(self.title)
            return f"https://www.youtube.com/results?search_query={query}"

        elif self.content_type == "spotify":
            # Spotify search URL - include artist if available
            query = self.title
            if "artist" in self.metadata and self.metadata["artist"]:
                query = f"{self.title} {self.metadata['artist']}"
            encoded_query = quote_plus(query)
            return f"https://open.spotify.com/search/{encoded_query}"

        elif self.content_type == "history":
            # For historical content, create a Google search URL
            query = quote_plus(f"{self.title} history")
            return f"https://www.google.com/search?q={query}"

        return ""

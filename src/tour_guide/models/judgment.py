"""Judgment result model for Judge agent outputs."""

from dataclasses import dataclass, field
from typing import Dict, List
from tour_guide.models.content import ContentResult


@dataclass
class JudgmentResult:
    """
    Result from Judge agent evaluation.

    Attributes:
        poi_name: Name of the POI being evaluated
        selected_content: The winning content result
        selected_type: Type of selected content (youtube, spotify, history)
        reasoning: 2-3 sentence explanation for the choice
        scores: Scores for all three content options
        all_content: All content options for reference
    """

    poi_name: str
    selected_content: ContentResult
    selected_type: str
    reasoning: str
    scores: Dict[str, int] = field(default_factory=dict)
    all_content: List[ContentResult] = field(default_factory=list)

    def __post_init__(self):
        """Validate judgment result data."""
        # Validate selected_type
        valid_types = ["youtube", "spotify", "history"]
        if self.selected_type not in valid_types:
            raise ValueError(
                f"Invalid selected_type: {self.selected_type}. Must be one of {valid_types}"
            )

        # Validate that selected_content matches selected_type
        if self.selected_content.content_type != self.selected_type:
            raise ValueError(
                f"Mismatch: selected_type is '{self.selected_type}' but "
                f"selected_content.content_type is '{self.selected_content.content_type}'"
            )

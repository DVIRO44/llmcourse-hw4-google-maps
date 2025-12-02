"""Judge agent for evaluating and selecting best content."""

import json
import logging
from typing import List

from tour_guide.agents.base import BaseAgent, AgentError
from tour_guide.models.content import ContentResult
from tour_guide.models.judgment import JudgmentResult
from tour_guide.skills.judge_skill import format_judge_prompt
from tour_guide.utils.claude_cli import call_claude, ClaudeError

logger = logging.getLogger(__name__)


class JudgeAgent(BaseAgent):
    """
    Agent that evaluates content from multiple sources and selects the best one.

    Evaluates YouTube, Spotify, and History content based on:
    - Relevance to POI (40 points)
    - Educational Value (25 points)
    - Entertainment Value (20 points)
    - Quality/Uniqueness (15 points)
    """

    def __init__(self):
        """Initialize the Judge agent."""
        super().__init__("judge")

    def run(self, input_data: List[ContentResult]) -> JudgmentResult:
        """
        Evaluate content options and select the best one.

        Args:
            input_data: List of ContentResult objects (up to 3: youtube, spotify, history)

        Returns:
            JudgmentResult with selected content and evaluation details

        Raises:
            AgentError: If input is invalid or evaluation fails
        """
        # Validate input
        if not isinstance(input_data, list):
            raise AgentError("Input must be a list of ContentResult objects")

        if len(input_data) == 0:
            raise AgentError("Cannot evaluate empty content list")

        if not all(isinstance(item, ContentResult) for item in input_data):
            raise AgentError("All items must be ContentResult objects")

        # Extract POI name from first result
        poi_name = input_data[0].poi_name if input_data[0].poi_name else "Unknown POI"

        # Handle edge case: only one content option
        if len(input_data) == 1:
            logger.info(f"Only one content option available for {poi_name}, selecting by default")
            return JudgmentResult(
                poi_name=poi_name,
                selected_content=input_data[0],
                selected_type=input_data[0].content_type,
                reasoning=f"Only one content option was available. Selected {input_data[0].content_type} by default.",
                scores={input_data[0].content_type: input_data[0].relevance_score},
                all_content=input_data,
            )

        # Format prompt with content options
        prompt = format_judge_prompt(poi_name, input_data)

        # Call Claude to evaluate
        try:
            response = call_claude(prompt, timeout=30)
        except ClaudeError as e:
            # If evaluation fails, use fallback: select highest relevance_score
            logger.warning(f"Judge Claude call failed, using fallback selection: {e}")
            return self._fallback_selection(poi_name, input_data)
        except Exception as e:
            logger.warning(f"Judge evaluation failed, using fallback selection: {e}")
            return self._fallback_selection(poi_name, input_data)

        # Parse JSON response
        try:
            result_data = self._parse_json_response(response)
        except Exception as e:
            logger.warning(f"Failed to parse judge response, using fallback: {e}")
            return self._fallback_selection(poi_name, input_data)

        # Validate response structure
        if "selected" not in result_data or "reasoning" not in result_data:
            logger.warning("Invalid judge response structure, using fallback")
            return self._fallback_selection(poi_name, input_data)

        selected_type = result_data["selected"]
        reasoning = result_data["reasoning"]
        scores = result_data.get("scores", {})

        # Find the selected content
        selected_content = None
        for content in input_data:
            if content.content_type == selected_type:
                selected_content = content
                break

        if selected_content is None:
            logger.warning(f"Selected type '{selected_type}' not found in content, using fallback")
            return self._fallback_selection(poi_name, input_data)

        return JudgmentResult(
            poi_name=poi_name,
            selected_content=selected_content,
            selected_type=selected_type,
            reasoning=reasoning,
            scores=scores,
            all_content=input_data,
        )

    def _parse_json_response(self, response: str) -> dict:
        """
        Parse Claude's JSON response.

        Args:
            response: Raw response from Claude

        Returns:
            Parsed JSON dict

        Raises:
            json.JSONDecodeError: If response is not valid JSON
        """
        # Extract JSON from response (handle code block wrapping)
        json_str = response.strip()

        if "```json" in json_str:
            start = json_str.index("```json") + 7
            end = json_str.index("```", start)
            json_str = json_str[start:end].strip()
        elif "```" in json_str:
            start = json_str.index("```") + 3
            end = json_str.index("```", start)
            json_str = json_str[start:end].strip()

        # Parse JSON
        data = json.loads(json_str)
        return data

    def _fallback_selection(self, poi_name: str, content_list: List[ContentResult]) -> JudgmentResult:
        """
        Fallback selection method when Claude evaluation fails.

        Selects content with highest relevance_score. Ties broken by priority:
        History > YouTube > Spotify

        Args:
            poi_name: Name of the POI
            content_list: List of ContentResult objects

        Returns:
            JudgmentResult with selected content
        """
        # Define priority for tiebreaking
        priority = {"history": 3, "youtube": 2, "spotify": 1}

        # Sort by relevance_score (descending) then by priority (descending)
        sorted_content = sorted(
            content_list,
            key=lambda x: (x.relevance_score, priority.get(x.content_type, 0)),
            reverse=True,
        )

        selected = sorted_content[0]

        scores = {content.content_type: content.relevance_score for content in content_list}

        return JudgmentResult(
            poi_name=poi_name,
            selected_content=selected,
            selected_type=selected.content_type,
            reasoning=f"Selected {selected.content_type} based on highest relevance score ({selected.relevance_score}).",
            scores=scores,
            all_content=content_list,
        )

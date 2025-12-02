"""History agent for generating historical narratives for POIs."""

import json
from tour_guide.agents.base import BaseAgent, AgentError
from tour_guide.models import POI, ContentResult
from tour_guide.utils.claude_cli import call_claude, ClaudeError
from tour_guide.skills.history_skill import format_history_prompt


class HistoryAgent(BaseAgent):
    """Agent that generates historical narratives for a POI."""

    def __init__(self):
        """Initialize History agent."""
        super().__init__("history")

    def run(self, input_data: POI) -> ContentResult:
        """
        Generate historical narrative for a POI.

        Args:
            input_data: POI object to generate narrative for

        Returns:
            ContentResult with historical narrative

        Raises:
            AgentError: If narrative generation fails
        """
        if not isinstance(input_data, POI):
            raise AgentError(f"Expected POI object, got {type(input_data)}")

        poi = input_data

        self.logger.info(f"Generating historical narrative for: {poi.name}")

        # Create prompt
        prompt = format_history_prompt(
            poi_name=poi.name,
            poi_description=poi.description,
            poi_category=poi.category.value,
        )

        try:
            # Call Claude
            self.logger.debug(f"Requesting historical narrative from Claude")
            response = call_claude(prompt, timeout=45)  # Longer timeout for narrative

            # Parse response
            result = self._parse_response(response, poi.name)

            self.logger.info(f"Generated narrative: {result.title}")
            return result

        except ClaudeError as e:
            error_msg = f"Claude CLI failed during history generation: {e}"
            self.logger.error(error_msg)
            raise AgentError(error_msg)

        except Exception as e:
            error_msg = f"History generation failed: {e}"
            self.logger.error(error_msg)
            raise AgentError(error_msg)

    def _parse_response(self, response: str, poi_name: str) -> ContentResult:
        """
        Parse Claude's JSON response into ContentResult.

        Args:
            response: Raw response from Claude
            poi_name: Name of the POI

        Returns:
            ContentResult object

        Raises:
            AgentError: If response parsing fails
        """
        try:
            # Extract JSON from response
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

            if "story" not in data:
                raise AgentError("Response missing 'story' field")

            story = data["story"]

            # Create ContentResult
            result = ContentResult(
                content_type="history",
                title=story["title"],
                description=story["narrative"],
                relevance_score=story.get("relevance_score", 50),
                metadata={
                    "key_facts": story.get("key_facts", []),
                    "time_period": story.get("time_period", ""),
                    "historical_figures": story.get("historical_figures", []),
                },
                agent_name="history",
                poi_name=poi_name,
            )

            return result

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse Claude response as JSON: {e}"
            self.logger.error(error_msg)
            raise AgentError(error_msg)

        except (KeyError, ValueError) as e:
            error_msg = f"Failed to parse Claude response: {e}"
            self.logger.error(error_msg)
            raise AgentError(error_msg)

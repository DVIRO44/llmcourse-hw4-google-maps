"""YouTube agent for finding relevant videos for POIs."""

import json
from tour_guide.agents.base import BaseAgent, AgentError
from tour_guide.models import POI, ContentResult
from tour_guide.utils.claude_cli import call_claude, ClaudeError
from tour_guide.skills.youtube_skill import format_youtube_prompt


class YouTubeAgent(BaseAgent):
    """Agent that finds relevant YouTube videos for a POI."""

    def __init__(self):
        """Initialize YouTube agent."""
        super().__init__("youtube")

    def run(self, input_data: POI) -> ContentResult:
        """
        Find relevant YouTube video for a POI.

        Args:
            input_data: POI object to find video for

        Returns:
            ContentResult with video suggestion

        Raises:
            AgentError: If video search fails
        """
        if not isinstance(input_data, POI):
            raise AgentError(f"Expected POI object, got {type(input_data)}")

        poi = input_data

        self.logger.info(f"Finding YouTube video for: {poi.name}")

        # Create prompt
        prompt = format_youtube_prompt(
            poi_name=poi.name,
            poi_description=poi.description,
            poi_category=poi.category.value,
        )

        try:
            # Call Claude
            self.logger.debug("Requesting video suggestion from Claude")
            response = call_claude(prompt, timeout=30)

            # Parse response
            result = self._parse_response(response, poi.name)

            self.logger.info(f"Found video: {result.title}")
            return result

        except ClaudeError as e:
            error_msg = f"Claude CLI failed during YouTube search: {e}"
            self.logger.error(error_msg)
            raise AgentError(error_msg)

        except Exception as e:
            error_msg = f"YouTube search failed: {e}"
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

            if "video" not in data:
                raise AgentError("Response missing 'video' field")

            video = data["video"]

            # Create ContentResult
            result = ContentResult(
                content_type="youtube",
                title=video["title"],
                description=video.get("description", ""),
                relevance_score=video.get("relevance_score", 50),
                metadata={
                    "channel": video.get("channel", ""),
                    "duration_estimate": video.get("duration_estimate", ""),
                    "why_relevant": video.get("why_relevant", ""),
                },
                agent_name="youtube",
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

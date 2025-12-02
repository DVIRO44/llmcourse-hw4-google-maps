"""Skill prompt for Judge agent."""

JUDGE_PROMPT = """You are a content judge. Evaluate these content options for the location "{poi_name}" and select the single best one.

**OPTION 1 - YouTube:**
Title: {youtube_title}
Description: {youtube_description}
Relevance Score: {youtube_score}

**OPTION 2 - Spotify:**
Title: {spotify_title}
Description: {spotify_description}
Relevance Score: {spotify_score}

**OPTION 3 - History:**
Title: {history_title}
Description: {history_description}
Relevance Score: {history_score}

**Evaluation Criteria:**
1. Relevance to POI (0-40 points): How specifically relevant is this content to this exact location?
2. Educational Value (0-25 points): How much will the visitor learn?
3. Entertainment Value (0-20 points): How engaging and enjoyable is this?
4. Quality/Uniqueness (0-15 points): Is this high-quality and unique content?

**Task:**
Evaluate each option, assign scores, and select EXACTLY ONE winner.

**Output Format (JSON only, no explanation):**
{{
  "selected": "youtube" | "spotify" | "history",
  "reasoning": "2-3 sentence explanation of why this option is best for this specific location",
  "scores": {{
    "youtube": 75,
    "spotify": 60,
    "history": 85
  }}
}}

Return ONLY the JSON object, no other text.
"""


def format_judge_prompt(poi_name: str, content_results: list) -> str:
    """
    Format the Judge prompt with content options.

    Args:
        poi_name: Name of the POI
        content_results: List of ContentResult objects [youtube, spotify, history]

    Returns:
        Formatted prompt string
    """
    # Initialize with defaults
    youtube = {"title": "N/A", "description": "Not available", "score": 0}
    spotify = {"title": "N/A", "description": "Not available", "score": 0}
    history = {"title": "N/A", "description": "Not available", "score": 0}

    # Fill in actual values
    for result in content_results:
        data = {
            "title": result.title,
            "description": result.description[:200] + "..."
            if len(result.description) > 200
            else result.description,
            "score": result.relevance_score,
        }

        if result.content_type == "youtube":
            youtube = data
        elif result.content_type == "spotify":
            spotify = data
        elif result.content_type == "history":
            history = data

    return JUDGE_PROMPT.format(
        poi_name=poi_name,
        youtube_title=youtube["title"],
        youtube_description=youtube["description"],
        youtube_score=youtube["score"],
        spotify_title=spotify["title"],
        spotify_description=spotify["description"],
        spotify_score=spotify["score"],
        history_title=history["title"],
        history_description=history["description"],
        history_score=history["score"],
    )

"""Skill prompt for History agent."""

HISTORY_PROMPT = """You are a historical storyteller. Create an engaging historical narrative about this location.

**Location Information:**
- Name: {poi_name}
- Description: {poi_description}
- Category: {poi_category}

**Task:**
Write a compelling historical narrative (300-500 words) about this location in story format. Include:
- Specific dates, people, and events
- Key historical moments or turning points
- Cultural and historical significance
- Engaging narrative that brings history to life
- Factual accuracy with concrete details

**Output Format (JSON only, no explanation):**
{{
  "story": {{
    "title": "The Siege of Masada: 960 Souls Against Rome",
    "narrative": "In 73 CE, atop an isolated rock plateau overlooking the Dead Sea, 960 Jewish rebels made their last stand against the might of Rome...[300-500 words continuing the story with specific historical details, people, dates, and events]",
    "key_facts": [
      "Masada was built by Herod the Great between 37-31 BCE",
      "The siege lasted from 73-74 CE during the First Jewish-Roman War",
      "960 Zealots chose mass suicide over Roman enslavement",
      "Archaeological excavations in the 1960s confirmed historical accounts"
    ],
    "relevance_score": 95,
    "time_period": "73-74 CE",
    "historical_figures": ["Eleazar ben Ya'ir", "Flavius Silva", "Josephus"]
  }}
}}

Return ONLY the JSON object, no other text.
"""


def format_history_prompt(poi_name: str, poi_description: str, poi_category: str) -> str:
    """
    Format the History prompt with POI data.

    Args:
        poi_name: Name of the POI
        poi_description: Description of the POI
        poi_category: Category of the POI

    Returns:
        Formatted prompt string
    """
    return HISTORY_PROMPT.format(
        poi_name=poi_name,
        poi_description=poi_description,
        poi_category=poi_category,
    )

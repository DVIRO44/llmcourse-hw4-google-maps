"""Configuration settings management."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import yaml


@dataclass
class LoggingConfig:
    max_bytes: int = 10485760  # 10 MB
    backup_count: int = 5
    level: str = "INFO"
    format: str = "json"


@dataclass
class RoutingConfig:
    osrm_url: str = "http://router.project-osrm.org"
    fallback_to_claude: bool = True
    timeout_seconds: int = 10


@dataclass
class AgentsConfig:
    content_timeout: int = 30
    judge_timeout: int = 10
    max_retries: int = 2


@dataclass
class OutputConfig:
    journey_delay: int = 5
    default_json_path: str = "./output/journey.json"
    default_markdown_path: str = "./output/journey.md"


@dataclass
class POIConfig:
    count: int = 10
    min_distance_between_km: float = 5.0


@dataclass
class Settings:
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    routing: RoutingConfig = field(default_factory=RoutingConfig)
    agents: AgentsConfig = field(default_factory=AgentsConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    poi: POIConfig = field(default_factory=POIConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> "Settings":
        """Load settings from YAML file."""
        if not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        return cls(
            logging=LoggingConfig(**data.get("logging", {})),
            routing=RoutingConfig(**data.get("routing", {})),
            agents=AgentsConfig(**data.get("agents", {})),
            output=OutputConfig(**data.get("output", {})),
            poi=POIConfig(**data.get("poi", {})),
        )


_settings: Optional[Settings] = None


def get_settings(config_path: Optional[Path] = None) -> Settings:
    """Get or create settings singleton."""
    global _settings

    if _settings is None:
        path = config_path or Path(
            os.environ.get("TOUR_GUIDE_CONFIG_PATH", "config/settings.yaml")
        )
        _settings = Settings.from_yaml(path)

    return _settings


def reset_settings():
    """Reset settings (for testing)."""
    global _settings
    _settings = None

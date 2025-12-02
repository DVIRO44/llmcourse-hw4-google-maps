# Implementation Tasks

## Overview

This document provides a detailed implementation checklist for the Tour Guide AI System, broken into 10 sequential phases with 28 total tasks. The implementation follows these principles:

- **Incremental Development**: Build one component at a time, ensuring each works before moving forward
- **Test-Driven**: Write tests for each component before implementation
- **Commit After Completion**: Commit after each task is complete and tested
- **Building Block Pattern**: Each component has clear input/output/config/dependencies/error handling
- **Bottom-Up Approach**: Start with foundational components (config, logging) before complex agents

**Total Duration Estimate**: 6-7 weeks for solo developer

---

## Phase 1: Project Foundation (Week 1)

### Task 1.1: Initialize UV Project
**Description**: Set up UV package manager and create pyproject.toml with all dependencies

**Files to Create**:
- `pyproject.toml` - Project metadata and dependencies
- `.gitignore` - Ignore logs/, output/, __pycache__, .env
- `.python-version` - Specify Python 3.10
- `README.md` - Basic project description

**Dependencies to Include**:
```toml
[project]
dependencies = [
    "click>=8.1.0",
    "rich>=13.0.0",
    "requests>=2.31.0",
    "pyyaml>=6.0",
    "jsonschema>=4.20.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]
```

**Acceptance Criteria**:
- `uv sync` completes without errors
- `uv run python --version` shows Python 3.10+
- All dependencies installed correctly

**Test Command**:
```bash
uv sync
uv run python -c "import click, rich, requests, yaml, jsonschema; print('All imports successful')"
```

**Commit Message**: `feat: initialize UV project with dependencies`

---

### Task 1.2: Create Package Structure
**Description**: Create all directories and `__init__.py` files per DESIGN.md Section 11

**Files to Create**:
```
src/tour_guide/
├── __init__.py                    # Package version export
├── __main__.py                    # CLI entry point
├── cli/
│   ├── __init__.py
│   └── main.py                    # Placeholder CLI
├── core/
│   ├── __init__.py
│   ├── types.py                   # Core data classes
│   └── exceptions.py              # Custom exceptions
├── agents/
│   └── __init__.py
├── routing/
│   └── __init__.py
├── queue/
│   └── __init__.py
├── logging_/                      # Avoid conflict with stdlib
│   └── __init__.py
├── output/
│   └── __init__.py
├── skills/
│   └── __init__.py
├── config/
│   └── __init__.py
└── utils/
    └── __init__.py

tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures
├── unit/
│   └── __init__.py
└── integration/
    └── __init__.py

config/
└── default.yaml                   # Default configuration

logs/
└── .gitkeep

output/
└── .gitkeep
```

**Core Types to Define** (`src/tour_guide/core/types.py`):
```python
from dataclasses import dataclass
from typing import Tuple, List, Optional, Dict, Any
from enum import Enum

@dataclass
class Waypoint:
    lat: float
    long: float
    distance_from_start_km: float

@dataclass
class RouteData:
    origin_coords: Tuple[float, float]
    destination_coords: Tuple[float, float]
    origin_name: str
    destination_name: str
    distance_km: float
    duration_seconds: int
    waypoints: List[Waypoint]
    landmarks: List[str]
    data_source: str  # "osrm" or "claude"

class POICategory(Enum):
    HISTORICAL = "historical"
    CULTURAL = "cultural"
    NATURAL = "natural"
    RELIGIOUS = "religious"
    ENTERTAINMENT = "entertainment"

@dataclass
class POI:
    id: str
    name: str
    coordinates: Tuple[float, float]
    description: str
    category: POICategory
    distance_from_start_km: float
    estimated_time_seconds: int
    metadata: Dict[str, Any]

class AgentType(Enum):
    YOUTUBE = "youtube"
    SPOTIFY = "spotify"
    HISTORY = "history"

class ResultStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"

@dataclass
class ContentResult:
    agent_type: AgentType
    poi_id: str
    content: Any
    relevance_score: float
    execution_time_seconds: float
    status: ResultStatus
    error_message: Optional[str] = None
```

**Exceptions to Define** (`src/tour_guide/core/exceptions.py`):
```python
class TourGuideError(Exception):
    """Base exception for Tour Guide"""
    pass

class RoutingError(TourGuideError):
    """Routing failed"""
    pass

class OSRMError(RoutingError):
    """OSRM API error"""
    pass

class ClaudeError(TourGuideError):
    """Claude CLI error"""
    pass

class AgentError(TourGuideError):
    """Agent execution error"""
    pass

class ConfigError(TourGuideError):
    """Configuration error"""
    pass
```

**Acceptance Criteria**:
- All directories created
- Package is importable: `from tour_guide import __version__`
- Core types are importable

**Test Command**:
```bash
uv run python -c "from tour_guide.core.types import POI, RouteData; from tour_guide.core.exceptions import TourGuideError; print('Package structure OK')"
```

**Commit Message**: `feat: create package structure with core types`

---

### Task 1.3: Implement Configuration Management
**Description**: Create config system that loads from YAML and environment variables

**Files to Create**:
- `src/tour_guide/config/settings.py` - Config classes and loader
- `config/default.yaml` - Default configuration
- `tests/unit/test_config.py` - Config tests

**Configuration Structure** (`config/default.yaml`):
```yaml
# Tour Guide Default Configuration

logging:
  level: INFO
  max_bytes: 10485760  # 10 MB
  backup_count: 5
  format: json
  log_dir: ./logs
  enable_console: true

routing:
  osrm_url: "http://router.project-osrm.org"
  fallback_to_claude: true
  timeout_seconds: 10
  max_retries: 2

agents:
  content_agent_timeout: 30
  judge_agent_timeout: 10
  max_retries: 2
  enable_parallel_execution: true

claude:
  model: "claude-sonnet-4"
  max_tokens: 4000
  temperature: 0.7
  subprocess_timeout: 15

output:
  journey_delay_seconds: 5
  enable_progress_bar: true
  enable_colors: true
  default_json_path: ./output/journey.json
  default_markdown_path: ./output/journey.md

poi:
  count: 10
  min_distance_between_km: 5
  categories:
    - historical
    - cultural
    - natural
    - religious
    - entertainment
  distribution_algorithm: even_spread

queues:
  poi_queue_size: 10
  content_queue_size: 30
  results_queue_size: 10

system:
  overall_timeout: 180
  force_continue: false
  verbose_errors: true
```

**Config Loader** (`src/tour_guide/config/settings.py`):
```python
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import yaml
import os

@dataclass
class LoggingConfig:
    level: str
    max_bytes: int
    backup_count: int
    format: str
    log_dir: Path
    enable_console: bool

@dataclass
class RoutingConfig:
    osrm_url: str
    fallback_to_claude: bool
    timeout_seconds: int
    max_retries: int

@dataclass
class AgentConfig:
    content_agent_timeout: int
    judge_agent_timeout: int
    max_retries: int
    enable_parallel_execution: bool

@dataclass
class ClaudeConfig:
    model: str
    max_tokens: int
    temperature: float
    subprocess_timeout: int

@dataclass
class Config:
    logging: LoggingConfig
    routing: RoutingConfig
    agents: AgentConfig
    claude: ClaudeConfig
    # ... other sections

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'Config':
        """Load config from YAML file with env var overrides"""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "default.yaml"

        with open(config_path) as f:
            data = yaml.safe_load(f)

        # Apply environment variable overrides
        data = cls._apply_env_overrides(data)

        return cls.from_dict(data)

    @staticmethod
    def _apply_env_overrides(data: dict) -> dict:
        """Override config with environment variables"""
        # Example: TOUR_GUIDE_LOG_LEVEL overrides logging.level
        if log_level := os.getenv("TOUR_GUIDE_LOG_LEVEL"):
            data["logging"]["level"] = log_level
        if osrm_url := os.getenv("TOUR_GUIDE_OSRM_URL"):
            data["routing"]["osrm_url"] = osrm_url
        return data
```

**Acceptance Criteria**:
- Config loads from YAML successfully
- Environment variables override YAML values
- Missing config file raises `ConfigError`

**Test Command**:
```bash
uv run pytest tests/unit/test_config.py -v
```

**Commit Message**: `feat: add configuration management with YAML and env vars`

---

### Task 1.4: Implement Logging System
**Description**: Set up logging with rotation, JSON format, and multi-process support

**Files to Create**:
- `src/tour_guide/logging_/setup.py` - Logger initialization
- `src/tour_guide/logging_/formatters.py` - JSON formatter
- `tests/unit/test_logging.py` - Logging tests

**Logger Setup** (`src/tour_guide/logging_/setup.py`):
```python
import logging
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "process_id": record.process,
            "thread_id": record.thread,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add custom fields
        if hasattr(record, "agent_name"):
            log_obj["agent_name"] = record.agent_name
        if hasattr(record, "poi_id"):
            log_obj["poi_id"] = record.poi_id
        if hasattr(record, "execution_time"):
            log_obj["execution_time_seconds"] = record.execution_time

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

def setup_logger(
    name: str,
    log_dir: Path,
    level: str = "INFO",
    max_bytes: int = 10485760,
    backup_count: int = 5,
    enable_console: bool = True,
    use_json: bool = True
) -> logging.Logger:
    """Set up logger with rotation"""

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    logger.handlers.clear()  # Remove existing handlers

    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)

    # File handler with rotation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"tour_guide_{timestamp}.log"

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )

    # Set formatter
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(process)d - %(name)s - %(message)s"
        )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler (optional)
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
```

**Acceptance Criteria**:
- Logs rotate when file reaches max size
- JSON format is valid
- Multi-process logging works without conflicts
- Log files created in correct directory

**Test Command**:
```bash
uv run pytest tests/unit/test_logging.py -v
```

**Commit Message**: `feat: add logging system with rotation and JSON format`

---

## Phase 2: Routing System (Week 1-2)

### Task 2.1: Implement OSRM Client
**Description**: HTTP client for OSRM routing API with proper error handling

**Files to Create**:
- `src/tour_guide/routing/osrm_client.py` - OSRM API client
- `tests/unit/test_osrm_client.py` - OSRM client tests

**OSRM Client** (`src/tour_guide/routing/osrm_client.py`):
```python
import requests
from typing import Tuple, List, Dict, Any
from tour_guide.core.types import RouteData, Waypoint
from tour_guide.core.exceptions import OSRMError
import logging

logger = logging.getLogger(__name__)

class OSRMClient:
    """Client for OSRM routing API"""

    def __init__(self, base_url: str = "http://router.project-osrm.org", timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float]
    ) -> RouteData:
        """Get route from OSRM API

        Args:
            origin: (lat, lon) tuple
            destination: (lat, lon) tuple

        Returns:
            RouteData object

        Raises:
            OSRMError: If OSRM request fails
        """
        # OSRM uses lon,lat format (opposite of lat,lon)
        origin_str = f"{origin[1]},{origin[0]}"
        dest_str = f"{destination[1]},{destination[0]}"

        url = f"{self.base_url}/route/v1/driving/{origin_str};{dest_str}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true"
        }

        try:
            logger.debug(f"OSRM request: {url}")
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "Ok":
                raise OSRMError(f"OSRM returned error: {data.get('message', 'Unknown error')}")

            return self._parse_osrm_response(data, origin, destination)

        except requests.Timeout:
            raise OSRMError(f"OSRM request timed out after {self.timeout}s")
        except requests.RequestException as e:
            raise OSRMError(f"OSRM request failed: {e}")
        except (KeyError, ValueError) as e:
            raise OSRMError(f"Invalid OSRM response: {e}")

    def _parse_osrm_response(
        self,
        data: Dict[str, Any],
        origin: Tuple[float, float],
        destination: Tuple[float, float]
    ) -> RouteData:
        """Parse OSRM JSON response into RouteData"""

        route = data["routes"][0]

        # Extract waypoints from geometry
        coordinates = route["geometry"]["coordinates"]
        waypoints = []

        cumulative_distance = 0.0
        for i, coord in enumerate(coordinates):
            if i > 0:
                # Calculate distance (simplified, OSRM provides this in legs)
                prev = coordinates[i - 1]
                # Rough distance calculation
                cumulative_distance += self._haversine(
                    prev[1], prev[0], coord[1], coord[0]
                )

            waypoints.append(Waypoint(
                lat=coord[1],
                long=coord[0],
                distance_from_start_km=cumulative_distance
            ))

        # Extract landmarks from steps
        landmarks = []
        for leg in route.get("legs", []):
            for step in leg.get("steps", []):
                if name := step.get("name"):
                    if name and name not in landmarks:
                        landmarks.append(name)

        return RouteData(
            origin_coords=origin,
            destination_coords=destination,
            origin_name=f"{origin[0]:.4f},{origin[1]:.4f}",
            destination_name=f"{destination[0]:.4f},{destination[1]:.4f}",
            distance_km=route["distance"] / 1000,
            duration_seconds=int(route["duration"]),
            waypoints=waypoints,
            landmarks=landmarks[:20],  # Limit to 20
            data_source="osrm"
        )

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Earth radius in km

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c
```

**Acceptance Criteria**:
- Successfully routes Tel Aviv (32.0853, 34.7818) to Jerusalem (31.7683, 35.2137)
- Returns RouteData with waypoints, distance, duration
- Handles timeouts and network errors gracefully
- Parses OSRM response correctly

**Test Command**:
```bash
uv run pytest tests/unit/test_osrm_client.py -v
```

**Commit Message**: `feat: add OSRM routing client`

---

### Task 2.2: Implement Claude Fallback Router
**Description**: Use Claude CLI subprocess when OSRM fails

**Files to Create**:
- `src/tour_guide/utils/claude_cli.py` - Claude CLI subprocess wrapper
- `src/tour_guide/routing/claude_router.py` - Claude-based routing
- `tests/unit/test_claude_router.py` - Tests

**Claude CLI Wrapper** (`src/tour_guide/utils/claude_cli.py`):
```python
import subprocess
import logging
from typing import Optional
from tour_guide.core.exceptions import ClaudeError

logger = logging.getLogger(__name__)

def call_claude_cli(
    prompt: str,
    model: str = "claude-sonnet-4",
    max_tokens: int = 4000,
    temperature: float = 0.7,
    timeout: int = 30
) -> str:
    """Call Claude CLI as subprocess

    Args:
        prompt: Prompt to send to Claude
        model: Model to use
        max_tokens: Maximum tokens in response
        temperature: Temperature (0.0-1.0)
        timeout: Timeout in seconds

    Returns:
        Claude's response as string

    Raises:
        ClaudeError: If Claude CLI fails
    """

    cmd = [
        "claude",
        "--model", model,
        "--max-tokens", str(max_tokens),
        "--temperature", str(temperature),
        prompt
    ]

    try:
        logger.debug(f"Calling Claude CLI with prompt length: {len(prompt)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )

        response = result.stdout.strip()
        logger.debug(f"Claude response length: {len(response)}")
        return response

    except subprocess.TimeoutExpired:
        raise ClaudeError(f"Claude CLI timed out after {timeout}s")
    except subprocess.CalledProcessError as e:
        raise ClaudeError(f"Claude CLI failed: {e.stderr}")
    except FileNotFoundError:
        raise ClaudeError("Claude CLI not found. Please install: pip install claude-cli")
```

**Claude Router** (`src/tour_guide/routing/claude_router.py`):
```python
from typing import Tuple
from tour_guide.core.types import RouteData, Waypoint
from tour_guide.utils.claude_cli import call_claude_cli
from tour_guide.core.exceptions import ClaudeError
import json
import logging

logger = logging.getLogger(__name__)

def get_route_from_claude(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    origin_name: str = "",
    destination_name: str = ""
) -> RouteData:
    """Get route using Claude CLI

    This is a fallback when OSRM fails. Claude will generate a plausible route.
    """

    prompt = f"""
You are a routing expert. Generate a plausible driving route between two locations.

Origin: {origin_name or f"{origin[0]:.4f},{origin[1]:.4f}"}
Destination: {destination_name or f"{destination[0]:.4f},{destination[1]:.4f}"}

Provide a route with:
1. Estimated distance in kilometers
2. Estimated duration in seconds
3. At least 20 waypoints (coordinates along the route)
4. Names of major roads/landmarks along the route

Return ONLY a JSON object in this format:
{{
  "distance_km": 65.0,
  "duration_seconds": 3600,
  "waypoints": [
    {{"lat": 32.0853, "long": 34.7818, "distance_from_start_km": 0.0}},
    ...
  ],
  "landmarks": ["Highway 1", "Latrun Interchange", ...]
}}
"""

    try:
        response = call_claude_cli(prompt, timeout=30)

        # Parse JSON response
        # Claude might wrap in ```json ... ```, so extract
        if "```json" in response:
            json_start = response.index("```json") + 7
            json_end = response.index("```", json_start)
            json_str = response[json_start:json_end].strip()
        else:
            json_str = response.strip()

        data = json.loads(json_str)

        # Convert to RouteData
        waypoints = [
            Waypoint(
                lat=w["lat"],
                long=w["long"],
                distance_from_start_km=w["distance_from_start_km"]
            )
            for w in data["waypoints"]
        ]

        return RouteData(
            origin_coords=origin,
            destination_coords=destination,
            origin_name=origin_name or f"{origin[0]:.4f},{origin[1]:.4f}",
            destination_name=destination_name or f"{destination[0]:.4f},{destination[1]:.4f}",
            distance_km=data["distance_km"],
            duration_seconds=data["duration_seconds"],
            waypoints=waypoints,
            landmarks=data["landmarks"],
            data_source="claude"
        )

    except (json.JSONDecodeError, KeyError) as e:
        raise ClaudeError(f"Invalid Claude response: {e}")
```

**Acceptance Criteria**:
- Returns valid RouteData when called
- Handles Claude CLI errors gracefully
- Generates plausible routes with waypoints

**Test Command**:
```bash
uv run pytest tests/unit/test_claude_router.py -v
```

**Commit Message**: `feat: add Claude fallback router`

---

### Task 2.3: Implement Route Planner
**Description**: Main routing interface that tries OSRM then falls back to Claude

**Files to Create**:
- `src/tour_guide/routing/planner.py` - Route planner
- `src/tour_guide/routing/geocoder.py` - Geocoding helper
- `tests/unit/test_route_planner.py` - Tests
- `tests/integration/test_routing_integration.py` - Integration tests

**Route Planner** (`src/tour_guide/routing/planner.py`):
```python
from typing import Union, Tuple
from tour_guide.core.types import RouteData
from tour_guide.routing.osrm_client import OSRMClient
from tour_guide.routing.claude_router import get_route_from_claude
from tour_guide.core.exceptions import RoutingError, OSRMError
from tour_guide.config.settings import RoutingConfig
import logging

logger = logging.getLogger(__name__)

class RoutePlanner:
    """Main routing interface with OSRM and Claude fallback"""

    def __init__(self, config: RoutingConfig):
        self.config = config
        self.osrm_client = OSRMClient(config.osrm_url, config.timeout_seconds)

    def plan_route(
        self,
        origin: Union[str, Tuple[float, float]],
        destination: Union[str, Tuple[float, float]]
    ) -> RouteData:
        """Plan route from origin to destination

        Args:
            origin: Place name or (lat, lon) tuple
            destination: Place name or (lat, lon) tuple

        Returns:
            RouteData object

        Raises:
            RoutingError: If both OSRM and Claude fail
        """

        # Convert place names to coordinates if needed
        origin_coords, origin_name = self._resolve_location(origin)
        dest_coords, dest_name = self._resolve_location(destination)

        logger.info(f"Planning route: {origin_name} → {dest_name}")

        # Try OSRM first
        try:
            logger.debug("Attempting OSRM routing")
            route = self.osrm_client.get_route(origin_coords, dest_coords)
            route.origin_name = origin_name
            route.destination_name = dest_name
            logger.info(f"OSRM routing successful: {route.distance_km:.1f} km")
            return route

        except OSRMError as e:
            logger.warning(f"OSRM failed: {e}")

            if not self.config.fallback_to_claude:
                raise RoutingError(f"OSRM failed and Claude fallback disabled: {e}")

        # Fallback to Claude
        try:
            logger.debug("Falling back to Claude routing")
            route = get_route_from_claude(
                origin_coords, dest_coords,
                origin_name, dest_name
            )
            logger.info(f"Claude routing successful: {route.distance_km:.1f} km")
            return route

        except Exception as e:
            logger.error(f"Claude fallback also failed: {e}")
            raise RoutingError(f"Both OSRM and Claude routing failed: {e}")

    def _resolve_location(self, location: Union[str, Tuple[float, float]]) -> Tuple[Tuple[float, float], str]:
        """Convert location to (coordinates, name) tuple"""

        if isinstance(location, tuple):
            # Already coordinates
            return location, f"{location[0]:.4f},{location[1]:.4f}"
        else:
            # Place name - need to geocode
            from tour_guide.routing.geocoder import geocode
            coords = geocode(location)
            return coords, location
```

**Simple Geocoder** (`src/tour_guide/routing/geocoder.py`):
```python
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# Simple hardcoded geocoding for Israeli cities (for now)
KNOWN_LOCATIONS = {
    "tel aviv": (32.0853, 34.7818),
    "jerusalem": (31.7683, 35.2137),
    "haifa": (32.7940, 34.9896),
    "eilat": (29.5577, 34.9519),
    "beer sheva": (31.2518, 34.7913),
    "nazareth": (32.7008, 35.2978),
    "akko": (32.9276, 35.0833),
    "caesarea": (32.5014, 34.8939),
    "masada": (31.3157, 35.3540),
    "dead sea": (31.5590, 35.4732),
    "tiberias": (32.7956, 35.5317),
    "rosh hanikra": (33.0891, 35.1064),
    "bethlehem": (31.7054, 35.2024),
    "jaffa": (32.0543, 34.7516),
}

def geocode(place_name: str) -> Tuple[float, float]:
    """Simple geocoder for known locations

    Args:
        place_name: Name of place

    Returns:
        (lat, lon) tuple

    Raises:
        ValueError: If place not found
    """

    normalized = place_name.lower().strip()

    if normalized in KNOWN_LOCATIONS:
        coords = KNOWN_LOCATIONS[normalized]
        logger.debug(f"Geocoded '{place_name}' to {coords}")
        return coords

    # TODO: Use Claude CLI for geocoding unknown places
    raise ValueError(f"Unknown location: {place_name}. Add to KNOWN_LOCATIONS or implement Claude geocoding.")
```

**Acceptance Criteria**:
- Successfully routes between all test cities
- Falls back to Claude when OSRM is mocked to fail
- Geocodes Israeli city names correctly
- Returns consistent RouteData format

**Test Command**:
```bash
uv run pytest tests/unit/test_route_planner.py -v
uv run pytest tests/integration/test_routing_integration.py -v
```

**Commit Message**: `feat: add route planner with OSRM and Claude fallback`

---

## Phase 3: Route Analyzer Agent (Week 2)

### Task 3.1: Implement Skills Framework
**Description**: Framework for loading and formatting prompt templates

**Files to Create**:
- `src/tour_guide/skills/loader.py` - Skill loader
- `src/tour_guide/skills/route_analysis.skill` - Route analysis prompt
- `tests/unit/test_skills.py` - Skills tests

**Skill Loader** (`src/tour_guide/skills/loader.py`):
```python
from pathlib import Path
from string import Template
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class Skill:
    """Represents a prompt template skill"""

    def __init__(self, name: str, template: str):
        self.name = name
        self.template = Template(template)

    def format(self, **kwargs) -> str:
        """Format skill template with variables"""
        try:
            return self.template.safe_substitute(**kwargs)
        except KeyError as e:
            logger.error(f"Missing variable in skill {self.name}: {e}")
            raise

class SkillLoader:
    """Loads and caches prompt template skills"""

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.cache: Dict[str, Skill] = {}

    def load(self, skill_name: str) -> Skill:
        """Load skill by name"""

        if skill_name in self.cache:
            return self.cache[skill_name]

        skill_file = self.skills_dir / f"{skill_name}.skill"

        if not skill_file.exists():
            raise FileNotFoundError(f"Skill not found: {skill_file}")

        template = skill_file.read_text()
        skill = Skill(skill_name, template)

        self.cache[skill_name] = skill
        logger.debug(f"Loaded skill: {skill_name}")

        return skill

# Global skill loader
_skills_dir = Path(__file__).parent
skill_loader = SkillLoader(_skills_dir)

def load_skill(skill_name: str) -> Skill:
    """Convenience function to load skill"""
    return skill_loader.load(skill_name)
```

**Route Analysis Skill** (`src/tour_guide/skills/route_analysis.skill`):
```
You are a route analysis expert. Analyze the following route and select exactly 10 points of interest (POIs) that would be most interesting to travelers.

**Route Information:**
- Origin: $origin
- Destination: $destination
- Total Distance: $distance_km km
- Waypoints: $waypoints_count waypoints
- Major Landmarks: $landmarks

**Selection Criteria:**
1. Historical significance (UNESCO sites, monuments, battlefields, ancient ruins)
2. Cultural importance (museums, religious sites, traditional markets, cultural centers)
3. Natural landmarks (national parks, viewpoints, beaches, unique geological formations)
4. Tourist popularity (highly rated attractions, famous locations)
5. Geographic distribution (evenly spaced along route, not clustered)

**Requirements:**
- Select EXACTLY 10 POIs (or fewer if route is very short < 20 km)
- Distribute POIs evenly along the route (minimum 5 km apart)
- Ensure each POI is actually near the route (within 5 km)
- Provide complete metadata for each POI
- Categories: historical, cultural, natural, religious, entertainment

**Output Format (JSON only, no explanation):**
{
  "pois": [
    {
      "name": "Masada National Park",
      "coordinates": [31.3157, 35.3540],
      "description": "Ancient fortress overlooking the Dead Sea, site of famous siege in 73 CE. UNESCO World Heritage Site with dramatic desert views and cable car access.",
      "category": "historical",
      "distance_from_start_km": 45.2
    }
  ]
}

Return ONLY the JSON object, no other text.
```

**Acceptance Criteria**:
- Skills load from .skill files
- Template variables substitute correctly
- Cache works (second load is instant)

**Test Command**:
```bash
uv run pytest tests/unit/test_skills.py -v
```

**Commit Message**: `feat: add skills framework for prompt templates`

---

### Task 3.2: Implement Route Analyzer Agent
**Description**: Agent that selects 10 interesting POIs from route using Claude CLI

**Files to Create**:
- `src/tour_guide/agents/route_analyzer.py` - Route analyzer agent
- `tests/unit/test_route_analyzer.py` - Tests

**Route Analyzer Agent** (`src/tour_guide/agents/route_analyzer.py`):
```python
from typing import List
import json
import uuid
from tour_guide.core.types import RouteData, POI, POICategory
from tour_guide.utils.claude_cli import call_claude_cli
from tour_guide.skills.loader import load_skill
from tour_guide.core.exceptions import AgentError
import logging

logger = logging.getLogger(__name__)

class RouteAnalyzerAgent:
    """Agent that selects interesting POIs from route"""

    def __init__(self, config):
        self.config = config
        self.skill = load_skill("route_analysis")

    def analyze_route(self, route_data: RouteData) -> List[POI]:
        """Analyze route and select 10 POIs

        Args:
            route_data: Route information

        Returns:
            List of POI objects (up to 10)

        Raises:
            AgentError: If analysis fails
        """

        logger.info(f"Analyzing route: {route_data.origin_name} → {route_data.destination_name}")

        # Format skill prompt
        prompt = self.skill.format(
            origin=route_data.origin_name,
            destination=route_data.destination_name,
            distance_km=route_data.distance_km,
            waypoints_count=len(route_data.waypoints),
            landmarks=", ".join(route_data.landmarks[:10]) if route_data.landmarks else "None"
        )

        try:
            # Call Claude CLI
            response = call_claude_cli(
                prompt,
                model=self.config.claude.model,
                max_tokens=self.config.claude.max_tokens,
                temperature=self.config.claude.temperature,
                timeout=self.config.claude.subprocess_timeout
            )

            # Parse JSON response
            pois = self._parse_response(response)

            logger.info(f"Found {len(pois)} POIs")
            return pois

        except Exception as e:
            logger.error(f"Route analysis failed: {e}")
            raise AgentError(f"Route analysis failed: {e}")

    def _parse_response(self, response: str) -> List[POI]:
        """Parse Claude's JSON response into POI objects"""

        # Extract JSON from response (handle code blocks)
        if "```json" in response:
            json_start = response.index("```json") + 7
            json_end = response.index("```", json_start)
            json_str = response[json_start:json_end].strip()
        elif "```" in response:
            json_start = response.index("```") + 3
            json_end = response.index("```", json_start)
            json_str = response[json_start:json_end].strip()
        else:
            json_str = response.strip()

        try:
            data = json.loads(json_str)
            pois_data = data.get("pois", [])

            pois = []
            for poi_data in pois_data[:10]:  # Limit to 10
                poi = POI(
                    id=str(uuid.uuid4()),
                    name=poi_data["name"],
                    coordinates=(poi_data["coordinates"][0], poi_data["coordinates"][1]),
                    description=poi_data["description"],
                    category=POICategory(poi_data["category"]),
                    distance_from_start_km=poi_data["distance_from_start_km"],
                    estimated_time_seconds=int(poi_data.get("estimated_time_seconds", 0)),
                    metadata={}
                )
                pois.append(poi)

            return pois

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse POIs: {e}\nResponse: {response}")
            raise AgentError(f"Invalid POI response from Claude: {e}")
```

**Acceptance Criteria**:
- Returns 10 well-distributed POIs for Tel Aviv → Jerusalem
- Handles short routes (< 20 km) with fewer POIs
- Validates POI data (coordinates, category)
- Logs analysis process

**Test Command**:
```bash
uv run pytest tests/unit/test_route_analyzer.py -v
```

**Commit Message**: `feat: add route analyzer agent`

---

## Phase 4: Base Agent Framework (Week 2-3)

### Task 4.1: Implement Base Content Agent Class
**Description**: Abstract base class for YouTube/Spotify/History agents

**Files to Create**:
- `src/tour_guide/agents/base.py` - Base agent class
- `tests/unit/test_base_agent.py` - Tests

**Base Agent** (`src/tour_guide/agents/base.py`):
```python
from abc import ABC, abstractmethod
from typing import Any, Optional
import time
import logging
from multiprocessing import Queue
from tour_guide.core.types import POI, ContentResult, AgentType, ResultStatus
from tour_guide.core.exceptions import AgentError

logger = logging.getLogger(__name__)

class BaseContentAgent(ABC):
    """Abstract base class for content agents"""

    def __init__(
        self,
        agent_type: AgentType,
        config,
        poi_queue: Queue,
        content_queue: Queue
    ):
        self.agent_type = agent_type
        self.config = config
        self.poi_queue = poi_queue
        self.content_queue = content_queue
        self.logger = logging.getLogger(f"agent.{agent_type.value}")

    def run(self):
        """Main worker loop - runs in separate process"""

        self.logger.info(f"{self.agent_type.value} agent started (PID: {os.getpid()})")

        while True:
            try:
                # Get POI from queue (blocking with timeout)
                poi = self.poi_queue.get(timeout=5)

                # Poison pill - terminate
                if poi is None:
                    self.logger.info(f"{self.agent_type.value} agent received poison pill, exiting")
                    break

                # Process POI
                result = self._process_poi(poi)

                # Put result in content queue
                self.content_queue.put(result)

            except Empty:
                # Queue empty, continue waiting
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error in {self.agent_type.value} agent: {e}", exc_info=True)
                # Continue processing next POI

        self.logger.info(f"{self.agent_type.value} agent finished")

    def _process_poi(self, poi: POI) -> ContentResult:
        """Process a single POI"""

        start_time = time.time()
        self.logger.info(f"Processing POI: {poi.name} ({poi.id})")

        try:
            # Call agent-specific content generation
            with timeout(self.config.agents.content_agent_timeout):
                content = self.generate_content(poi)
                score = self.calculate_relevance_score(poi, content)

            execution_time = time.time() - start_time

            result = ContentResult(
                agent_type=self.agent_type,
                poi_id=poi.id,
                content=content,
                relevance_score=score,
                execution_time_seconds=execution_time,
                status=ResultStatus.SUCCESS,
                error_message=None
            )

            self.logger.info(
                f"Successfully processed {poi.name}: score={score:.1f}, time={execution_time:.1f}s",
                extra={"poi_id": poi.id, "relevance_score": score, "execution_time": execution_time}
            )

            return result

        except TimeoutError:
            execution_time = time.time() - start_time
            self.logger.warning(f"Timeout processing {poi.name} after {execution_time:.1f}s")

            return ContentResult(
                agent_type=self.agent_type,
                poi_id=poi.id,
                content=None,
                relevance_score=0.0,
                execution_time_seconds=execution_time,
                status=ResultStatus.TIMEOUT,
                error_message=f"Timeout after {self.config.agents.content_agent_timeout}s"
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed to process {poi.name}: {e}")

            return ContentResult(
                agent_type=self.agent_type,
                poi_id=poi.id,
                content=None,
                relevance_score=0.0,
                execution_time_seconds=execution_time,
                status=ResultStatus.FAILURE,
                error_message=str(e)
            )

    @abstractmethod
    def generate_content(self, poi: POI) -> Any:
        """Generate content for POI - implemented by subclasses"""
        pass

    @abstractmethod
    def calculate_relevance_score(self, poi: POI, content: Any) -> float:
        """Calculate relevance score (0-100) - implemented by subclasses"""
        pass
```

**Acceptance Criteria**:
- Can be subclassed by content agents
- Handles timeouts correctly
- Returns error results instead of crashing
- Logs all activities

**Test Command**:
```bash
uv run pytest tests/unit/test_base_agent.py -v
```

**Commit Message**: `feat: add base content agent class`

---

## Phase 5: Content Agents (Week 3-4)

### Task 5.1: Implement YouTube Agent
**Description**: Agent that finds relevant videos for a POI

**Files to Create**:
- `src/tour_guide/agents/youtube_agent.py` - YouTube agent
- `src/tour_guide/skills/youtube_search.skill` - YouTube skill
- `tests/unit/test_youtube_agent.py` - Tests

**YouTube Skill** (`src/tour_guide/skills/youtube_search.skill`):
```
You are a YouTube content curator. Find 3 relevant videos for the following location.

**Location Information:**
- Name: $poi_name
- Description: $poi_description
- Category: $poi_category

**Task:**
Generate 3 YouTube video suggestions that would be interesting for someone visiting this location. Focus on:
- Historical documentaries
- Travel guides
- Cultural features
- Local stories

**Output Format (JSON only):**
{
  "videos": [
    {
      "title": "The Siege of Masada: Ancient Israel's Last Stand",
      "channel": "History Documentaries HD",
      "duration_minutes": 12,
      "url": "https://youtube.com/watch?v=example",
      "description": "Documentary about the famous siege of Masada in 73 CE",
      "relevance_score": 95.0
    }
  ]
}

Return ONLY the JSON, no other text.
```

**YouTube Agent** (`src/tour_guide/agents/youtube_agent.py`):
```python
from dataclasses import dataclass
from typing import List
import json
from tour_guide.agents.base import BaseContentAgent
from tour_guide.core.types import POI, AgentType
from tour_guide.utils.claude_cli import call_claude_cli
from tour_guide.skills.loader import load_skill
import logging

logger = logging.getLogger(__name__)

@dataclass
class VideoSuggestion:
    title: str
    channel: str
    duration_minutes: int
    url: str
    description: str
    relevance_score: float

@dataclass
class VideoContent:
    videos: List[VideoSuggestion]
    search_query: str

class YouTubeAgent(BaseContentAgent):
    """Agent that finds relevant YouTube videos"""

    def __init__(self, config, poi_queue, content_queue):
        super().__init__(AgentType.YOUTUBE, config, poi_queue, content_queue)
        self.skill = load_skill("youtube_search")

    def generate_content(self, poi: POI) -> VideoContent:
        """Generate video suggestions for POI"""

        prompt = self.skill.format(
            poi_name=poi.name,
            poi_description=poi.description,
            poi_category=poi.category.value
        )

        response = call_claude_cli(
            prompt,
            model=self.config.claude.model,
            timeout=15
        )

        # Parse response
        data = self._parse_response(response)

        videos = [
            VideoSuggestion(
                title=v["title"],
                channel=v["channel"],
                duration_minutes=v["duration_minutes"],
                url=v["url"],
                description=v["description"],
                relevance_score=v["relevance_score"]
            )
            for v in data["videos"]
        ]

        return VideoContent(
            videos=videos,
            search_query=f"{poi.name} history documentary"
        )

    def calculate_relevance_score(self, poi: POI, content: VideoContent) -> float:
        """Calculate average relevance score"""
        if not content.videos:
            return 0.0
        return sum(v.relevance_score for v in content.videos) / len(content.videos)

    def _parse_response(self, response: str) -> dict:
        """Parse Claude JSON response"""
        # Extract JSON (handle code blocks)
        if "```json" in response:
            start = response.index("```json") + 7
            end = response.index("```", start)
            json_str = response[start:end].strip()
        else:
            json_str = response.strip()

        return json.loads(json_str)
```

**Acceptance Criteria**:
- Returns 3 video suggestions for any POI
- Suggestions are relevant to location
- Handles Claude failures gracefully

**Test Command**:
```bash
uv run pytest tests/unit/test_youtube_agent.py -v
```

**Commit Message**: `feat: add YouTube agent`

---

### Task 5.2: Implement Spotify Agent
**Description**: Agent that finds relevant music for a POI

**Files to Create**:
- `src/tour_guide/agents/spotify_agent.py` - Spotify agent
- `src/tour_guide/skills/music_search.skill` - Music skill
- `tests/unit/test_spotify_agent.py` - Tests

**Music Skill** (`src/tour_guide/skills/music_search.skill`):
```
You are a music curator. Suggest 3 songs/albums related to the following location.

**Location Information:**
- Name: $poi_name
- Description: $poi_description
- Category: $poi_category
- Coordinates: $coordinates

**Task:**
Suggest music that connects to this location through:
- Local musical traditions
- Songs about the place
- Historical era music
- Regional artists
- Thematic connections

**Output Format (JSON only):**
{
  "suggestions": [
    {
      "title": "Jerusalem of Gold",
      "artist": "Naomi Shemer",
      "type": "song",
      "genre": "Israeli folk",
      "year": 1967,
      "duration_minutes": 4,
      "relevance_explanation": "Iconic Israeli song about Jerusalem, known worldwide",
      "relevance_score": 98.0
    }
  ]
}

Return ONLY the JSON, no other text.
```

**Implementation**: Similar to YouTube agent but returns MusicContent

**Commit Message**: `feat: add Spotify agent`

---

### Task 5.3: Implement History Agent
**Description**: Agent that generates historical narratives for a POI

**Files to Create**:
- `src/tour_guide/agents/history_agent.py` - History agent
- `src/tour_guide/skills/history_narrative.skill` - History skill
- `tests/unit/test_history_agent.py` - Tests

**History Skill** (`src/tour_guide/skills/history_narrative.skill`):
```
You are a historian and storyteller. Write an engaging historical narrative about this location.

**Location Information:**
- Name: $poi_name
- Description: $poi_description
- Category: $poi_category

**Requirements:**
- Length: 300-500 words
- Style: Engaging narrative (not dry facts)
- Include: Specific dates, people, events
- Connect: Local history to broader context
- Format: Story-like (beginning, middle, end)

**Output Format (JSON only):**
{
  "title": "The Siege of Masada: 73 CE",
  "narrative": "In the year 73 CE, high atop a desert plateau overlooking the Dead Sea, a group of Jewish rebels made their final stand against the Roman Empire...",
  "key_facts": [
    "Built by Herod the Great between 37-31 BCE",
    "Last stronghold to fall in the First Jewish-Roman War",
    "960 rebels chose death over slavery"
  ],
  "time_period": "1st Century CE",
  "historical_figures": ["Eleazar ben Ya'ir", "Flavius Silva"],
  "sources": ["Josephus - The Jewish War"],
  "relevance_score": 95.0
}

Return ONLY the JSON, no other text.
```

**Implementation**: Similar structure, returns HistoryContent with narrative

**Commit Message**: `feat: add History agent`

---

## Phase 6: Judge Agent (Week 4)

### Task 6.1: Implement Judge Agent
**Description**: Agent that evaluates and selects best content from the three content agents

**Files to Create**:
- `src/tour_guide/agents/judge_agent.py` - Judge agent
- `src/tour_guide/skills/content_evaluation.skill` - Evaluation skill
- `tests/unit/test_judge_agent.py` - Tests

**Judge Skill** (`src/tour_guide/skills/content_evaluation.skill`):
```
You are a content evaluation expert. Evaluate these content options and select the BEST one for travelers visiting this location.

**Location:**
- Name: $poi_name
- Category: $poi_category

**Content Options:**

1. **YouTube Video:**
$youtube_summary

2. **Spotify Music:**
$spotify_summary

3. **Historical Narrative:**
$history_summary

**Evaluation Criteria:**
- Relevance to POI (40%)
- Educational value (30%)
- Entertainment value (20%)
- Content quality (10%)

**Task:**
1. Evaluate each option
2. Assign score (0-100)
3. Select the BEST option
4. Explain reasoning (2-3 sentences)

**Output Format (JSON only):**
{
  "selected_agent": "history",
  "reasoning": "The historical narrative provides unique insights into the siege of Masada with specific dates and people, offering high educational value that complements the dramatic location.",
  "scores": {
    "youtube": 78.0,
    "spotify": 65.0,
    "history": 92.0
  }
}

Return ONLY the JSON, no other text.
```

**Judge Agent** (`src/tour_guide/agents/judge_agent.py`):
```python
from dataclasses import dataclass
from typing import Dict
import json
from tour_guide.core.types import POI, ContentResult, AgentType
from tour_guide.utils.claude_cli import call_claude_cli
from tour_guide.skills.loader import load_skill
import logging

logger = logging.getLogger(__name__)

@dataclass
class JudgmentResult:
    poi_id: str
    selected_agent: AgentType
    selected_content: Any
    reasoning: str
    scores: Dict[AgentType, float]
    evaluation_time_seconds: float

class JudgeAgent:
    """Agent that evaluates content and selects the best"""

    def __init__(self, config):
        self.config = config
        self.skill = load_skill("content_evaluation")

    def judge_content(
        self,
        poi: POI,
        youtube_result: ContentResult,
        spotify_result: ContentResult,
        history_result: ContentResult
    ) -> JudgmentResult:
        """Evaluate three content results and select best"""

        logger.info(f"Judging content for POI: {poi.name}")

        # Check which agents succeeded
        candidates = []
        if youtube_result.status == ResultStatus.SUCCESS:
            candidates.append(("youtube", youtube_result))
        if spotify_result.status == ResultStatus.SUCCESS:
            candidates.append(("spotify", spotify_result))
        if history_result.status == ResultStatus.SUCCESS:
            candidates.append(("history", history_result))

        # Handle edge cases
        if not candidates:
            return self._handle_all_failed(poi, youtube_result, spotify_result, history_result)

        if len(candidates) == 1:
            return self._handle_single_candidate(poi, candidates[0])

        # Use Claude to evaluate
        prompt = self._build_prompt(poi, youtube_result, spotify_result, history_result)

        response = call_claude_cli(
            prompt,
            model=self.config.claude.model,
            timeout=self.config.agents.judge_agent_timeout
        )

        # Parse judgment
        judgment = self._parse_response(response)

        # Get selected content
        result_map = {
            AgentType.YOUTUBE: youtube_result,
            AgentType.SPOTIFY: spotify_result,
            AgentType.HISTORY: history_result
        }

        selected_agent = AgentType(judgment["selected_agent"])
        selected_content = result_map[selected_agent].content

        return JudgmentResult(
            poi_id=poi.id,
            selected_agent=selected_agent,
            selected_content=selected_content,
            reasoning=judgment["reasoning"],
            scores=judgment["scores"],
            evaluation_time_seconds=0.0  # TODO: track
        )
```

**Acceptance Criteria**:
- Selects best content for each POI
- Handles cases where agents fail
- Provides clear reasoning

**Test Command**:
```bash
uv run pytest tests/unit/test_judge_agent.py -v
```

**Commit Message**: `feat: add Judge agent`

---

## Phase 7: Queue and Parallel Processing (Week 4-5)

### Task 7.1: Implement Queue Manager
**Description**: Manages creation and lifecycle of all queues

**Files to Create**:
- `src/tour_guide/queue/manager.py` - Queue manager
- `tests/unit/test_queue_manager.py` - Tests

**Commit Message**: `feat: add queue manager`

---

### Task 7.2: Implement Parallel Executor
**Description**: Spawns and manages content agent processes

**Files to Create**:
- `src/tour_guide/parallel/executor.py` - Parallel executor
- `tests/unit/test_parallel_executor.py` - Tests

**Commit Message**: `feat: add parallel executor`

---

### Task 7.3: Integrate Queue with Agents
**Description**: Connect full pipeline via queues

**Files to Modify**: Agents, executor

**Commit Message**: `feat: integrate queue-based agent communication`

---

## Phase 8: Output System (Week 5)

### Task 8.1: Implement Rich CLI Display
**Description**: Formatted terminal output with progress bars

**Files to Create**:
- `src/tour_guide/output/cli_display.py` - Rich CLI
- `tests/unit/test_cli_display.py` - Tests

**Commit Message**: `feat: add Rich CLI display`

---

### Task 8.2: Implement JSON Export
**Description**: Export results to JSON file

**Files to Create**:
- `src/tour_guide/output/json_exporter.py` - JSON export
- `src/tour_guide/output/schemas.py` - JSON schema
- `tests/unit/test_json_export.py` - Tests

**Commit Message**: `feat: add JSON export`

---

### Task 8.3: Implement Markdown Report
**Description**: Generate human-readable Markdown report

**Files to Create**:
- `src/tour_guide/output/markdown_generator.py` - Markdown generator
- `tests/unit/test_markdown_generator.py` - Tests

**Commit Message**: `feat: add Markdown report generator`

---

## Phase 9: Self-Diagnosis System (Week 5-6)

### Task 9.1: Implement Log Parser
**Description**: Parse and analyze JSON log files

**Files to Create**:
- `src/tour_guide/diagnosis/parser.py` - Log parser
- `tests/unit/test_log_parser.py` - Tests

**Commit Message**: `feat: add log parser`

---

### Task 9.2: Implement Diagnostic Analyzer
**Description**: Use Claude to analyze logs

**Files to Create**:
- `src/tour_guide/diagnosis/analyzer.py` - Analyzer
- `src/tour_guide/skills/log_diagnosis.skill` - Diagnosis skill
- `tests/unit/test_diagnostic_analyzer.py` - Tests

**Commit Message**: `feat: add diagnostic analyzer`

---

### Task 9.3: Add Diagnose CLI Command
**Description**: Add `tour-guide diagnose` command

**Files to Modify**: `src/tour_guide/cli/main.py`

**Commit Message**: `feat: add diagnose CLI command`

---

## Phase 10: Integration and Polish (Week 6-7)

### Task 10.1: Implement Main Orchestrator
**Description**: Main coordinator that ties everything together

**Files to Create**:
- `src/tour_guide/orchestrator.py` - Orchestrator
- `tests/integration/test_orchestrator.py` - Integration tests

**Commit Message**: `feat: add main orchestrator`

---

### Task 10.2: Implement Main CLI
**Description**: Complete CLI with all commands

**Files to Create**:
- `src/tour_guide/cli/main.py` - CLI commands

**CLI Commands**:
```bash
tour-guide route <origin> <destination> [OPTIONS]
tour-guide diagnose [OPTIONS]
tour-guide --version
tour-guide --help
```

**Commit Message**: `feat: complete CLI implementation`

---

### Task 10.3: Run All Test Routes
**Description**: Test with all 10 Israeli routes

**Files to Create**:
- `tests/integration/test_all_routes.py` - All route tests

**Test Routes**:
1. Tel Aviv → Jerusalem
2. Haifa → Akko
3. Tel Aviv → Eilat
4. Jerusalem → Dead Sea
5. Nazareth → Tiberias
6. Tel Aviv → Caesarea
7. Beer Sheva → Masada
8. Haifa → Rosh Hanikra
9. Jerusalem → Bethlehem
10. Tel Aviv → Jaffa

**Commit Message**: `test: validate all 10 test routes`

---

### Task 10.4: Final Documentation
**Description**: Update README.md with complete instructions

**Files to Modify**:
- `README.md` - User guide
- `CONTRIBUTING.md` - Developer guide

**README sections**:
- Installation
- Quick Start
- Usage Examples
- Configuration
- Troubleshooting

**Commit Message**: `docs: finalize README with usage instructions`

---

## Summary Checklist

### Phase 1: Project Foundation (4 tasks) ✓
- [ ] Task 1.1: Initialize UV Project
- [ ] Task 1.2: Create Package Structure
- [ ] Task 1.3: Implement Configuration Management
- [ ] Task 1.4: Implement Logging System

### Phase 2: Routing System (3 tasks) ✓
- [ ] Task 2.1: Implement OSRM Client
- [ ] Task 2.2: Implement Claude Fallback Router
- [ ] Task 2.3: Implement Route Planner

### Phase 3: Route Analyzer (2 tasks) ✓
- [ ] Task 3.1: Implement Skills Framework
- [ ] Task 3.2: Implement Route Analyzer Agent

### Phase 4: Base Agent Framework (1 task) ✓
- [ ] Task 4.1: Implement Base Content Agent Class

### Phase 5: Content Agents (3 tasks) ✓
- [ ] Task 5.1: Implement YouTube Agent
- [ ] Task 5.2: Implement Spotify Agent
- [ ] Task 5.3: Implement History Agent

### Phase 6: Judge Agent (1 task) ✓
- [ ] Task 6.1: Implement Judge Agent

### Phase 7: Queue and Parallel Processing (3 tasks) ✓
- [ ] Task 7.1: Implement Queue Manager
- [ ] Task 7.2: Implement Parallel Executor
- [ ] Task 7.3: Integrate Queue with Agents

### Phase 8: Output System (3 tasks) ✓
- [ ] Task 8.1: Implement Rich CLI Display
- [ ] Task 8.2: Implement JSON Export
- [ ] Task 8.3: Implement Markdown Report

### Phase 9: Self-Diagnosis (3 tasks) ✓
- [ ] Task 9.1: Implement Log Parser
- [ ] Task 9.2: Implement Diagnostic Analyzer
- [ ] Task 9.3: Add Diagnose CLI Command

### Phase 10: Integration and Polish (4 tasks) ✓
- [ ] Task 10.1: Implement Main Orchestrator
- [ ] Task 10.2: Implement Main CLI
- [ ] Task 10.3: Run All Test Routes
- [ ] Task 10.4: Final Documentation

---

**Total Tasks**: 28
**Estimated Duration**: 6-7 weeks for solo developer
**Completion Strategy**: Commit after each task, test continuously, iterate on feedback

---

## Development Guidelines

### Commit Message Format
```
<type>: <description>

Types:
- feat: New feature
- fix: Bug fix
- test: Add tests
- docs: Documentation
- refactor: Code refactoring
- style: Code style changes
- chore: Maintenance tasks
```

### Testing Strategy
- Write tests BEFORE implementation (TDD)
- Run tests after each task
- Aim for 80%+ coverage
- Use mocks for external services (OSRM, Claude CLI)

### Code Quality
- Follow PEP 8 (enforced by ruff)
- Add type hints to all functions
- Write docstrings for public APIs
- Keep functions small and focused

### Progress Tracking
- Check off tasks as completed
- Update this document with any deviations
- Note any blocked tasks or dependencies

---

**Document Version**: 1.0
**Last Updated**: 2025-12-02
**Status**: Ready for Implementation

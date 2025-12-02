# Tour Guide 🗺️

**Transform your road trips into engaging, AI-curated learning experiences**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

**Tour Guide** is a multi-agent AI system that automatically discovers and curates entertaining, educational content about points of interest along any road trip route. Simply provide an origin and destination, and Tour Guide will:

- Analyze your route and identify the 10 most interesting locations
- Generate relevant content for each location using three specialized AI agents working in parallel
- Intelligently select the best content (videos, music, or historical narratives) for each point of interest
- Present everything in a beautiful, animated CLI experience with optional JSON and Markdown exports

The system uses **no external API keys** (except Claude CLI which you authenticate once), leverages free OSRM routing, and employs sophisticated multiprocessing to analyze routes in under 2 minutes. Perfect for travelers, educators, content creators, and developers interested in multi-agent AI systems.

**Key Innovation**: A judge agent evaluates content from YouTube, Spotify, and History agents, selecting the single best piece of content for each location based on relevance, educational value, and quality. The entire system is fault-tolerant, with comprehensive logging and self-diagnosis capabilities.

---

## Features

- 🚗 **Free Route Planning**: Uses OSRM (no API keys needed) with automatic Claude fallback
- 🤖 **5 AI Agents**: Route Analyzer, YouTube, Spotify, History, and Judge agents working together
- ⚡ **Parallel Processing**: Content agents run simultaneously using multiprocessing
- 📺 **YouTube Integration**: Finds relevant documentary and travel videos for each location
- 🎵 **Music Recommendations**: Suggests local music, folk songs, and thematic playlists
- 📖 **Historical Narratives**: Generates engaging 300-500 word stories about each location
- ⚖️ **Intelligent Selection**: Judge agent picks the best content using AI evaluation
- 🎨 **Rich CLI**: Beautiful terminal interface with progress bars and animated journey
- 📁 **Multiple Exports**: JSON (for APIs) and Markdown (for reports)
- 🔍 **Self-Diagnosis**: Analyze logs to automatically identify and fix issues
- 📝 **Comprehensive Logging**: JSON-formatted logs with rotation and per-agent tracking
- 🛡️ **Fault Tolerant**: Continues with partial results even if agents fail

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER: "Tel Aviv → Jerusalem"             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│ STAGE 1: Route Planning (OSRM → Claude fallback)          │
│ Output: RouteData with waypoints                           │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│ STAGE 2: Route Analysis (Claude)                          │
│ Output: 10 Points of Interest (POIs)                      │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│ STAGE 3: Content Discovery (Parallel)                     │
│                                                            │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│    │   YouTube    │  │   Spotify    │  │   History    │  │
│    │    Agent     │  │    Agent     │  │    Agent     │  │
│    │  (Process 1) │  │  (Process 2) │  │  (Process 3) │  │
│    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│           │                 │                 │           │
│           └─────────────────┴─────────────────┘           │
│                      30 Content Results                    │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│ STAGE 4: Content Judging (Claude)                         │
│ Output: Best content selected for each POI                │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│ STAGE 5: Output                                           │
│ - Rich CLI (animated, 5-second delays)                    │
│ - JSON export (structured data)                           │
│ - Markdown report (human-readable)                        │
└────────────────────────────────────────────────────────────┘

Total Duration: ~90-120 seconds (without animation delays)
```

---

## Installation

### Prerequisites

Before installing Tour Guide, ensure you have:

1. **Python 3.10 or higher**
   ```bash
   python --version  # Should show 3.10+
   ```

2. **UV package manager** (recommended) or pip
   ```bash
   uv --version  # If not installed, see below
   ```

3. **Claude CLI** (required for AI agents)
   ```bash
   claude --version  # If not installed, see below
   ```

### Step 1: Install UV Package Manager

UV is a fast Python package manager. Install it:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
```

### Step 2: Install Claude CLI

```bash
# Using pip
pip install anthropic-cli

# Authenticate (one-time setup)
claude auth login
```

Follow the prompts to authenticate with your Anthropic API key.

### Step 3: Install Tour Guide

```bash
# Clone the repository
git clone https://github.com/DVIRO44/llmcourse-hw4-google-maps.git
cd llmcourse-hw4-google-maps

# Install dependencies
uv sync

# Verify installation
uv run tour-guide --version
```

### Alternative: Install Without UV

If you prefer using pip:

```bash
git clone https://github.com/DVIRO44/llmcourse-hw4-google-maps.git
cd llmcourse-hw4-google-maps
pip install -e .

# Verify installation
tour-guide --version
```

---

## Quick Start

### Basic Usage

Plan a tour from Tel Aviv to Jerusalem:

```bash
uv run tour-guide route "Tel Aviv" "Jerusalem"
```

This will:
1. ✅ Plan the route using OSRM
2. ✅ Analyze route and find 10 interesting POIs
3. ✅ Generate content for each POI (parallel processing)
4. ✅ Judge and select the best content
5. ✅ Display animated journey in terminal (5-second delays)

### Skip Animation (Fast Mode)

For quick results without delays:

```bash
uv run tour-guide route "Tel Aviv" "Jerusalem" --no-animation
```

### Export Results

Export to JSON and Markdown:

```bash
uv run tour-guide route "Tel Aviv" "Jerusalem" \
    --json-output output/journey.json \
    --markdown-output output/report.md
```

### Use Coordinates

You can also use coordinates instead of place names:

```bash
uv run tour-guide route "32.0853,34.7818" "31.7683,35.2137"
```

### Customize Number of POIs

Select 5 POIs instead of the default 10:

```bash
uv run tour-guide route "Haifa" "Akko" --poi-count 5
```

### Diagnose Issues

If agents are failing or routes are slow:

```bash
# Analyze all logs from last 24 hours
uv run tour-guide diagnose

# Analyze specific agent
uv run tour-guide diagnose --agent youtube

# Analyze last 50 log entries
uv run tour-guide diagnose --last 50

# Save diagnostic report
uv run tour-guide diagnose --output diagnosis.md
```

---

## CLI Reference

### Commands

#### `tour-guide route <origin> <destination>`

Plan a tour guide journey between two locations.

**Arguments:**
- `origin` - Starting location (place name or "lat,lon")
- `destination` - Ending location (place name or "lat,lon")

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--json-output PATH` | `-j` | Export results to JSON file | None |
| `--markdown-output PATH` | `-m` | Generate Markdown report | None |
| `--no-animation` | | Skip 5-second delays between POIs | False |
| `--poi-count N` | `-n` | Number of POIs to select | 10 |
| `--config PATH` | `-c` | Path to custom config file | config/default.yaml |
| `--log-level LEVEL` | `-l` | Log level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `--verbose` | `-v` | Enable verbose output | False |
| `--quiet` | `-q` | Suppress progress bars | False |

**Examples:**

```bash
# Basic usage
uv run tour-guide route "Tel Aviv" "Jerusalem"

# With all options
uv run tour-guide route "Tel Aviv" "Jerusalem" \
    --json-output results.json \
    --markdown-output report.md \
    --no-animation \
    --poi-count 8 \
    --verbose

# Using coordinates
uv run tour-guide route "32.0853,34.7818" "31.7683,35.2137"

# Custom config
uv run tour-guide route "Haifa" "Akko" --config my_config.yaml
```

#### `tour-guide diagnose`

Analyze logs and identify issues with agents or routing.

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--hours N` | | Analyze logs from last N hours | 24 |
| `--agent NAME` | `-a` | Focus on specific agent (youtube, spotify, history, judge) | all |
| `--last N` | `-n` | Analyze last N log entries | 100 |
| `--output PATH` | `-o` | Save diagnostic report to file | None |
| `--verbose` | `-v` | Show detailed analysis | False |

**Examples:**

```bash
# Basic diagnosis
uv run tour-guide diagnose

# Analyze specific agent
uv run tour-guide diagnose --agent youtube

# Last 6 hours only
uv run tour-guide diagnose --hours 6

# Save to file
uv run tour-guide diagnose --output diagnosis.md
```

#### `tour-guide --version`

Show version information.

#### `tour-guide --help`

Show help message with all commands and options.

---

## Configuration

### Configuration File

Tour Guide uses YAML configuration files. The default config is at `config/default.yaml`.

**Create Custom Config** (`config/my_config.yaml`):

```yaml
# Logging Configuration
logging:
  level: INFO                 # DEBUG, INFO, WARNING, ERROR, CRITICAL
  max_bytes: 10485760        # 10 MB - log file size before rotation
  backup_count: 5            # Keep 5 backup log files
  format: json               # json or text
  log_dir: ./logs
  enable_console: true       # Also log to console

# Routing Configuration
routing:
  osrm_url: "http://router.project-osrm.org"
  fallback_to_claude: true   # Use Claude if OSRM fails
  timeout_seconds: 10        # OSRM request timeout
  max_retries: 2             # Number of retries

# Agent Configuration
agents:
  content_agent_timeout: 30  # Seconds before content agent times out
  judge_agent_timeout: 10    # Seconds before judge agent times out
  max_retries: 2             # Agent retry attempts
  enable_parallel_execution: true

  # YouTube Agent Settings
  youtube:
    max_videos: 3
    prefer_documentary: true
    min_duration_minutes: 3
    max_duration_minutes: 20

  # Spotify Agent Settings
  spotify:
    max_suggestions: 3
    prefer_local_music: true
    include_modern: false    # Prefer historical music

  # History Agent Settings
  history:
    min_words: 300
    max_words: 500
    include_sources: true
    narrative_style: engaging  # or "academic"

  # Judge Agent Settings
  judge:
    evaluation_criteria:
      relevance_weight: 0.4
      educational_value_weight: 0.3
      entertainment_value_weight: 0.2
      quality_weight: 0.1
    default_preference:
      - history
      - youtube
      - spotify

# Claude CLI Configuration
claude:
  model: "claude-sonnet-4"   # Claude model to use
  max_tokens: 4000           # Maximum tokens per request
  temperature: 0.7           # Temperature (0.0-1.0)
  subprocess_timeout: 15     # Subprocess timeout

# Output Configuration
output:
  journey_delay_seconds: 5   # Delay between POIs in CLI
  enable_progress_bar: true
  enable_colors: true
  default_json_path: ./output/journey.json
  default_markdown_path: ./output/journey.md

# POI Configuration
poi:
  count: 10                  # Number of POIs to select
  min_distance_between_km: 5 # Minimum distance between POIs
  categories:
    - historical
    - cultural
    - natural
    - religious
    - entertainment
  distribution_algorithm: even_spread  # or "density_based"

# Queue Configuration
queues:
  poi_queue_size: 10
  content_queue_size: 30
  results_queue_size: 10
  use_bounded_queues: true

# System Configuration
system:
  overall_timeout: 180       # 3 minutes - overall system timeout
  force_continue: false      # Continue even if many POIs fail
  verbose_errors: true       # Show detailed error messages
```

**Use Custom Config:**

```bash
uv run tour-guide route "Tel Aviv" "Jerusalem" --config config/my_config.yaml
```

### Environment Variables

Override configuration values with environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `TOUR_GUIDE_LOG_LEVEL` | Log level | `DEBUG` |
| `TOUR_GUIDE_LOG_DIR` | Log directory | `/var/log/tour_guide` |
| `TOUR_GUIDE_OSRM_URL` | OSRM server URL | `http://localhost:5000` |
| `TOUR_GUIDE_CLAUDE_MODEL` | Claude model | `claude-opus-4` |
| `TOUR_GUIDE_OUTPUT_DIR` | Output directory | `./results` |
| `TOUR_GUIDE_CONFIG_PATH` | Config file path | `./my_config.yaml` |

**Example:**

```bash
export TOUR_GUIDE_LOG_LEVEL=DEBUG
export TOUR_GUIDE_CLAUDE_MODEL=claude-opus-4
uv run tour-guide route "Tel Aviv" "Jerusalem"
```

---

## Output Examples

### Rich CLI Output

```
╔══════════════════════════════════════════════════════════════╗
║           TOUR GUIDE: Tel Aviv → Jerusalem                  ║
╚══════════════════════════════════════════════════════════════╝

Route Information:
  Distance: 65.3 km
  Duration: 1h 15m
  POIs: 10

Stage 1: Route Planning ████████████████████████ 100%
Stage 2: Route Analysis ████████████████████████ 100%
Stage 3: Content Discovery ████████████████████████ 100%
Stage 4: Judging ████████████████████████ 100%

┌──────────────────────────────────────────────────────────────┐
│ POI 1/10: Latrun Monastery                                   │
│ Category: Religious | 25.5 km from start                     │
├──────────────────────────────────────────────────────────────┤
│ Trappist monastery famous for its wine production and        │
│ peaceful grounds. Established in 1890.                       │
│                                                              │
│ 🎵 SELECTED: Music Recommendation                            │
│                                                              │
│ ♪ "Shir LaShalom" - Israeli Peace Song                      │
│   Artist: Various Artists                                    │
│   Genre: Israeli folk                                        │
│   Relevance: Reflects the peaceful monastic atmosphere       │
└──────────────────────────────────────────────────────────────┘

[5 second delay...]

┌──────────────────────────────────────────────────────────────┐
│ POI 2/10: Mini Israel                                        │
│ Category: Entertainment | 32.1 km from start                 │
├──────────────────────────────────────────────────────────────┤
│ Miniature park featuring 1:25 scale models of famous         │
│ Israeli landmarks and buildings.                             │
│                                                              │
│ 📺 SELECTED: YouTube Video                                   │
│                                                              │
│ "Mini Israel: A Journey Through Time"                       │
│ Channel: Travel Israel HD                                    │
│ Duration: 8 minutes                                          │
│ https://youtube.com/watch?v=...                              │
└──────────────────────────────────────────────────────────────┘

...

╔══════════════════════════════════════════════════════════════╗
║                      JOURNEY COMPLETE                        ║
╚══════════════════════════════════════════════════════════════╝

Summary Statistics:
  ✓ POIs Processed: 10/10
  ✓ Content Type Distribution:
    - Videos: 4
    - Music: 3
    - History: 3
  ✓ Total Execution Time: 95 seconds
  ✓ Success Rate: 100%

Exports:
  📁 JSON: output/journey.json
  📄 Markdown: output/report.md
```

### JSON Export Structure

```json
{
  "metadata": {
    "version": "1.0.0",
    "timestamp": "2025-12-02T14:30:45Z",
    "execution_time_seconds": 95.3
  },
  "route": {
    "origin": "Tel Aviv",
    "destination": "Jerusalem",
    "origin_coords": [32.0853, 34.7818],
    "destination_coords": [31.7683, 35.2137],
    "distance_km": 65.3,
    "duration_seconds": 4500,
    "data_source": "osrm"
  },
  "pois": [
    {
      "id": "uuid-1234",
      "name": "Latrun Monastery",
      "coordinates": [31.8367, 34.9839],
      "description": "Trappist monastery famous for its wine production...",
      "category": "religious",
      "distance_from_start_km": 25.5
    }
  ],
  "judgments": [
    {
      "poi_id": "uuid-1234",
      "selected_agent": "spotify",
      "selected_content": {
        "suggestions": [
          {
            "title": "Shir LaShalom",
            "artist": "Various Artists",
            "genre": "Israeli folk",
            "relevance_score": 88.0
          }
        ]
      },
      "reasoning": "Music recommendation reflects peaceful monastic atmosphere",
      "scores": {
        "youtube": 75.0,
        "spotify": 88.0,
        "history": 82.0
      }
    }
  ],
  "execution_stats": {
    "total_time_seconds": 95.3,
    "routing_time": 8.2,
    "analysis_time": 9.5,
    "content_discovery_time": 65.1,
    "judging_time": 12.5,
    "success_rate": 1.0
  }
}
```

### Markdown Report Example

```markdown
# Tour Guide Report: Tel Aviv → Jerusalem

**Generated**: 2025-12-02 14:30:45 UTC
**Duration**: 95 seconds

---

## Route Overview

- **Origin**: Tel Aviv (32.0853, 34.7818)
- **Destination**: Jerusalem (31.7683, 35.2137)
- **Distance**: 65.3 km
- **Estimated Duration**: 1 hour 15 minutes
- **Data Source**: OSRM

---

## Points of Interest

### 1. Latrun Monastery 🙏
**Category**: Religious | **Distance from start**: 25.5 km

Trappist monastery famous for its wine production and peaceful grounds. Established in 1890 by French monks.

**Selected Content: Music** 🎵

- **Title**: Shir LaShalom (Song for Peace)
- **Artist**: Various Artists
- **Genre**: Israeli folk
- **Relevance**: Reflects the peaceful monastic atmosphere and historical significance

**Why This Content?**
Music recommendation reflects peaceful monastic atmosphere and connects to the location's spiritual significance.

---

### 2. Mini Israel 🎭
**Category**: Entertainment | **Distance from start**: 32.1 km

Miniature park featuring 1:25 scale models of famous Israeli landmarks and buildings.

**Selected Content: YouTube Video** 📺

- **Title**: Mini Israel: A Journey Through Time
- **Channel**: Travel Israel HD
- **Duration**: 8 minutes
- **Link**: [Watch on YouTube](https://youtube.com/watch?v=...)

**Why This Content?**
Video provides comprehensive overview of the park and showcases the impressive miniature replicas.

---

## Summary Statistics

- **Total POIs**: 10
- **Content Distribution**:
  - Videos: 4 (40%)
  - Music: 3 (30%)
  - Historical Narratives: 3 (30%)
- **Success Rate**: 100%
- **Execution Time**: 95 seconds

---

## Appendix: All Content Options

<details>
<summary>Click to see all content generated for each POI</summary>

### POI 1: Latrun Monastery

**YouTube Option** (Score: 75.0)
- Video 1: "Latrun Monastery History"
- Video 2: "Wine Making at Latrun"

**Spotify Option** (Score: 88.0) ✓ SELECTED
- Song 1: "Shir LaShalom"

**History Option** (Score: 82.0)
- Narrative about Trappist monks...

</details>

---

**Generated with Tour Guide AI System**
```

---

## Test Routes

Tour Guide includes 10 pre-configured Israeli test routes for validation:

| # | Route | Distance | Terrain | POI Density |
|---|-------|----------|---------|-------------|
| 1 | Tel Aviv → Jerusalem | ~65 km | Urban to historic | High |
| 2 | Haifa → Akko | ~20 km | Coastal cities | High |
| 3 | Tel Aviv → Eilat | ~350 km | Desert, long distance | Low |
| 4 | Jerusalem → Dead Sea | ~40 km | Mountain to lowest point | Medium |
| 5 | Nazareth → Tiberias | ~35 km | Religious sites, sea | High |
| 6 | Tel Aviv → Caesarea | ~50 km | Coastal, Roman ruins | Medium |
| 7 | Beer Sheva → Masada | ~90 km | Desert, historic fortress | Low |
| 8 | Haifa → Rosh Hanikra | ~35 km | Coastal, grottoes | Medium |
| 9 | Jerusalem → Bethlehem | ~10 km | Religious, very short | High |
| 10 | Tel Aviv → Jaffa | ~5 km | Urban, very short | Very High |

### Run Individual Test Routes

```bash
# Route 1: Tel Aviv to Jerusalem
uv run tour-guide route "Tel Aviv" "Jerusalem"

# Route 3: Long distance route
uv run tour-guide route "Tel Aviv" "Eilat"

# Route 9: Short route
uv run tour-guide route "Jerusalem" "Bethlehem"
```

### Run All Test Routes (Automated)

```bash
# Run all 10 test routes
uv run pytest tests/integration/test_routes.py -v

# Run with detailed output
uv run pytest tests/integration/test_routes.py -v -s
```

---

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/DVIRO44/llmcourse-hw4-google-maps.git
cd llmcourse-hw4-google-maps

# Install with dev dependencies
uv sync --dev

# Verify setup
uv run pytest --version
uv run ruff --version
```

### Project Structure

```
llmcourse-hw4-google-maps/
├── src/
│   └── tour_guide/              # Main package
│       ├── __init__.py          # Package initialization
│       ├── __main__.py          # CLI entry point
│       ├── cli/                 # CLI commands
│       │   ├── main.py
│       │   └── options.py
│       ├── core/                # Core business logic
│       │   ├── orchestrator.py  # Main coordinator
│       │   ├── types.py         # Data classes
│       │   └── exceptions.py    # Custom exceptions
│       ├── agents/              # Agent implementations
│       │   ├── base.py          # Base agent class
│       │   ├── route_analyzer.py
│       │   ├── youtube_agent.py
│       │   ├── spotify_agent.py
│       │   ├── history_agent.py
│       │   └── judge_agent.py
│       ├── routing/             # Routing system
│       │   ├── osrm_client.py   # OSRM API client
│       │   ├── claude_router.py # Claude fallback
│       │   └── planner.py       # Main planner
│       ├── skills/              # Prompt templates
│       │   ├── loader.py
│       │   ├── route_analysis.skill
│       │   ├── youtube_search.skill
│       │   ├── music_search.skill
│       │   ├── history_narrative.skill
│       │   └── content_evaluation.skill
│       ├── queue/               # Queue management
│       │   └── manager.py
│       ├── logging_/            # Logging system
│       │   ├── setup.py
│       │   └── formatters.py
│       ├── output/              # Output formatters
│       │   ├── cli_display.py   # Rich CLI
│       │   ├── json_exporter.py
│       │   └── markdown_generator.py
│       ├── diagnosis/           # Self-diagnosis
│       │   ├── parser.py
│       │   └── analyzer.py
│       ├── config/              # Configuration
│       │   └── settings.py
│       └── utils/               # Utilities
│           ├── claude_cli.py
│           ├── retry.py
│           └── timeout.py
│
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   │   ├── test_config.py
│   │   ├── test_routing.py
│   │   ├── test_agents.py
│   │   └── test_output.py
│   ├── integration/             # Integration tests
│   │   ├── test_routes.py
│   │   └── test_end_to_end.py
│   └── fixtures/                # Test fixtures
│       └── mock_responses.py
│
├── config/                      # Configuration files
│   └── default.yaml
│
├── logs/                        # Log files (gitignored)
├── output/                      # Output files (gitignored)
│
├── docs/                        # Documentation
│   ├── PRD.md                   # Product requirements
│   ├── DESIGN.md                # Architecture design
│   └── TASKS.md                 # Implementation tasks
│
├── pyproject.toml               # Project metadata
├── uv.lock                      # Dependency lock file
├── README.md                    # This file
├── LICENSE                      # MIT License
└── .gitignore                   # Git ignore patterns
```

### Run Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=tour_guide --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_routing.py -v

# Run specific test
uv run pytest tests/unit/test_routing.py::test_osrm_client -v

# Run integration tests only
uv run pytest tests/integration/ -v

# Run with verbose output
uv run pytest -v -s
```

### Code Quality

```bash
# Format code with ruff
uv run ruff format .

# Check code style
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check . --fix

# Type checking with mypy
uv run mypy src/tour_guide
```

### Build Package

```bash
# Build distribution
uv build

# Install locally in editable mode
uv pip install -e .
```

### View Coverage Report

```bash
# Generate HTML coverage report
uv run pytest --cov=tour_guide --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## How It Works

### 1. Route Planning (Stage 1)

The system first retrieves routing information between the origin and destination:

- **Primary**: Uses OSRM (Open Source Routing Machine) - a free, open-source routing engine
- **Fallback**: If OSRM fails (network issues, timeout), automatically falls back to Claude-generated routes
- **Output**: RouteData object with waypoints, distance, duration, and landmarks

**Why OSRM?** No API keys required, self-hostable, good global coverage, and fast response times.

### 2. Route Analysis (Stage 2)

The Route Analyzer agent uses Claude CLI to intelligently select the 10 most interesting POIs:

- Analyzes waypoints and landmarks from the route
- Applies selection criteria: historical significance, cultural importance, natural features, tourist popularity
- Ensures geographic distribution (POIs spaced evenly, minimum 5 km apart)
- Returns 10 POI objects with coordinates, descriptions, and categories

### 3. Parallel Content Discovery (Stage 3)

Three specialized agents work **simultaneously** using Python multiprocessing:

**YouTube Agent**:
- Generates search queries for each POI
- Finds relevant videos (documentaries, travel guides, cultural features)
- Returns top 3 video suggestions with relevance scores

**Spotify Agent**:
- Identifies music connected to the location (local traditions, songs about the place, historical era)
- Returns top 3 music suggestions with explanations

**History Agent**:
- Generates engaging historical narratives (300-500 words)
- Story format with specific dates, people, events
- Connects local history to broader context

**Key Innovation**: All three agents process the same 10 POIs in parallel, dramatically reducing execution time (3x speedup vs sequential).

### 4. Content Judging (Stage 4)

The Judge agent evaluates all content options and selects the best one for each POI:

- Receives 3 content results per POI (YouTube, Spotify, History)
- Uses Claude to evaluate based on:
  - Relevance to POI (40% weight)
  - Educational value (30%)
  - Entertainment value (20%)
  - Content quality (10%)
- Selects **exactly one** content type per POI
- Provides reasoning for each selection

**Graceful Degradation**: If agents fail, Judge still makes best selection from available content.

### 5. Output (Stage 5)

Results are presented in multiple formats:

**Rich CLI**:
- Progress bars for each stage
- Animated journey with 5-second delays between POIs
- Formatted boxes showing POI details and selected content
- Summary statistics (success rate, content distribution)

**JSON Export** (optional):
- Complete structured data for APIs
- Includes all metadata, route info, POIs, judgments, execution stats
- Schema-validated for consistency

**Markdown Report** (optional):
- Human-readable narrative format
- Embedded links for videos/music
- Full historical narratives
- Appendix with all content options

---

## Troubleshooting

### Common Issues

#### 1. Claude CLI Not Found

**Error**: `ClaudeError: Claude CLI not found`

**Solution**:
```bash
# Install Claude CLI
pip install anthropic-cli

# Authenticate
claude auth login

# Verify
claude --version
```

#### 2. OSRM Timeout or Connection Error

**Error**: `OSRMError: OSRM request timed out`

**What Happens**: System automatically falls back to Claude-generated routes.

**If You Want to Use Your Own OSRM Server**:
```yaml
# config/settings.yaml
routing:
  osrm_url: "http://localhost:5000"  # Your OSRM server
```

#### 3. Agent Timeouts

**Error**: Agents timing out frequently (status: timeout)

**Solution 1 - Increase Timeout**:
```yaml
# config/settings.yaml
agents:
  content_agent_timeout: 45  # Increase from 30 to 45 seconds
```

**Solution 2 - Check Claude CLI**:
```bash
# Test Claude CLI directly
claude "Hello, world"

# If slow, check your internet connection or Anthropic API status
```

**Solution 3 - Use Diagnose**:
```bash
uv run tour-guide diagnose --agent youtube
```

#### 4. All Agents Failing

**Error**: `All agents failed for POI`

**Solution**:
```bash
# Enable verbose logging
uv run tour-guide route "Tel Aviv" "Jerusalem" --log-level DEBUG --verbose

# Check logs
cat logs/tour_guide_*.log | grep ERROR

# Run diagnosis
uv run tour-guide diagnose
```

#### 5. Import Errors

**Error**: `ModuleNotFoundError: No module named 'tour_guide'`

**Solution**:
```bash
# Reinstall package
uv sync

# Or install in editable mode
uv pip install -e .

# Verify
uv run python -c "import tour_guide; print(tour_guide.__version__)"
```

#### 6. Permission Denied for Logs Directory

**Error**: `PermissionError: [Errno 13] Permission denied: 'logs/tour_guide.log'`

**Solution**:
```bash
# Create logs directory with correct permissions
mkdir -p logs
chmod 755 logs

# Or change log directory in config
export TOUR_GUIDE_LOG_DIR=/tmp/tour_guide_logs
```

#### 7. Multiprocessing Issues on macOS

**Error**: `RuntimeError: context has already been set`

**Solution**: This is a known issue with multiprocessing on macOS. The package handles it automatically, but if you still see issues:

```python
# In your Python environment
import multiprocessing
multiprocessing.set_start_method('spawn', force=True)
```

#### 8. Rate Limiting from Claude API

**Error**: `ClaudeError: Rate limit exceeded`

**Solution**:
```yaml
# config/settings.yaml
agents:
  max_retries: 3  # Increase retries
  content_agent_timeout: 60  # Give more time

claude:
  temperature: 0.5  # Lower temperature might speed up responses
```

### Getting Help

If you encounter issues not covered here:

1. **Check Logs**: Enable debug logging with `--log-level DEBUG`
2. **Run Diagnosis**: `uv run tour-guide diagnose` analyzes logs automatically
3. **Search Issues**: Check [GitHub Issues](https://github.com/DVIRO44/llmcourse-hw4-google-maps/issues)
4. **Create Issue**: Open a new issue with:
   - Error message
   - Log file excerpt
   - Steps to reproduce
   - Python version, OS

---

## Performance Tuning

### Speed Optimization

To reduce execution time:

```yaml
# config/settings.yaml
agents:
  content_agent_timeout: 20  # Reduce from 30
  enable_parallel_execution: true  # Always enabled

poi:
  count: 5  # Fewer POIs = faster

output:
  journey_delay_seconds: 0  # No delays
```

### Quality Optimization

For better content quality:

```yaml
# config/settings.yaml
claude:
  model: "claude-opus-4"  # More powerful model
  temperature: 0.3  # Lower temperature for more factual content

agents:
  content_agent_timeout: 60  # More time for quality
  youtube:
    prefer_documentary: true
    min_duration_minutes: 5  # Longer, higher-quality videos
```

---

## Contributing

Contributions are welcome! Here's how to contribute:

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/llmcourse-hw4-google-maps.git
cd llmcourse-hw4-google-maps
```

### 2. Create Feature Branch

```bash
git checkout -b feature/my-new-feature
```

### 3. Make Changes

- Follow the coding style (PEP 8)
- Add tests for new features
- Update documentation if needed

### 4. Run Tests

```bash
# Run all tests
uv run pytest

# Check code style
uv run ruff check .

# Format code
uv run ruff format .
```

### 5. Commit and Push

```bash
git add .
git commit -m "feat: add my new feature"
git push origin feature/my-new-feature
```

### 6. Create Pull Request

- Open PR on GitHub
- Describe changes clearly
- Link related issues

### Contribution Guidelines

- **Code Style**: Follow PEP 8, use ruff for formatting
- **Tests**: Add tests for new features (aim for 80%+ coverage)
- **Documentation**: Update README.md, docstrings, and comments
- **Commits**: Use conventional commit messages (feat:, fix:, docs:, etc.)
- **Issues**: Check existing issues before creating new ones

---

## Roadmap

### Planned Features (Future Versions)

- [ ] **v1.1**: Real-time GPS integration during actual driving
- [ ] **v1.2**: Web interface for non-CLI users
- [ ] **v1.3**: Support for multiple languages (i18n)
- [ ] **v1.4**: Caching of Claude responses to reduce API calls
- [ ] **v1.5**: Spotify API integration for actual playback
- [ ] **v1.6**: Image/photo discovery for POIs
- [ ] **v1.7**: Custom agent plugins (user-defined agents)
- [ ] **v2.0**: Mobile app (iOS/Android)

See [TASKS.md](TASKS.md) for detailed implementation tasks.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Private use allowed
- ⚠️ Liability and warranty not provided

---

## Acknowledgments

### Technologies Used

- **[OSRM](http://project-osrm.org/)** - Free, open-source routing engine
- **[Claude AI](https://www.anthropic.com/claude)** - Anthropic's AI assistant for agent intelligence
- **[UV](https://github.com/astral-sh/uv)** - Fast Python package manager
- **[Rich](https://github.com/Textualize/rich)** - Beautiful terminal formatting
- **Python Multiprocessing** - Parallel agent execution

### Inspiration

This project was created as a university assignment for an LLM course, demonstrating:
- Multi-agent AI systems
- Parallel processing with Python
- Queue-based communication patterns
- Fault-tolerant design
- Self-diagnosis capabilities

### University Course

Part of the LLM course curriculum at [University Name], focusing on practical applications of large language models in multi-agent systems.

---

## Documentation

For more detailed information, see:

- **[PRD.md](PRD.md)** - Product Requirements Document (what we're building and why)
- **[DESIGN.md](DESIGN.md)** - Architecture and Design Document (how it works)
- **[TASKS.md](TASKS.md)** - Implementation Tasks (step-by-step build guide)
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution Guidelines

---

## Contact

- **GitHub**: [DVIRO44](https://github.com/DVIRO44)
- **Repository**: [llmcourse-hw4-google-maps](https://github.com/DVIRO44/llmcourse-hw4-google-maps)
- **Issues**: [Report a Bug](https://github.com/DVIRO44/llmcourse-hw4-google-maps/issues)

---

<div align="center">

**Built with ❤️ for travelers and AI enthusiasts**

[⬆ Back to Top](#tour-guide-)

</div>

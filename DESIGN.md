# Architecture and Design Document: Tour Guide AI System

## Document Information

**Version**: 1.0
**Last Updated**: 2025-12-02
**Status**: Design Approved
**Related**: PRD.md

---

## 1. System Architecture Overview

### Architectural Style

Tour Guide follows a **multi-agent, queue-based, parallel processing** architecture with the following key characteristics:

- **Multi-Agent System**: Five specialized agents (Route Analyzer, YouTube, Spotify, History, Judge) work independently
- **Queue-Based Communication**: Agents communicate exclusively via bounded queues (no direct function calls)
- **Parallel Processing**: Content agents execute concurrently using Python multiprocessing
- **Fault Isolation**: Agent failures are contained and don't cascade to other components
- **Graceful Degradation**: System continues with partial results when agents fail

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TOUR GUIDE AI SYSTEM                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   CLI User   │
│   Interface  │
└──────┬───────┘
       │
       ├── tour-guide route <origin> <destination>
       ├── tour-guide diagnose
       └── tour-guide --help
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATOR                                       │
│  - Main coordinator and workflow manager                                    │
│  - Spawns and manages all agents and queues                                 │
│  - Handles timeouts and process lifecycle                                   │
└────┬────────────────────────────────────────────────────────────────────┬───┘
     │                                                                     │
     ▼                                                                     ▼
┌─────────────────┐                                              ┌──────────────┐
│  ROUTE PLANNER  │                                              │    LOGGER    │
│  - OSRM Client  │                                              │  - Rotation  │
│  - Claude Fallbk│◄─────────────────────────────────────────────┤  - JSON fmt  │
└────┬────────────┘                                              │  - Diagnosis │
     │                                                           └──────────────┘
     │ RouteData
     ▼
┌─────────────────┐
│ ROUTE ANALYZER  │
│  AGENT          │
│  - Claude CLI   │
│  - POI Selector │
└────┬────────────┘
     │
     │ List[POI] (10 items)
     ▼
┌──────────────────────────────────────────────────────────────┐
│                       POI QUEUE                              │
│  (multiprocessing.Queue, bounded size=10)                    │
└────┬────────────────────────────────────────────────────┬────┘
     │                          │                          │
     ▼                          ▼                          ▼
┌──────────┐              ┌──────────┐              ┌──────────┐
│ YOUTUBE  │              │ SPOTIFY  │              │ HISTORY  │
│  AGENT   │              │  AGENT   │              │  AGENT   │
│ (Process)│              │ (Process)│              │ (Process)│
└────┬─────┘              └────┬─────┘              └────┬─────┘
     │                         │                         │
     └─────────────────────────┼─────────────────────────┘
                               │ ContentResult[]
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    CONTENT QUEUE                             │
│  (multiprocessing.Queue, bounded size=30)                    │
└────┬─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────┐
│  JUDGE AGENT    │
│  - Claude CLI   │
│  - Evaluator    │
└────┬────────────┘
     │
     │ JudgmentResult[]
     ▼
┌──────────────────────────────────────────────────────────────┐
│                    RESULTS QUEUE                             │
│  (multiprocessing.Queue, bounded size=10)                    │
└────┬─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                  OUTPUT FORMATTER                            │
│  - Rich CLI (progress bars, animations)                     │
│  - JSON Exporter (schema validation)                        │
│  - Markdown Generator (formatted reports)                   │
└─────────────────────────────────────────────────────────────┘

External Dependencies:
┌──────────────┐      ┌──────────────┐
│ OSRM Service │      │  Claude CLI  │
│ (HTTP API)   │      │ (subprocess) │
└──────────────┘      └──────────────┘
```

---

## 2. Component Architecture

### Data Flow Pipeline

```
USER INPUT (origin, destination)
    │
    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: ROUTE PLANNING                                                  │
│ Duration: ~5-10 seconds                                                   │
└───────────────────────────────────────────────────────────────────────────┘
    │
    │ Try OSRM
    ├──────────► [OSRM Success] ──► RouteData
    │                  │
    │                  │ [OSRM Failure]
    │                  ▼
    └──────────► [Claude Fallback] ──► RouteData
    │
    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: ROUTE ANALYSIS                                                  │
│ Duration: ~10 seconds                                                     │
└───────────────────────────────────────────────────────────────────────────┘
    │
    │ RouteData (waypoints, landmarks, directions)
    ▼
[Route Analyzer Agent]
    │ - Uses Claude CLI
    │ - Selects 10 interesting POIs
    │ - Applies distribution algorithm
    │
    │ POI[] (10 items)
    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: CONTENT DISCOVERY (PARALLEL)                                    │
│ Duration: ~30-60 seconds                                                  │
└───────────────────────────────────────────────────────────────────────────┘
    │
    │ FOR EACH POI (10 iterations):
    │
    ├─────────────────────┬─────────────────────┬─────────────────────┐
    │                     │                     │                     │
    ▼                     ▼                     ▼                     ▼
[YouTube Agent]     [Spotify Agent]     [History Agent]
Process #1          Process #2          Process #3
    │                     │                     │
    │ VideoResult         │ MusicResult         │ HistoryResult
    └─────────────────────┴─────────────────────┴──────────┐
                                                            │
                          3 results per POI × 10 POIs = 30 results
                                                            │
                                                            ▼
                                                    [Content Queue]
                                                            │
┌───────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: JUDGING                                                          │
│ Duration: ~5-10 seconds                                                   │
└───────────────────────────────────────────────────────────────────────────┘
    │
    │ FOR EACH POI (10 iterations):
    │   - Collect 3 content results (YouTube, Spotify, History)
    │   - Evaluate with Claude CLI
    │   - Select best content
    │
    ▼
[Judge Agent]
    │
    │ JudgmentResult[] (10 items)
    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ STAGE 5: OUTPUT                                                           │
│ Duration: ~50 seconds (with 5s delays) or instant (--no-animation)       │
└───────────────────────────────────────────────────────────────────────────┘
    │
    ├─────► [Rich CLI Display]
    │         - Progress bars
    │         - Animated journey (5s delays)
    │         - Summary statistics
    │
    ├─────► [JSON Export]
    │         - Full data structure
    │         - Schema validation
    │
    └─────► [Markdown Report]
              - Formatted narrative
              - Embedded links

TOTAL DURATION: ~90-120 seconds (without animation delays)
```

---

## 3. Component Specifications (Building Blocks)

### 3.1 Orchestrator

**Purpose**: Main coordinator that manages the entire workflow, spawns processes, manages queues, and handles the overall lifecycle of the tour guide journey.

**Input Data**:
```python
@dataclass
class OrchestratorInput:
    origin: str              # "Tel Aviv" or "32.0853,34.7818"
    destination: str         # "Jerusalem" or "31.7683,35.2137"
    config: Config          # Loaded from config.yaml
    cli_options: CLIOptions # --json-output, --no-animation, etc.
```

**Output Data**:
```python
@dataclass
class OrchestratorOutput:
    journey: Journey                    # Complete journey data
    execution_stats: ExecutionStats    # Timing, success rates
    errors: List[ErrorReport]          # Any errors encountered
```

**Setup Data**:
```yaml
orchestrator:
  overall_timeout_seconds: 180  # 3 minutes
  enable_progress_bar: true
  enable_logging: true
```

**Dependencies**:
- Route Planner
- Route Analyzer Agent
- Queue Manager
- Content Agent Pool
- Judge Agent
- Output Formatter
- Logger

**Error Handling**:
- **Timeout**: Kill all child processes, return partial results
- **Critical Failure**: Log error, display user-friendly message, exit gracefully
- **Partial Failure**: Continue with available results (e.g., 8/10 POIs succeeded)

**Workflow**:
1. Load configuration
2. Initialize logger
3. Create queues (POI, Content, Results)
4. Execute Route Planner
5. Execute Route Analyzer Agent
6. Spawn Content Agent Pool (3 processes)
7. Spawn Judge Agent
8. Collect results from Results Queue
9. Execute Output Formatter
10. Cleanup (join processes, close queues)

---

### 3.2 Route Planner

**Purpose**: Retrieves routing information from OSRM, with automatic fallback to Claude CLI if OSRM fails. Handles geocoding (place names → coordinates) and route data parsing.

**Input Data**:
```python
@dataclass
class RoutePlannerInput:
    origin: str       # Place name or "lat,long"
    destination: str  # Place name or "lat,long"
    config: RoutingConfig
```

**Output Data**:
```python
@dataclass
class RouteData:
    origin_coords: Tuple[float, float]      # (lat, long)
    destination_coords: Tuple[float, float]
    origin_name: str
    destination_name: str
    distance_km: float
    duration_seconds: int
    waypoints: List[Waypoint]               # 20+ waypoints
    landmarks: List[str]                    # Named locations
    steps: List[RouteStep]                  # Turn-by-turn directions
    data_source: str                        # "osrm" or "claude"

@dataclass
class Waypoint:
    lat: float
    long: float
    distance_from_start_km: float
```

**Setup Data**:
```yaml
routing:
  osrm_url: "http://router.project-osrm.org"
  fallback_to_claude: true
  timeout_seconds: 10
  max_retries: 2
  cache_enabled: true
  cache_ttl_seconds: 3600
```

**Dependencies**:
- `requests` library (for OSRM HTTP calls)
- Claude CLI subprocess wrapper
- Logger

**Error Handling**:
- **OSRM Timeout**: Retry once, then fallback to Claude
- **OSRM Invalid Response**: Validate JSON schema, fallback to Claude if invalid
- **Geocoding Failure**: Use Claude to convert place names to coordinates
- **Claude Fallback Failure**: Raise `RoutingError`, propagate to Orchestrator
- **Network Error**: Retry with exponential backoff (1s, 2s, 4s)

**Algorithm**:
```python
def plan_route(input: RoutePlannerInput) -> RouteData:
    # 1. Geocode if necessary
    origin_coords = geocode(input.origin)
    dest_coords = geocode(input.destination)

    # 2. Try OSRM
    try:
        route_data = fetch_osrm_route(origin_coords, dest_coords)
        if validate_route_data(route_data):
            return parse_osrm_response(route_data)
    except (OSRMTimeout, OSRMError) as e:
        log.warning(f"OSRM failed: {e}, falling back to Claude")

    # 3. Fallback to Claude
    route_data = fetch_claude_route(origin_coords, dest_coords)
    return parse_claude_response(route_data)
```

---

### 3.3 Route Analyzer Agent

**Purpose**: Intelligent agent that analyzes the complete route and selects exactly 10 points of interest (POIs) based on historical significance, cultural importance, natural landmarks, and geographic distribution.

**Input Data**:
```python
@dataclass
class RouteAnalyzerInput:
    route_data: RouteData
    config: POIConfig
```

**Output Data**:
```python
@dataclass
class POI:
    id: str                              # UUID
    name: str                            # "Masada National Park"
    coordinates: Tuple[float, float]     # (lat, long)
    description: str                     # 2-3 sentences
    category: POICategory               # Enum: historical, cultural, natural, religious, entertainment
    distance_from_start_km: float       # Position along route
    estimated_time_seconds: int         # Time from route start
    metadata: Dict[str, Any]            # Additional data

class RouteAnalyzerOutput:
    pois: List[POI]  # Exactly 10 POIs (or fewer for short routes)
```

**Setup Data**:
```yaml
poi:
  count: 10
  min_distance_between_km: 5
  categories:
    - historical
    - cultural
    - natural
    - religious
    - entertainment
  distribution_algorithm: "even_spread"  # or "density_based"
```

**Dependencies**:
- Claude CLI subprocess wrapper
- Skill: `route_analysis.skill` (prompt template)
- Logger

**Error Handling**:
- **Claude Timeout**: Retry once, return empty list if fails
- **Malformed Response**: Parse partial results, supplement with waypoints
- **Insufficient POIs**: Return all available POIs (< 10)
- **Invalid Coordinates**: Skip invalid POIs, continue with valid ones

**Algorithm**:
```python
def analyze_route(input: RouteAnalyzerInput) -> RouteAnalyzerOutput:
    # 1. Load route analysis skill (prompt template)
    skill = load_skill("route_analysis")

    # 2. Prepare prompt with route data
    prompt = skill.format(
        origin=input.route_data.origin_name,
        destination=input.route_data.destination_name,
        waypoints=input.route_data.waypoints,
        landmarks=input.route_data.landmarks,
        distance_km=input.route_data.distance_km
    )

    # 3. Call Claude CLI
    response = claude_cli_call(prompt, timeout=10)

    # 4. Parse Claude response (JSON format)
    pois = parse_pois_from_response(response)

    # 5. Apply distribution algorithm
    distributed_pois = apply_distribution(pois, algorithm="even_spread")

    # 6. Validate and return top 10
    return RouteAnalyzerOutput(pois=distributed_pois[:10])
```

---

### 3.4 Base Content Agent (Abstract)

**Purpose**: Abstract base class for all content agents (YouTube, Spotify, History). Provides common functionality: queue management, timeout handling, error handling, logging.

**Input Data**:
```python
@dataclass
class ContentAgentInput:
    poi: POI
    config: AgentConfig
    poi_queue: multiprocessing.Queue
    content_queue: multiprocessing.Queue
```

**Output Data**:
```python
@dataclass
class ContentResult:
    agent_type: AgentType        # Enum: youtube, spotify, history
    poi_id: str                  # Reference to POI
    content: Any                 # Agent-specific content
    relevance_score: float       # 0-100
    execution_time_seconds: float
    status: ResultStatus         # Enum: success, failure, timeout
    error_message: Optional[str]
```

**Setup Data**:
```yaml
agents:
  content_agent_timeout: 30
  max_retries: 2
  enable_parallel_execution: true
```

**Dependencies**:
- Claude CLI subprocess wrapper
- Skill loader (prompt templates)
- Logger

**Error Handling**:
- **Timeout (30s)**: Terminate subprocess, return error result
- **Claude Failure**: Retry once, return error result if fails again
- **Invalid Response**: Log warning, return error result with explanation
- **Queue Full**: Block until space available (bounded queue)

**Abstract Methods**:
```python
class BaseContentAgent(ABC):
    @abstractmethod
    def generate_content(self, poi: POI) -> Any:
        """Agent-specific content generation logic"""
        pass

    @abstractmethod
    def calculate_relevance_score(self, poi: POI, content: Any) -> float:
        """Calculate relevance score (0-100)"""
        pass
```

**Worker Loop**:
```python
def run(self):
    """Main worker loop for content agent process"""
    while True:
        try:
            # 1. Get POI from queue (blocking, with timeout)
            poi = self.poi_queue.get(timeout=5)

            if poi is None:  # Poison pill to terminate
                break

            # 2. Generate content (with timeout)
            with timeout(self.config.content_agent_timeout):
                content = self.generate_content(poi)
                score = self.calculate_relevance_score(poi, content)

            # 3. Create result
            result = ContentResult(
                agent_type=self.agent_type,
                poi_id=poi.id,
                content=content,
                relevance_score=score,
                status=ResultStatus.SUCCESS
            )

            # 4. Put result in content queue
            self.content_queue.put(result)

        except TimeoutError:
            # Handle timeout
            result = ContentResult(
                agent_type=self.agent_type,
                poi_id=poi.id,
                status=ResultStatus.TIMEOUT,
                error_message="Agent exceeded 30s timeout"
            )
            self.content_queue.put(result)

        except Exception as e:
            # Handle unexpected errors
            log.error(f"Agent {self.agent_type} failed: {e}")
            result = ContentResult(
                agent_type=self.agent_type,
                poi_id=poi.id,
                status=ResultStatus.FAILURE,
                error_message=str(e)
            )
            self.content_queue.put(result)
```

---

### 3.5 YouTube Agent

**Purpose**: Finds relevant YouTube video content for a POI using Claude CLI to generate search queries and simulate video results.

**Input Data**: Inherits from `BaseContentAgent` (`POI` via queue)

**Output Data**:
```python
@dataclass
class VideoContent:
    videos: List[VideoSuggestion]  # Top 3 videos
    search_query: str              # Query used

@dataclass
class VideoSuggestion:
    title: str                     # "History of Masada Fortress"
    channel: str                   # "Historical Documentaries"
    duration_minutes: int          # 12
    url: str                       # YouTube URL (simulated or real)
    description: str               # Brief description
    view_count: Optional[int]      # Views (if available)
    relevance_score: float         # 0-100
```

**Setup Data**:
```yaml
agents:
  youtube:
    max_videos: 3
    prefer_documentary: true
    min_duration_minutes: 3
    max_duration_minutes: 20
```

**Dependencies**:
- Claude CLI subprocess wrapper
- Skill: `youtube_search.skill`
- Logger

**Error Handling**:
- Same as `BaseContentAgent`
- **No Videos Found**: Return empty list with explanation

**Implementation**:
```python
def generate_content(self, poi: POI) -> VideoContent:
    # 1. Load YouTube search skill
    skill = load_skill("youtube_search")

    # 2. Generate search query using Claude
    prompt = skill.format(
        poi_name=poi.name,
        poi_description=poi.description,
        poi_category=poi.category
    )

    # 3. Call Claude to generate video suggestions
    response = claude_cli_call(prompt, timeout=15)

    # 4. Parse response
    videos = parse_video_suggestions(response)

    return VideoContent(
        videos=videos[:3],
        search_query=f"{poi.name} history documentary"
    )

def calculate_relevance_score(self, poi: POI, content: VideoContent) -> float:
    # Use average of video relevance scores
    if not content.videos:
        return 0.0
    return sum(v.relevance_score for v in content.videos) / len(content.videos)
```

---

### 3.6 Spotify Agent

**Purpose**: Finds relevant music (songs, albums, playlists) for a POI based on local music traditions, historical era, or thematic content.

**Input Data**: Inherits from `BaseContentAgent` (`POI` via queue)

**Output Data**:
```python
@dataclass
class MusicContent:
    suggestions: List[MusicSuggestion]  # Top 3 suggestions
    reasoning: str                       # Why this music is relevant

@dataclass
class MusicSuggestion:
    title: str                           # "Jerusalem of Gold"
    artist: str                          # "Naomi Shemer"
    type: str                            # "song", "album", "playlist"
    genre: str                           # "Israeli folk"
    year: Optional[int]                  # 1967
    duration_minutes: Optional[int]      # 4
    url: str                             # Spotify URL (simulated)
    relevance_explanation: str           # Why relevant to POI
    relevance_score: float               # 0-100
```

**Setup Data**:
```yaml
agents:
  spotify:
    max_suggestions: 3
    prefer_local_music: true
    include_modern: false  # Prefer historical music
```

**Dependencies**:
- Claude CLI subprocess wrapper
- Skill: `music_search.skill`
- Logger

**Error Handling**:
- Same as `BaseContentAgent`
- **No Music Found**: Return general regional music

**Implementation**:
```python
def generate_content(self, poi: POI) -> MusicContent:
    # 1. Load music search skill
    skill = load_skill("music_search")

    # 2. Generate music suggestions using Claude
    prompt = skill.format(
        poi_name=poi.name,
        poi_description=poi.description,
        poi_category=poi.category,
        location_context=f"{poi.coordinates}"
    )

    # 3. Call Claude
    response = claude_cli_call(prompt, timeout=15)

    # 4. Parse response
    suggestions = parse_music_suggestions(response)

    return MusicContent(
        suggestions=suggestions[:3],
        reasoning=f"Music related to {poi.name} and its cultural context"
    )

def calculate_relevance_score(self, poi: POI, content: MusicContent) -> float:
    if not content.suggestions:
        return 0.0
    return sum(s.relevance_score for s in content.suggestions) / len(content.suggestions)
```

---

### 3.7 History Agent

**Purpose**: Generates engaging historical narratives (300-500 words) about a POI, including specific dates, people, events, and connections to broader historical context.

**Input Data**: Inherits from `BaseContentAgent` (`POI` via queue)

**Output Data**:
```python
@dataclass
class HistoryContent:
    title: str                    # "The Siege of Masada: 73 CE"
    narrative: str                # 300-500 word story
    key_facts: List[str]          # Bulleted facts
    time_period: str              # "1st Century CE"
    historical_figures: List[str] # ["Eleazar ben Ya'ir", "Flavius Silva"]
    sources: List[str]            # References (if available)
    reading_time_minutes: int     # Estimated reading time
    relevance_score: float        # 0-100
```

**Setup Data**:
```yaml
agents:
  history:
    min_words: 300
    max_words: 500
    include_sources: true
    narrative_style: "engaging"  # or "academic"
```

**Dependencies**:
- Claude CLI subprocess wrapper
- Skill: `history_narrative.skill`
- Logger

**Error Handling**:
- Same as `BaseContentAgent`
- **Insufficient Historical Data**: Provide general regional history

**Implementation**:
```python
def generate_content(self, poi: POI) -> HistoryContent:
    # 1. Load history narrative skill
    skill = load_skill("history_narrative")

    # 2. Generate historical narrative using Claude
    prompt = skill.format(
        poi_name=poi.name,
        poi_description=poi.description,
        poi_category=poi.category,
        target_words=400
    )

    # 3. Call Claude (longer timeout for narrative generation)
    response = claude_cli_call(prompt, timeout=20)

    # 4. Parse response
    history = parse_history_narrative(response)

    # 5. Calculate reading time
    word_count = len(history.narrative.split())
    reading_time = max(3, word_count // 200)  # 200 words/minute

    return HistoryContent(
        title=history.title,
        narrative=history.narrative,
        key_facts=history.key_facts,
        time_period=history.time_period,
        historical_figures=history.historical_figures,
        sources=history.sources,
        reading_time_minutes=reading_time,
        relevance_score=history.relevance_score
    )

def calculate_relevance_score(self, poi: POI, content: HistoryContent) -> float:
    # History agent provides its own score
    return content.relevance_score
```

---

### 3.8 Judge Agent

**Purpose**: Meta-agent that evaluates outputs from YouTube, Spotify, and History agents and selects the single best content for each POI based on relevance, educational value, entertainment value, and quality.

**Input Data**:
```python
@dataclass
class JudgeInput:
    poi: POI
    youtube_result: ContentResult  # May contain VideoContent or error
    spotify_result: ContentResult  # May contain MusicContent or error
    history_result: ContentResult  # May contain HistoryContent or error
    config: JudgeConfig
```

**Output Data**:
```python
@dataclass
class JudgmentResult:
    poi_id: str
    selected_agent: AgentType          # youtube, spotify, or history
    selected_content: Any              # Content from winning agent
    reasoning: str                     # 2-3 sentences explaining choice
    scores: Dict[AgentType, float]    # Scores for all three agents
    evaluation_time_seconds: float
```

**Setup Data**:
```yaml
agents:
  judge:
    timeout_seconds: 10
    evaluation_criteria:
      relevance_weight: 0.4
      educational_value_weight: 0.3
      entertainment_value_weight: 0.2
      quality_weight: 0.1
    default_preference: ["history", "youtube", "spotify"]  # Tie-breaker
```

**Dependencies**:
- Claude CLI subprocess wrapper
- Skill: `content_evaluation.skill`
- Logger

**Error Handling**:
- **All Agents Failed**: Select least-bad option (highest relevance score, even if error)
- **Timeout**: Use fallback heuristic (prefer history, then youtube, then spotify)
- **Tie**: Use default preference order
- **Claude Failure**: Use weighted scoring heuristic

**Algorithm**:
```python
def judge_content(input: JudgeInput) -> JudgmentResult:
    # 1. Collect all available content
    candidates = []
    if input.youtube_result.status == ResultStatus.SUCCESS:
        candidates.append(("youtube", input.youtube_result))
    if input.spotify_result.status == ResultStatus.SUCCESS:
        candidates.append(("spotify", input.spotify_result))
    if input.history_result.status == ResultStatus.SUCCESS:
        candidates.append(("history", input.history_result))

    # 2. Handle edge case: no successful agents
    if not candidates:
        return handle_all_agents_failed(input)

    # 3. Handle edge case: only one successful agent
    if len(candidates) == 1:
        agent_type, result = candidates[0]
        return JudgmentResult(
            poi_id=input.poi.id,
            selected_agent=agent_type,
            selected_content=result.content,
            reasoning=f"Only {agent_type} agent succeeded",
            scores={agent_type: result.relevance_score}
        )

    # 4. Use Claude to evaluate multiple candidates
    skill = load_skill("content_evaluation")
    prompt = skill.format(
        poi=input.poi,
        youtube_content=input.youtube_result.content if "youtube" in [c[0] for c in candidates] else None,
        spotify_content=input.spotify_result.content if "spotify" in [c[0] for c in candidates] else None,
        history_content=input.history_result.content if "history" in [c[0] for c in candidates] else None
    )

    # 5. Call Claude
    response = claude_cli_call(prompt, timeout=10)

    # 6. Parse judgment
    judgment = parse_judgment(response)

    # 7. Handle tie
    if judgment.is_tie():
        selected = apply_tie_breaker(candidates, config.default_preference)
    else:
        selected = judgment.selected_agent

    return JudgmentResult(
        poi_id=input.poi.id,
        selected_agent=selected,
        selected_content=get_content_for_agent(selected, input),
        reasoning=judgment.reasoning,
        scores=judgment.scores
    )
```

---

### 3.9 Queue Manager

**Purpose**: Manages creation, lifecycle, and cleanup of all multiprocessing queues. Ensures proper bounded queue sizes and provides utilities for queue operations.

**Input Data**:
```python
@dataclass
class QueueManagerConfig:
    poi_queue_size: int = 10
    content_queue_size: int = 30
    results_queue_size: int = 10
```

**Output Data**:
```python
@dataclass
class QueueSet:
    poi_queue: multiprocessing.Queue
    content_queue: multiprocessing.Queue
    results_queue: multiprocessing.Queue
```

**Setup Data**:
```yaml
queues:
  poi_queue_size: 10
  content_queue_size: 30
  results_queue_size: 10
  use_bounded_queues: true
```

**Dependencies**:
- Python `multiprocessing` module
- Logger

**Error Handling**:
- **Queue Full**: Block until space available (or timeout after 30s)
- **Queue Closed**: Detect closed queues, raise `QueueClosedError`
- **Cleanup Failure**: Force-close queues, log warning

**API**:
```python
class QueueManager:
    def create_queues(self, config: QueueManagerConfig) -> QueueSet:
        """Create all queues with bounded sizes"""
        pass

    def close_queues(self, queues: QueueSet):
        """Close all queues (prevents further puts)"""
        pass

    def drain_queue(self, queue: multiprocessing.Queue) -> List[Any]:
        """Drain remaining items from queue"""
        pass

    def send_poison_pills(self, queue: multiprocessing.Queue, count: int):
        """Send None to terminate worker processes"""
        pass
```

---

### 3.10 Logger

**Purpose**: Provides comprehensive logging with rotation, structured JSON format, and self-diagnosis capabilities. Logs all agent activities, errors, and performance metrics.

**Input Data**:
```python
@dataclass
class LogConfig:
    log_level: str              # DEBUG, INFO, WARNING, ERROR, CRITICAL
    max_bytes: int              # 10485760 (10 MB)
    backup_count: int           # 5
    log_format: str             # "json" or "text"
    log_dir: Path               # "./logs"
    enable_console: bool        # Also log to console
```

**Output Data**:
```python
# Structured log entry (JSON format)
{
    "timestamp": "2025-12-02T14:30:45.123Z",
    "level": "INFO",
    "process_id": 12345,
    "agent_name": "youtube_agent",
    "poi_id": "uuid-1234",
    "message": "Content generated successfully",
    "execution_time_seconds": 8.5,
    "metadata": {
        "relevance_score": 85.0,
        "video_count": 3
    }
}
```

**Setup Data**:
```yaml
logging:
  max_bytes: 10485760  # 10 MB
  backup_count: 5
  level: INFO
  format: json
  log_dir: "./logs"
  enable_console: true
  enable_self_diagnosis: true
```

**Dependencies**:
- Python `logging` module
- `logging.handlers.RotatingFileHandler`
- Claude CLI (for self-diagnosis)

**Error Handling**:
- **Disk Full**: Disable file logging, continue with console logging
- **Permission Denied**: Fallback to `/tmp` directory
- **Rotation Failure**: Continue with current log file, log warning

**API**:
```python
class TourGuideLogger:
    def __init__(self, config: LogConfig):
        """Initialize logger with rotation"""
        pass

    def log_agent_start(self, agent_name: str, poi_id: str):
        """Log agent execution start"""
        pass

    def log_agent_complete(self, agent_name: str, poi_id: str,
                          execution_time: float, success: bool):
        """Log agent execution completion"""
        pass

    def log_error(self, component: str, error: Exception, context: Dict):
        """Log error with full context"""
        pass

    def diagnose_logs(self, hours: int = 24) -> DiagnosticReport:
        """Analyze logs and generate diagnostic report"""
        pass
```

**Self-Diagnosis Algorithm**:
```python
def diagnose_logs(self, hours: int = 24) -> DiagnosticReport:
    # 1. Parse log files from last N hours
    log_entries = parse_recent_logs(hours)

    # 2. Extract patterns
    error_frequency = count_errors_by_type(log_entries)
    performance_trends = analyze_execution_times(log_entries)
    agent_reliability = calculate_success_rates(log_entries)

    # 3. Use Claude to analyze patterns
    skill = load_skill("log_diagnosis")
    prompt = skill.format(
        error_frequency=error_frequency,
        performance_trends=performance_trends,
        agent_reliability=agent_reliability
    )

    response = claude_cli_call(prompt, timeout=30)

    # 4. Generate report
    return DiagnosticReport(
        issues=parse_issues(response),
        recommendations=parse_recommendations(response),
        summary_stats=calculate_summary_stats(log_entries)
    )
```

---

### 3.11 Output Formatter

**Purpose**: Formats journey results into three output formats: Rich CLI (with progress bars and animations), JSON (with schema validation), and Markdown (formatted reports).

**Input Data**:
```python
@dataclass
class OutputFormatterInput:
    journey: Journey              # Complete journey data
    execution_stats: ExecutionStats
    cli_options: CLIOptions      # --json-output, --no-animation, etc.
```

**Output Data**:
```python
# Multiple output formats generated simultaneously
- Rich CLI display (to console)
- JSON file (if --json-output specified)
- Markdown file (if --markdown-output specified)
```

**Setup Data**:
```yaml
output:
  journey_delay_seconds: 5
  enable_progress_bar: true
  enable_colors: true
  default_json_path: "./output/journey.json"
  default_markdown_path: "./output/journey.md"
```

**Dependencies**:
- `rich` library (progress bars, tables, panels)
- `jsonschema` (JSON validation)
- Logger

**Error Handling**:
- **File Write Failure**: Retry once, log error if fails
- **Invalid JSON Schema**: Log error, save raw data anyway
- **Terminal Too Small**: Disable fancy formatting, use simple text

**API**:
```python
class OutputFormatter:
    def display_cli(self, journey: Journey, no_animation: bool = False):
        """Display journey in rich CLI format"""
        pass

    def export_json(self, journey: Journey, path: Path):
        """Export journey to JSON file"""
        pass

    def generate_markdown(self, journey: Journey, path: Path):
        """Generate markdown report"""
        pass

    def show_progress(self, stage: str, progress: float):
        """Update progress bar"""
        pass
```

**Rich CLI Display Algorithm**:
```python
def display_cli(self, journey: Journey, no_animation: bool = False):
    # 1. Display header
    console.print(Panel(
        f"[bold]Journey: {journey.origin} → {journey.destination}[/bold]",
        style="blue"
    ))

    # 2. Display route stats
    console.print(f"Distance: {journey.distance_km} km")
    console.print(f"POIs: {len(journey.pois)}")

    # 3. Simulate journey with delays
    for i, (poi, judgment) in enumerate(zip(journey.pois, journey.judgments)):
        # Display POI
        console.print(Panel(
            f"[bold]{poi.name}[/bold]\n{poi.description}",
            title=f"POI {i+1}/10",
            style="green"
        ))

        # Display selected content
        display_content(judgment.selected_content, judgment.selected_agent)

        # Wait 5 seconds (unless --no-animation)
        if not no_animation and i < len(journey.pois) - 1:
            time.sleep(5)

    # 4. Display summary
    display_summary_stats(journey)
```

---

## 4. Data Flow Diagram

### Queue-Based Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW PIPELINE                               │
└──────────────────────────────────────────────────────────────────────────┘

[Orchestrator]
      │
      │ Creates queues
      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    QUEUE INITIALIZATION                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ poi_queue = multiprocessing.Queue(maxsize=10)                          │
│ content_queue = multiprocessing.Queue(maxsize=30)                      │
│ results_queue = multiprocessing.Queue(maxsize=10)                      │
└─────────────────────────────────────────────────────────────────────────┘

[Orchestrator] → [Route Planner] → RouteData
                                        │
                                        ▼
                 [Route Analyzer Agent] ← RouteData
                                        │
                                        │ Produces 10 POIs
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          POI QUEUE                                      │
│  Bounded size: 10                                                       │
│  Type: multiprocessing.Queue                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  [POI #1] [POI #2] [POI #3] ... [POI #10]                             │
└──┬────────────────────┬────────────────────┬───────────────────────────┘
   │                    │                    │
   │ queue.get()        │ queue.get()        │ queue.get()
   ▼                    ▼                    ▼
┌──────────┐      ┌──────────┐      ┌──────────┐
│ YouTube  │      │ Spotify  │      │ History  │
│  Agent   │      │  Agent   │      │  Agent   │
│ Process  │      │ Process  │      │ Process  │
│   #1     │      │   #2     │      │   #3     │
└────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                 │
     │ queue.put()     │ queue.put()     │ queue.put()
     │                 │                 │
     │ VideoResult     │ MusicResult     │ HistoryResult
     │                 │                 │
     └─────────────────┴─────────────────┴──────┐
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       CONTENT QUEUE                                     │
│  Bounded size: 30 (3 results × 10 POIs)                                │
│  Type: multiprocessing.Queue                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  [Result-1a] [Result-1b] [Result-1c] (POI #1)                          │
│  [Result-2a] [Result-2b] [Result-2c] (POI #2)                          │
│  ...                                                                    │
│  [Result-10a] [Result-10b] [Result-10c] (POI #10)                      │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               │ queue.get() in batches of 3
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         JUDGE AGENT                                      │
│  - Groups results by POI (3 results per POI)                            │
│  - Evaluates with Claude CLI                                            │
│  - Selects best content                                                 │
└────────────────────────┬─────────────────────────────────────────────────┘
                         │
                         │ queue.put() for each POI
                         │
                         │ JudgmentResult × 10
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        RESULTS QUEUE                                    │
│  Bounded size: 10                                                       │
│  Type: multiprocessing.Queue                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  [Judgment #1] [Judgment #2] ... [Judgment #10]                        │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               │ queue.get() until empty
                               ▼
                    [Orchestrator collects all results]
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       OUTPUT FORMATTER                                   │
│  - Rich CLI display                                                      │
│  - JSON export                                                           │
│  - Markdown generation                                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

### Message Flow Timing

```
Time (seconds)
    0 ├─► Route Planning (OSRM)
      │
   10 ├─► Route Analysis (Claude CLI)
      │
   20 ├─► POI Queue populated with 10 POIs
      │
      │   ┌── POI #1 → [YouTube | Spotify | History] ──┐
      │   │                                             │
   30 │   ├── POI #2 → [YouTube | Spotify | History] ──┤
      │   │                                             │
   40 │   ├── POI #3 → [YouTube | Spotify | History] ──┤
      │   │                                             ├─► Content Queue
   50 │   ├── POI #4 → [YouTube | Spotify | History] ──┤
      │   │                                             │
   60 │   ├── POI #5 → [YouTube | Spotify | History] ──┤
      │   │                                             │
   70 │   ├── POI #6 → [YouTube | Spotify | History] ──┤
      │   │            (All parallel)                   │
   80 │   ├── POI #7 → [YouTube | Spotify | History] ──┤
      │   │                                             │
   90 │   ├── POI #8 → [YouTube | Spotify | History] ──┤
      │   │                                             │
  100 │   ├── POI #9 → [YouTube | Spotify | History] ──┤
      │   │                                             │
  110 │   └── POI #10 → [YouTube | Spotify | History] ─┘
      │
      │   Content Queue now has ~30 results
      │
  120 ├─► Judge Agent evaluates (10 POIs × 1s each)
      │
  130 ├─► Results Queue populated with 10 judgments
      │
      ├─► Output Formatter (instant)
      │
  180 └─► CLI journey simulation complete (with 5s delays)

Total: ~90-120 seconds (without animation delays)
```

---

## 5. Queue Architecture

### Queue Types and Purposes

| Queue Name      | Max Size | Producer              | Consumer(s)          | Message Type      | Purpose                          |
|-----------------|----------|-----------------------|----------------------|-------------------|----------------------------------|
| POI Queue       | 10       | Route Analyzer Agent  | 3 Content Agents     | POI               | Distribute POIs to workers       |
| Content Queue   | 30       | 3 Content Agents      | Judge Agent          | ContentResult     | Collect all content results      |
| Results Queue   | 10       | Judge Agent           | Orchestrator         | JudgmentResult    | Collect final judgments          |

### Message Formats

**POI Message**:
```python
{
    "id": "uuid-1234",
    "name": "Masada National Park",
    "coordinates": (31.3157, 35.3540),
    "description": "Ancient fortress overlooking the Dead Sea...",
    "category": "historical",
    "distance_from_start_km": 45.2,
    "estimated_time_seconds": 2700
}
```

**ContentResult Message**:
```python
{
    "agent_type": "youtube",  # or "spotify", "history"
    "poi_id": "uuid-1234",
    "content": {
        # Agent-specific content structure
        "videos": [...],  # For YouTube
        "suggestions": [...],  # For Spotify
        "narrative": "...",  # For History
    },
    "relevance_score": 85.0,
    "execution_time_seconds": 8.5,
    "status": "success",  # or "failure", "timeout"
    "error_message": null
}
```

**JudgmentResult Message**:
```python
{
    "poi_id": "uuid-1234",
    "selected_agent": "history",
    "selected_content": {
        # Full content from winning agent
    },
    "reasoning": "Historical narrative provides unique insights...",
    "scores": {
        "youtube": 78.0,
        "spotify": 65.0,
        "history": 92.0
    },
    "evaluation_time_seconds": 4.2
}
```

### Synchronization Strategy

**Producer-Consumer Pattern**:
```
BLOCKING BEHAVIOR:
- Producers: Block when queue is full (put() with timeout)
- Consumers: Block when queue is empty (get() with timeout)

TIMEOUT STRATEGY:
- Queue.put(item, timeout=5): Wait max 5 seconds, raise Full exception
- Queue.get(timeout=5): Wait max 5 seconds, raise Empty exception

POISON PILL TERMINATION:
- Send None to queue to signal workers to terminate
- Each worker checks: if item is None, break loop and exit
```

**Bounded Queue Benefits**:
1. **Memory Control**: Prevents unlimited memory growth
2. **Backpressure**: Slows producers if consumers are overwhelmed
3. **Deadlock Prevention**: Bounded queues with proper timeouts prevent deadlocks

**Queue Lifecycle**:
```python
# 1. Create bounded queues
poi_queue = multiprocessing.Queue(maxsize=10)
content_queue = multiprocessing.Queue(maxsize=30)
results_queue = multiprocessing.Queue(maxsize=10)

# 2. Start consumer processes
youtube_proc = Process(target=youtube_agent.run, args=(poi_queue, content_queue))
spotify_proc = Process(target=spotify_agent.run, args=(poi_queue, content_queue))
history_proc = Process(target=history_agent.run, args=(poi_queue, content_queue))
judge_proc = Process(target=judge_agent.run, args=(content_queue, results_queue))

for proc in [youtube_proc, spotify_proc, history_proc, judge_proc]:
    proc.start()

# 3. Produce POIs
for poi in pois:
    poi_queue.put(poi)

# 4. Send poison pills to content agents
for _ in range(3):
    poi_queue.put(None)

# 5. Wait for content agents to finish
youtube_proc.join()
spotify_proc.join()
history_proc.join()

# 6. Send poison pill to judge agent
content_queue.put(None)

# 7. Wait for judge to finish
judge_proc.join()

# 8. Collect results
results = []
while not results_queue.empty():
    results.append(results_queue.get_nowait())

# 9. Close queues
poi_queue.close()
content_queue.close()
results_queue.close()
```

---

## 6. Parallel Processing Design

### Multiprocessing vs Multithreading

**Decision: Use Multiprocessing**

| Factor               | Multiprocessing           | Multithreading         | Choice        |
|----------------------|---------------------------|------------------------|---------------|
| GIL Limitation       | ✓ Bypasses GIL            | ✗ Limited by GIL       | Multiprocessing |
| CPU-Bound Tasks      | ✓ True parallelism        | ✗ Sequential execution | Multiprocessing |
| I/O-Bound Tasks      | ✓ Works well              | ✓ Works well           | Either        |
| Memory Overhead      | ✗ Higher (separate memory)| ✓ Shared memory        | Acceptable    |
| Fault Isolation      | ✓ Process crashes isolated| ✗ Thread crash = death | Multiprocessing |
| Our Use Case         | Claude CLI subprocesses   | -                      | Multiprocessing |

**Rationale**: Content agents spawn Claude CLI subprocesses (I/O-bound), but we still use multiprocessing for:
1. **Fault Isolation**: If one agent's subprocess hangs, it doesn't block others
2. **True Parallelism**: 3 agents run simultaneously on 3 CPU cores
3. **Timeout Control**: Easier to kill hung processes than threads

### Process Pool Configuration

**Architecture**:
```
┌────────────────────────────────────────────────────────────┐
│                    MAIN PROCESS                            │
│  - Orchestrator                                            │
│  - Route Planner                                           │
│  - Route Analyzer Agent                                    │
│  - Output Formatter                                        │
└──────────────┬─────────────────────────────────────────────┘
               │
               │ Spawns 4 child processes
               │
               ├───────────────┬───────────────┬───────────────┬───────────────┐
               ▼               ▼               ▼               ▼               │
         ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │
         │ YouTube  │    │ Spotify  │    │ History  │    │  Judge   │        │
         │  Agent   │    │  Agent   │    │  Agent   │    │  Agent   │        │
         │ Process  │    │ Process  │    │ Process  │    │ Process  │        │
         └──────────┘    └──────────┘    └──────────┘    └──────────┘        │
               │               │               │               │               │
               │               │               │               │               │
               └── Each spawns Claude CLI subprocesses (up to 10 each) ───────┘

Total processes: 1 (main) + 4 (agents) + up to 40 (Claude CLI) = 45 max
```

**Configuration**:
```python
# Process pool configuration
CONTENT_AGENT_POOL_SIZE = 3  # YouTube, Spotify, History
JUDGE_AGENT_POOL_SIZE = 1    # Single judge agent
MAX_CLAUDE_SUBPROCESSES = 10 # Per agent

# Spawn method (platform-specific)
multiprocessing.set_start_method('spawn')  # Cross-platform compatibility
```

### Worker Lifecycle Management

**Process States**:
```
CREATED → STARTING → RUNNING → [SUCCESS | TIMEOUT | FAILURE] → TERMINATED
```

**Lifecycle Management**:
```python
class AgentProcessManager:
    def spawn_agent(self, agent_class, *args) -> Process:
        """Spawn a new agent process"""
        proc = Process(target=agent_class.run, args=args)
        proc.daemon = False  # Don't die with parent (for cleanup)
        proc.start()
        self.register_process(proc)
        return proc

    def monitor_processes(self, processes: List[Process], timeout: int):
        """Monitor processes and enforce timeout"""
        start_time = time.time()

        while any(p.is_alive() for p in processes):
            # Check timeout
            if time.time() - start_time > timeout:
                log.warning(f"Timeout reached, terminating processes")
                self.terminate_processes(processes)
                break

            # Check for zombies
            for proc in processes:
                if not proc.is_alive() and proc.exitcode is None:
                    log.error(f"Process {proc.pid} is zombie, cleaning up")
                    proc.join(timeout=1)

            time.sleep(0.1)  # Poll every 100ms

        # Join all processes
        for proc in processes:
            proc.join(timeout=1)

    def terminate_processes(self, processes: List[Process]):
        """Gracefully terminate processes"""
        for proc in processes:
            if proc.is_alive():
                proc.terminate()  # SIGTERM

        # Wait for graceful shutdown
        time.sleep(1)

        # Force kill if still alive
        for proc in processes:
            if proc.is_alive():
                log.warning(f"Process {proc.pid} didn't terminate, killing")
                proc.kill()  # SIGKILL

        # Final join
        for proc in processes:
            proc.join(timeout=1)
```

### Timeout Handling

**Timeout Hierarchy**:
```
┌─────────────────────────────────────────────────────────────┐
│ OVERALL SYSTEM TIMEOUT: 180 seconds (3 minutes)            │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐│
│  │ STAGE TIMEOUTS:                                        ││
│  │  - Route Planning: 10s                                 ││
│  │  - Route Analysis: 10s                                 ││
│  │  - Content Discovery: 90s                              ││
│  │  - Judging: 60s                                        ││
│  │  - Output: 10s                                         ││
│  │                                                         ││
│  │  ┌──────────────────────────────────────────────────┐ ││
│  │  │ AGENT TIMEOUTS:                                  │ ││
│  │  │  - Content Agent Process: 30s per POI           │ ││
│  │  │  - Judge Agent Process: 10s per POI             │ ││
│  │  │                                                   │ ││
│  │  │  ┌───────────────────────────────────────────┐  │ ││
│  │  │  │ SUBPROCESS TIMEOUTS:                      │  │ ││
│  │  │  │  - Claude CLI call: 15s                   │  │ ││
│  │  │  │  - OSRM request: 10s                      │  │ ││
│  │  │  └───────────────────────────────────────────┘  │ ││
│  │  └──────────────────────────────────────────────────┘ ││
│  └────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**Timeout Implementation**:
```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds: int):
    """Context manager for timeout enforcement"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    # Set signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Restore old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

# Usage in agent
def generate_content(self, poi: POI) -> Any:
    try:
        with timeout(30):
            return self._generate_content_impl(poi)
    except TimeoutError:
        log.error(f"Agent {self.agent_type} timed out for POI {poi.id}")
        raise
```

---

## 7. Logging Architecture

### Log Levels and Usage

| Level    | When to Use                                      | Examples                                      |
|----------|--------------------------------------------------|-----------------------------------------------|
| DEBUG    | Detailed diagnostic info (dev/troubleshooting)   | Queue sizes, agent inputs/outputs, subprocess calls |
| INFO     | High-level progress (normal operations)          | "POI processed", "Agent completed", "Route planned" |
| WARNING  | Recoverable issues (degraded operation)          | "OSRM timeout, using Claude", "Agent retry #1" |
| ERROR    | Non-fatal errors (operation failed but recoverable) | "Agent failed for POI", "Invalid JSON response" |
| CRITICAL | System failures (unrecoverable, exit required)   | "All agents failed", "Out of memory", "Config missing" |

### Rotation Configuration

**File Naming Pattern**:
```
logs/
├── tour_guide_20251202_143045.log        # Current log
├── tour_guide_20251202_143045.log.1      # First rotation
├── tour_guide_20251202_143045.log.2      # Second rotation
├── tour_guide_20251202_143045.log.3      # Third rotation
├── tour_guide_20251202_143045.log.4      # Fourth rotation
└── tour_guide_20251202_143045.log.5      # Fifth rotation (oldest)
```

**Rotation Triggers**:
- **Size-based**: Rotate when log file reaches 10 MB
- **Automatic backup**: Keep 5 most recent log files
- **Oldest deleted**: When 6th rotation occurs, delete oldest

**Implementation**:
```python
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format log records as JSON"""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "process_id": record.process,
            "agent_name": getattr(record, "agent_name", "unknown"),
            "poi_id": getattr(record, "poi_id", None),
            "message": record.getMessage(),
            "execution_time_seconds": getattr(record, "execution_time", None),
            "metadata": getattr(record, "metadata", {})
        }

        # Include exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

def setup_logger(config: LogConfig) -> logging.Logger:
    """Setup logger with rotation"""
    logger = logging.getLogger("tour_guide")
    logger.setLevel(getattr(logging, config.log_level))

    # Ensure log directory exists
    config.log_dir.mkdir(parents=True, exist_ok=True)

    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = config.log_dir / f"tour_guide_{timestamp}.log"

    # Create rotating file handler
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=config.max_bytes,
        backupCount=config.backup_count
    )

    # Set formatter
    if config.log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(process)d - %(message)s"
        )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler (optional)
    if config.enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
```

### Structured Log Format (JSON)

**Standard Log Entry**:
```json
{
    "timestamp": "2025-12-02T14:30:45.123Z",
    "level": "INFO",
    "process_id": 12345,
    "agent_name": "youtube_agent",
    "poi_id": "uuid-1234",
    "message": "Content generated successfully",
    "execution_time_seconds": 8.5,
    "metadata": {
        "relevance_score": 85.0,
        "video_count": 3,
        "search_query": "Masada fortress history"
    }
}
```

**Error Log Entry**:
```json
{
    "timestamp": "2025-12-02T14:31:20.456Z",
    "level": "ERROR",
    "process_id": 12346,
    "agent_name": "spotify_agent",
    "poi_id": "uuid-5678",
    "message": "Claude CLI subprocess timed out",
    "execution_time_seconds": 30.0,
    "metadata": {
        "timeout_seconds": 30,
        "retry_attempt": 1,
        "subprocess_pid": 12350
    },
    "exception": "TimeoutError: Claude CLI did not respond within 30 seconds"
}
```

### Self-Diagnosis Flow

```
┌────────────────────────────────────────────────────────────────┐
│ USER TRIGGERS: tour-guide diagnose                             │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│ STEP 1: Parse Log Files (Last 24 Hours)                       │
│  - Read all log files in logs/                                │
│  - Parse JSON entries                                          │
│  - Filter by timestamp (last 24h)                             │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│ STEP 2: Extract Patterns                                      │
│  - Error frequency: Count errors by type                      │
│  - Performance trends: Analyze execution times                │
│  - Agent reliability: Calculate success/failure rates         │
│  - Resource usage: Memory, CPU (if available)                 │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│ STEP 3: Aggregate Statistics                                  │
│                                                                │
│  Error Frequency:                                             │
│    - TimeoutError: 15 occurrences (spotify_agent: 12)        │
│    - OSRMError: 3 occurrences                                 │
│                                                                │
│  Performance Trends:                                          │
│    - youtube_agent: avg 8.5s (increasing: 7s → 10s)          │
│    - spotify_agent: avg 25s (timeouts common)                │
│    - history_agent: avg 12s (stable)                         │
│                                                                │
│  Agent Reliability:                                           │
│    - youtube_agent: 95% success rate                          │
│    - spotify_agent: 60% success rate (40% timeouts)          │
│    - history_agent: 90% success rate                          │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│ STEP 4: Use Claude CLI to Analyze                             │
│  - Load log_diagnosis.skill                                   │
│  - Send aggregated stats to Claude                            │
│  - Claude identifies issues and recommends solutions          │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│ STEP 5: Generate Diagnostic Report                            │
│                                                                │
│  ISSUES IDENTIFIED:                                           │
│  1. Spotify agent has 40% timeout rate                        │
│     - Likely cause: Claude CLI unresponsive for music queries│
│     - Impact: Reduced music content availability             │
│                                                                │
│  2. Performance degradation in YouTube agent                  │
│     - Execution time increased from 7s to 10s over 24h       │
│     - Likely cause: API rate limiting or network issues      │
│                                                                │
│  RECOMMENDATIONS:                                             │
│  1. Increase spotify_agent timeout to 45 seconds             │
│  2. Implement retry logic with exponential backoff            │
│  3. Cache Claude responses for common queries                │
│  4. Monitor YouTube agent for rate limiting                   │
│                                                                │
│  SUMMARY STATISTICS:                                          │
│  - Total routes processed: 25                                 │
│  - Average execution time: 95 seconds                         │
│  - Overall success rate: 85%                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## 8. Skills (Prompt Templates) Design

### Skill Structure

**Definition**: Skills are reusable prompt templates that agents load to interact with Claude CLI. Each skill defines:
- **Purpose**: What the skill does
- **Input Variables**: Placeholders for dynamic data
- **Prompt Template**: The actual prompt sent to Claude
- **Output Format**: Expected response structure
- **Examples**: Few-shot examples for Claude

**File Structure**:
```
tour_guide/
└── skills/
    ├── __init__.py
    ├── route_analysis.skill
    ├── youtube_search.skill
    ├── music_search.skill
    ├── history_narrative.skill
    ├── content_evaluation.skill
    └── log_diagnosis.skill
```

### Skill File Format (.skill)

**Example: route_analysis.skill**
```yaml
---
name: route_analysis
version: 1.0
description: Analyzes a route and selects 10 interesting points of interest
author: Tour Guide System
---

# INPUT VARIABLES
# - origin: str (origin name)
# - destination: str (destination name)
# - waypoints: List[Waypoint] (route waypoints)
# - landmarks: List[str] (named locations along route)
# - distance_km: float (total route distance)

# PROMPT TEMPLATE
You are a route analysis expert. Analyze the following route and select exactly 10 points of interest (POIs) that would be most interesting to travelers.

**Route Information:**
- Origin: {origin}
- Destination: {destination}
- Total Distance: {distance_km} km
- Waypoints: {waypoints_count} waypoints
- Identified Landmarks: {landmarks}

**Selection Criteria:**
1. Historical significance (UNESCO sites, monuments, battlefields)
2. Cultural importance (museums, religious sites, traditional markets)
3. Natural landmarks (parks, viewpoints, geological formations)
4. Tourist popularity (highly rated attractions)
5. Geographic distribution (evenly spaced, not clustered)

**Requirements:**
- Select EXACTLY 10 POIs (or fewer if route is very short)
- Distribute POIs evenly along the route
- Ensure minimum 5 km between POIs
- Provide complete metadata for each POI

**Output Format (JSON):**
```json
{
  "pois": [
    {
      "name": "Masada National Park",
      "coordinates": [31.3157, 35.3540],
      "description": "Ancient fortress overlooking the Dead Sea, site of famous siege in 73 CE",
      "category": "historical",
      "distance_from_start_km": 45.2
    },
    ...
  ]
}
```

# OUTPUT FORMAT
json

# EXAMPLES
[Example route with 10 POIs...]
```

### How Agents Load and Use Skills

**Skill Loader**:
```python
from pathlib import Path
import yaml
from string import Template

class SkillLoader:
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills_cache = {}

    def load_skill(self, skill_name: str) -> 'Skill':
        """Load skill from .skill file"""
        if skill_name in self.skills_cache:
            return self.skills_cache[skill_name]

        skill_file = self.skills_dir / f"{skill_name}.skill"

        if not skill_file.exists():
            raise FileNotFoundError(f"Skill {skill_name} not found")

        # Parse skill file
        content = skill_file.read_text()

        # Split YAML frontmatter and prompt template
        parts = content.split("---", 2)
        metadata = yaml.safe_load(parts[1])
        prompt_template = parts[2].strip()

        skill = Skill(
            name=metadata["name"],
            version=metadata["version"],
            description=metadata["description"],
            prompt_template=prompt_template
        )

        self.skills_cache[skill_name] = skill
        return skill

class Skill:
    def __init__(self, name: str, version: str, description: str,
                 prompt_template: str):
        self.name = name
        self.version = version
        self.description = description
        self.prompt_template = Template(prompt_template)

    def format(self, **kwargs) -> str:
        """Format skill template with provided variables"""
        return self.prompt_template.safe_substitute(**kwargs)
```

**Agent Usage**:
```python
class RouteAnalyzerAgent:
    def __init__(self):
        self.skill_loader = SkillLoader(Path("tour_guide/skills"))

    def analyze_route(self, route_data: RouteData) -> List[POI]:
        # 1. Load skill
        skill = self.skill_loader.load_skill("route_analysis")

        # 2. Format prompt
        prompt = skill.format(
            origin=route_data.origin_name,
            destination=route_data.destination_name,
            waypoints_count=len(route_data.waypoints),
            landmarks=", ".join(route_data.landmarks),
            distance_km=route_data.distance_km
        )

        # 3. Call Claude CLI
        response = self.claude_cli.call(prompt)

        # 4. Parse response
        pois = self.parse_pois(response)

        return pois
```

### Example Skill Template: content_evaluation.skill

```yaml
---
name: content_evaluation
version: 1.0
description: Evaluates content from YouTube, Spotify, and History agents
author: Tour Guide System
---

# INPUT VARIABLES
# - poi: POI object
# - youtube_content: VideoContent or None
# - spotify_content: MusicContent or None
# - history_content: HistoryContent or None

# PROMPT TEMPLATE
You are a content evaluation expert. Evaluate the following content options for a point of interest and select the BEST one.

**Point of Interest:**
- Name: {poi_name}
- Description: {poi_description}
- Category: {poi_category}

**Content Options:**

1. **YouTube Video:**
{youtube_content_summary}

2. **Spotify Music:**
{spotify_content_summary}

3. **Historical Narrative:**
{history_content_summary}

**Evaluation Criteria:**
- Relevance to POI (40%)
- Educational value (30%)
- Entertainment value (20%)
- Content quality (10%)

**Your Task:**
1. Evaluate each content option using the criteria above
2. Assign a score (0-100) to each option
3. Select the BEST option
4. Provide reasoning (2-3 sentences) explaining your choice

**Output Format (JSON):**
```json
{
  "selected_agent": "history",
  "reasoning": "Historical narrative provides unique insights into the siege of Masada with specific dates and people, offering high educational value that complements the location's significance.",
  "scores": {
    "youtube": 78.0,
    "spotify": 65.0,
    "history": 92.0
  }
}
```

# OUTPUT FORMAT
json
```

---

## 9. Error Handling Strategy

### Error Categories

| Category              | Examples                                  | Severity   | Recovery Strategy                 |
|-----------------------|-------------------------------------------|------------|-----------------------------------|
| **Network Errors**    | OSRM timeout, DNS failure                | Medium     | Retry with backoff, fallback      |
| **Subprocess Errors** | Claude CLI crash, timeout                | Medium     | Retry once, return error result   |
| **Data Errors**       | Malformed JSON, invalid coordinates      | Low        | Skip invalid data, continue       |
| **Agent Errors**      | Content generation failure               | Medium     | Return error result, continue     |
| **System Errors**     | Out of memory, disk full                 | Critical   | Log error, exit gracefully        |
| **Configuration Errors**| Missing config file, invalid values    | Critical   | Display error, exit               |

### Retry Logic

**Exponential Backoff**:
```python
import time
from typing import TypeVar, Callable

T = TypeVar('T')

def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> T:
    """Retry function with exponential backoff"""
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            return func()
        except exceptions as e:
            if attempt == max_retries - 1:
                # Last attempt, re-raise
                raise

            log.warning(f"Attempt {attempt + 1} failed: {e}, retrying in {delay}s")
            time.sleep(delay)
            delay *= backoff_factor

    # Should never reach here
    raise RuntimeError("Retry logic failed")

# Usage
def fetch_osrm_route():
    return retry_with_backoff(
        lambda: requests.get(osrm_url, timeout=10).json(),
        max_retries=3,
        initial_delay=1.0,
        exceptions=(requests.Timeout, requests.ConnectionError)
    )
```

### Fallback Mechanisms

**Primary-Fallback Chain**:
```
OSRM → Claude CLI → Error

Content Agent → Retry → Error Result (not crash)

Judge Agent → Heuristic Scoring → Error (all agents failed)
```

**Implementation**:
```python
class RoutePlanner:
    def plan_route(self, origin: str, destination: str) -> RouteData:
        # Try OSRM first
        try:
            return self.fetch_osrm_route(origin, destination)
        except (OSRMTimeout, OSRMError) as e:
            log.warning(f"OSRM failed: {e}, falling back to Claude")

        # Fallback to Claude
        try:
            return self.fetch_claude_route(origin, destination)
        except ClaudeError as e:
            log.error(f"Claude fallback also failed: {e}")
            raise RoutingError("Both OSRM and Claude failed")

class ContentAgent(BaseContentAgent):
    def run(self):
        while True:
            poi = self.poi_queue.get()

            if poi is None:
                break

            try:
                # Try to generate content
                content = self.generate_content(poi)
                result = ContentResult(
                    agent_type=self.agent_type,
                    poi_id=poi.id,
                    content=content,
                    status=ResultStatus.SUCCESS
                )
            except TimeoutError:
                # Timeout: return error result (don't crash)
                result = ContentResult(
                    agent_type=self.agent_type,
                    poi_id=poi.id,
                    status=ResultStatus.TIMEOUT,
                    error_message="Agent timed out"
                )
            except Exception as e:
                # Unexpected error: return error result (don't crash)
                log.error(f"Agent {self.agent_type} failed: {e}")
                result = ContentResult(
                    agent_type=self.agent_type,
                    poi_id=poi.id,
                    status=ResultStatus.FAILURE,
                    error_message=str(e)
                )

            # Always put result (even if error)
            self.content_queue.put(result)
```

### Graceful Degradation

**Degradation Levels**:
```
LEVEL 1: Full Success
- All 10 POIs with selected content

LEVEL 2: Partial Success (Acceptable)
- 8-9 POIs with selected content
- 1-2 POIs failed

LEVEL 3: Degraded Operation (Warning)
- 5-7 POIs with selected content
- Some agents consistently failing

LEVEL 4: Minimal Operation (Error)
- 1-4 POIs with selected content
- Most agents failing

LEVEL 5: Complete Failure (Critical)
- 0 POIs or routing failed
- System cannot continue
```

**Implementation**:
```python
class Orchestrator:
    def evaluate_results(self, judgments: List[JudgmentResult]) -> DegradationLevel:
        """Evaluate quality of results"""
        success_count = sum(1 for j in judgments if j.selected_content is not None)
        total_count = len(judgments)

        success_rate = success_count / total_count if total_count > 0 else 0

        if success_rate >= 0.9:
            return DegradationLevel.FULL_SUCCESS
        elif success_rate >= 0.7:
            return DegradationLevel.PARTIAL_SUCCESS
        elif success_rate >= 0.5:
            return DegradationLevel.DEGRADED
        elif success_rate > 0:
            return DegradationLevel.MINIMAL
        else:
            return DegradationLevel.COMPLETE_FAILURE

    def handle_degradation(self, level: DegradationLevel, judgments: List[JudgmentResult]):
        """Handle degraded operation"""
        if level == DegradationLevel.FULL_SUCCESS:
            log.info("All POIs processed successfully")

        elif level == DegradationLevel.PARTIAL_SUCCESS:
            log.warning("Some POIs failed, continuing with partial results")

        elif level == DegradationLevel.DEGRADED:
            log.error("Many POIs failed, results may be incomplete")
            # Still continue and output available results

        elif level == DegradationLevel.MINIMAL:
            log.error("Most POIs failed, very few results available")
            # Ask user if they want to continue
            if not self.config.force_continue:
                raise DegradedOperationError("Too many failures")

        elif level == DegradationLevel.COMPLETE_FAILURE:
            log.critical("All POIs failed, cannot continue")
            raise CompleteFailureError("System failure")
```

---

## 10. Configuration Management

### Config File Structure

**config.yaml**:
```yaml
# Tour Guide Configuration File
# Version: 1.0

# ============================================================
# LOGGING CONFIGURATION
# ============================================================
logging:
  # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  level: INFO

  # Maximum log file size before rotation (bytes)
  max_bytes: 10485760  # 10 MB

  # Number of backup log files to keep
  backup_count: 5

  # Log format: json or text
  format: json

  # Log directory
  log_dir: "./logs"

  # Enable console logging (in addition to file)
  enable_console: true

  # Enable self-diagnosis feature
  enable_self_diagnosis: true

# ============================================================
# ROUTING CONFIGURATION
# ============================================================
routing:
  # OSRM server URL
  osrm_url: "http://router.project-osrm.org"

  # Fallback to Claude if OSRM fails
  fallback_to_claude: true

  # Request timeout (seconds)
  timeout_seconds: 10

  # Maximum retries for failed requests
  max_retries: 2

  # Enable caching of routes (development only)
  cache_enabled: false

  # Cache TTL (seconds)
  cache_ttl_seconds: 3600

# ============================================================
# AGENT CONFIGURATION
# ============================================================
agents:
  # Content agent timeout (seconds)
  content_agent_timeout: 30

  # Judge agent timeout (seconds)
  judge_agent_timeout: 10

  # Maximum retries for failed agents
  max_retries: 2

  # Enable parallel execution
  enable_parallel_execution: true

  # YouTube agent settings
  youtube:
    max_videos: 3
    prefer_documentary: true
    min_duration_minutes: 3
    max_duration_minutes: 20

  # Spotify agent settings
  spotify:
    max_suggestions: 3
    prefer_local_music: true
    include_modern: false

  # History agent settings
  history:
    min_words: 300
    max_words: 500
    include_sources: true
    narrative_style: "engaging"  # or "academic"

  # Judge agent settings
  judge:
    evaluation_criteria:
      relevance_weight: 0.4
      educational_value_weight: 0.3
      entertainment_value_weight: 0.2
      quality_weight: 0.1
    default_preference: ["history", "youtube", "spotify"]

# ============================================================
# CLAUDE CLI CONFIGURATION
# ============================================================
claude:
  # Model to use
  model: "claude-sonnet-4"

  # Maximum tokens per request
  max_tokens: 4000

  # Temperature (0.0-1.0)
  temperature: 0.7

  # Subprocess timeout (seconds)
  subprocess_timeout: 15

# ============================================================
# OUTPUT CONFIGURATION
# ============================================================
output:
  # Delay between POIs in journey simulation (seconds)
  journey_delay_seconds: 5

  # Enable progress bar
  enable_progress_bar: true

  # Enable colors in CLI output
  enable_colors: true

  # Default JSON output path
  default_json_path: "./output/journey.json"

  # Default Markdown output path
  default_markdown_path: "./output/journey.md"

# ============================================================
# POI CONFIGURATION
# ============================================================
poi:
  # Number of POIs to select
  count: 10

  # Minimum distance between POIs (km)
  min_distance_between_km: 5

  # POI categories to consider
  categories:
    - historical
    - cultural
    - natural
    - religious
    - entertainment

  # Distribution algorithm: even_spread or density_based
  distribution_algorithm: "even_spread"

# ============================================================
# QUEUE CONFIGURATION
# ============================================================
queues:
  # POI queue size
  poi_queue_size: 10

  # Content queue size
  content_queue_size: 30

  # Results queue size
  results_queue_size: 10

  # Use bounded queues (recommended)
  use_bounded_queues: true

# ============================================================
# SYSTEM CONFIGURATION
# ============================================================
system:
  # Overall system timeout (seconds)
  overall_timeout: 180

  # Force continue even if many POIs fail
  force_continue: false

  # Enable detailed error messages
  verbose_errors: true
```

### Environment Variables

**Override Configuration with Environment Variables**:
```bash
# Logging
export TOUR_GUIDE_LOG_LEVEL=DEBUG
export TOUR_GUIDE_LOG_DIR=/var/log/tour_guide

# Routing
export TOUR_GUIDE_OSRM_URL=http://localhost:5000

# Claude
export TOUR_GUIDE_CLAUDE_MODEL=claude-sonnet-4

# Output
export TOUR_GUIDE_OUTPUT_DIR=/tmp/tour_guide_output
```

**Environment Variable Loading**:
```python
import os
from pathlib import Path

class ConfigLoader:
    def load_config(self, config_path: Path) -> Config:
        """Load config from YAML and override with env vars"""
        # 1. Load YAML
        with open(config_path) as f:
            config_dict = yaml.safe_load(f)

        # 2. Override with environment variables
        config_dict = self.apply_env_overrides(config_dict)

        # 3. Validate and convert to Config object
        return Config.from_dict(config_dict)

    def apply_env_overrides(self, config_dict: dict) -> dict:
        """Override config with environment variables"""
        env_mapping = {
            "TOUR_GUIDE_LOG_LEVEL": ("logging", "level"),
            "TOUR_GUIDE_LOG_DIR": ("logging", "log_dir"),
            "TOUR_GUIDE_OSRM_URL": ("routing", "osrm_url"),
            "TOUR_GUIDE_CLAUDE_MODEL": ("claude", "model"),
            "TOUR_GUIDE_OUTPUT_DIR": ("output", "default_json_path"),
        }

        for env_var, (section, key) in env_mapping.items():
            value = os.getenv(env_var)
            if value:
                config_dict[section][key] = value

        return config_dict
```

### Default Values

**Default Configuration**:
```python
@dataclass
class DefaultConfig:
    """Default configuration values"""

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_MAX_BYTES: int = 10485760  # 10 MB
    LOG_BACKUP_COUNT: int = 5

    # Routing
    OSRM_URL: str = "http://router.project-osrm.org"
    ROUTING_TIMEOUT: int = 10

    # Agents
    CONTENT_AGENT_TIMEOUT: int = 30
    JUDGE_AGENT_TIMEOUT: int = 10

    # Claude
    CLAUDE_MODEL: str = "claude-sonnet-4"
    CLAUDE_MAX_TOKENS: int = 4000
    CLAUDE_TEMPERATURE: float = 0.7

    # Output
    JOURNEY_DELAY: int = 5

    # POI
    POI_COUNT: int = 10
    MIN_POI_DISTANCE_KM: float = 5.0

    # Queues
    POI_QUEUE_SIZE: int = 10
    CONTENT_QUEUE_SIZE: int = 30
    RESULTS_QUEUE_SIZE: int = 10

    # System
    OVERALL_TIMEOUT: int = 180
```

---

## 11. Directory Structure

### Full Package Structure

```
llmcourse-hw4-google-maps/
│
├── README.md                          # User-facing documentation
├── PRD.md                             # Product Requirements Document
├── DESIGN.md                          # This document
├── CONTRIBUTING.md                    # Developer guide
├── LICENSE                            # License file
├── pyproject.toml                     # UV project configuration
├── uv.lock                            # UV lock file
│
├── .gitignore                         # Git ignore patterns
├── .python-version                    # Python version (3.10+)
│
├── config.yaml                        # Default configuration
├── config.example.yaml                # Example configuration
│
├── src/
│   └── tour_guide/                    # Main package
│       ├── __init__.py                # Package init
│       ├── __main__.py                # CLI entry point (python -m tour_guide)
│       ├── version.py                 # Version info
│       │
│       ├── cli/                       # Command-line interface
│       │   ├── __init__.py
│       │   ├── main.py                # CLI commands (route, diagnose)
│       │   ├── options.py             # CLI options and arguments
│       │   └── validators.py          # Input validation
│       │
│       ├── core/                      # Core business logic
│       │   ├── __init__.py
│       │   ├── orchestrator.py        # Main coordinator
│       │   ├── route_planner.py       # OSRM + Claude routing
│       │   ├── exceptions.py          # Custom exceptions
│       │   └── types.py               # Core data types (RouteData, POI, etc.)
│       │
│       ├── agents/                    # Agent implementations
│       │   ├── __init__.py
│       │   ├── base.py                # BaseContentAgent (abstract)
│       │   ├── route_analyzer.py      # Route Analyzer Agent
│       │   ├── youtube_agent.py       # YouTube Agent
│       │   ├── spotify_agent.py       # Spotify Agent
│       │   ├── history_agent.py       # History Agent
│       │   ├── judge_agent.py         # Judge Agent
│       │   └── process_manager.py     # Process lifecycle management
│       │
│       ├── queues/                    # Queue management
│       │   ├── __init__.py
│       │   ├── queue_manager.py       # Queue creation and lifecycle
│       │   └── messages.py            # Message data types
│       │
│       ├── logging/                   # Logging system
│       │   ├── __init__.py
│       │   ├── logger.py              # Logger setup
│       │   ├── formatters.py          # JSON formatter
│       │   ├── diagnosis.py           # Self-diagnosis logic
│       │   └── parsers.py             # Log parsing
│       │
│       ├── output/                    # Output formatters
│       │   ├── __init__.py
│       │   ├── formatter.py           # OutputFormatter
│       │   ├── cli_display.py         # Rich CLI display
│       │   ├── json_exporter.py       # JSON export
│       │   ├── markdown_generator.py  # Markdown report
│       │   └── schemas.py             # JSON schemas
│       │
│       ├── skills/                    # Prompt templates
│       │   ├── __init__.py
│       │   ├── loader.py              # Skill loader
│       │   ├── route_analysis.skill   # Route analysis prompt
│       │   ├── youtube_search.skill   # YouTube search prompt
│       │   ├── music_search.skill     # Music search prompt
│       │   ├── history_narrative.skill# History narrative prompt
│       │   ├── content_evaluation.skill# Judge evaluation prompt
│       │   └── log_diagnosis.skill    # Log diagnosis prompt
│       │
│       ├── claude/                    # Claude CLI integration
│       │   ├── __init__.py
│       │   ├── subprocess_wrapper.py  # Subprocess management
│       │   ├── prompt_builder.py      # Prompt formatting
│       │   └── response_parser.py     # Response parsing
│       │
│       ├── config/                    # Configuration management
│       │   ├── __init__.py
│       │   ├── loader.py              # Config loader
│       │   ├── schema.py              # Config schema/validation
│       │   └── defaults.py            # Default values
│       │
│       └── utils/                     # Utility functions
│           ├── __init__.py
│           ├── retry.py               # Retry logic
│           ├── timeout.py             # Timeout utilities
│           ├── validation.py          # Input validation
│           └── geocoding.py           # Geocoding helpers
│
├── tests/                             # Test suite
│   ├── __init__.py
│   ├── conftest.py                    # Pytest fixtures
│   │
│   ├── unit/                          # Unit tests
│   │   ├── __init__.py
│   │   ├── test_route_planner.py
│   │   ├── test_agents.py
│   │   ├── test_queue_manager.py
│   │   ├── test_logger.py
│   │   └── test_output.py
│   │
│   ├── integration/                   # Integration tests
│   │   ├── __init__.py
│   │   ├── test_end_to_end.py
│   │   ├── test_parallel_execution.py
│   │   └── test_error_handling.py
│   │
│   └── fixtures/                      # Test fixtures
│       ├── __init__.py
│       ├── routes.py                  # 10 Israeli test routes
│       ├── mock_responses.py          # Mock Claude/OSRM responses
│       └── sample_outputs.py          # Expected outputs
│
├── logs/                              # Log files (gitignored)
│   └── .gitkeep
│
├── output/                            # Output files (gitignored)
│   ├── .gitkeep
│   ├── journey.json                   # Example JSON output
│   └── journey.md                     # Example Markdown output
│
└── docs/                              # Additional documentation
    ├── user_guide.md                  # User guide
    ├── developer_guide.md             # Developer guide
    ├── api_reference.md               # API documentation
    └── architecture_diagrams/         # Diagrams (if not ASCII)
        └── system_architecture.png
```

---

## 12. API Design

### CLI Commands and Arguments

**Main Command: tour-guide**

```bash
# Route planning command
tour-guide route <origin> <destination> [OPTIONS]

# Diagnostic command
tour-guide diagnose [OPTIONS]

# Help command
tour-guide --help
tour-guide route --help
tour-guide diagnose --help
```

**Route Command**:
```bash
tour-guide route "Tel Aviv" "Jerusalem" \
  --json-output journey.json \
  --markdown-output report.md \
  --no-animation \
  --config custom_config.yaml \
  --log-level DEBUG
```

**Options**:
```
REQUIRED ARGUMENTS:
  origin              Origin location (place name or "lat,long")
  destination         Destination location (place name or "lat,long")

OUTPUT OPTIONS:
  --json-output PATH           Export results to JSON file
  --markdown-output PATH       Generate Markdown report
  --no-animation               Skip 5-second delays in CLI display
  --quiet                      Suppress progress bars and animations

CONFIGURATION OPTIONS:
  --config PATH                Path to config.yaml (default: ./config.yaml)
  --log-level LEVEL            Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  --log-dir PATH               Log directory (default: ./logs)

AGENT OPTIONS:
  --poi-count N                Number of POIs to select (default: 10)
  --content-timeout N          Content agent timeout in seconds (default: 30)
  --no-parallel                Disable parallel execution (sequential mode)

OTHER OPTIONS:
  --version                    Show version and exit
  --help                       Show help and exit
```

**Diagnose Command**:
```bash
tour-guide diagnose \
  --hours 24 \
  --output diagnosis.md \
  --verbose
```

**Options**:
```
DIAGNOSTIC OPTIONS:
  --hours N                    Analyze logs from last N hours (default: 24)
  --output PATH                Save diagnostic report to file
  --verbose                    Show detailed analysis

OTHER OPTIONS:
  --help                       Show help and exit
```

### Public Python API (Library Usage)

**Basic Usage**:
```python
from tour_guide import TourGuide
from tour_guide.config import Config

# Initialize with default config
guide = TourGuide()

# Plan a journey
journey = guide.plan_journey(
    origin="Tel Aviv",
    destination="Jerusalem"
)

# Access results
for poi, judgment in zip(journey.pois, journey.judgments):
    print(f"{poi.name}: {judgment.selected_agent}")

# Export results
guide.export_json(journey, "journey.json")
guide.export_markdown(journey, "report.md")
```

**Advanced Usage with Custom Config**:
```python
from tour_guide import TourGuide
from tour_guide.config import Config
from pathlib import Path

# Load custom config
config = Config.from_file(Path("custom_config.yaml"))

# Override specific settings
config.agents.content_agent_timeout = 45
config.output.journey_delay_seconds = 0  # No animation

# Initialize with custom config
guide = TourGuide(config=config)

# Plan journey with callbacks
def on_progress(stage: str, progress: float):
    print(f"{stage}: {progress:.0%}")

journey = guide.plan_journey(
    origin="32.0853,34.7818",  # Coordinates
    destination="31.7683,35.2137",
    progress_callback=on_progress
)
```

**Async API (Future Enhancement)**:
```python
import asyncio
from tour_guide import TourGuideAsync

async def main():
    guide = TourGuideAsync()

    # Plan multiple journeys concurrently
    journeys = await asyncio.gather(
        guide.plan_journey_async("Tel Aviv", "Jerusalem"),
        guide.plan_journey_async("Haifa", "Akko"),
        guide.plan_journey_async("Beer Sheva", "Masada")
    )

    for journey in journeys:
        print(f"{journey.origin} → {journey.destination}: {len(journey.pois)} POIs")

asyncio.run(main())
```

---

## 13. Testing Strategy

### Unit Test Approach

**Test Coverage Goals**:
- **Minimum**: 80% code coverage
- **Target**: 90% code coverage
- **Critical Components**: 100% coverage (Orchestrator, Queue Manager, Agents)

**Unit Test Structure**:
```python
# tests/unit/test_route_planner.py
import pytest
from unittest.mock import Mock, patch
from tour_guide.core.route_planner import RoutePlanner
from tour_guide.core.types import RouteData

class TestRoutePlanner:
    @pytest.fixture
    def route_planner(self):
        """Create RoutePlanner instance"""
        config = Mock()
        config.osrm_url = "http://test-osrm.org"
        config.timeout_seconds = 10
        return RoutePlanner(config)

    def test_plan_route_osrm_success(self, route_planner):
        """Test successful OSRM routing"""
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                "routes": [{"distance": 65000, "duration": 3600}]
            }

            route = route_planner.plan_route("Tel Aviv", "Jerusalem")

            assert route.distance_km == 65.0
            assert route.duration_seconds == 3600
            assert route.data_source == "osrm"

    def test_plan_route_osrm_timeout_fallback(self, route_planner):
        """Test fallback to Claude when OSRM times out"""
        with patch('requests.get') as mock_get, \
             patch.object(route_planner, 'fetch_claude_route') as mock_claude:

            mock_get.side_effect = TimeoutError()
            mock_claude.return_value = RouteData(
                origin_name="Tel Aviv",
                destination_name="Jerusalem",
                distance_km=65.0,
                data_source="claude"
            )

            route = route_planner.plan_route("Tel Aviv", "Jerusalem")

            assert route.data_source == "claude"
            mock_claude.assert_called_once()

    def test_geocode_place_name(self, route_planner):
        """Test geocoding place name to coordinates"""
        coords = route_planner.geocode("Tel Aviv")

        assert len(coords) == 2
        assert 31.0 < coords[0] < 33.0  # Rough latitude check
        assert 34.0 < coords[1] < 36.0  # Rough longitude check
```

**Mocking Strategy**:
- **Mock External Services**: OSRM, Claude CLI (subprocess)
- **Mock Queues**: Use `queue.Queue` instead of `multiprocessing.Queue` for unit tests
- **Mock Filesystem**: Use temporary directories for log and output files
- **Deterministic Responses**: Fixtures with known inputs/outputs

### Integration Test Approach

**Integration Test Categories**:
1. **End-to-End**: Full journey from origin to destination
2. **Parallel Execution**: Test multiprocessing with all agents
3. **Error Handling**: Test failure scenarios and recovery
4. **Performance**: Benchmark execution times

**Integration Test Example**:
```python
# tests/integration/test_end_to_end.py
import pytest
from pathlib import Path
from tour_guide import TourGuide
from tour_guide.config import Config

class TestEndToEnd:
    @pytest.fixture
    def tour_guide(self, tmp_path):
        """Create TourGuide with test config"""
        config = Config()
        config.logging.log_dir = tmp_path / "logs"
        config.output.journey_delay_seconds = 0  # No delays in tests
        return TourGuide(config)

    @pytest.mark.slow
    @pytest.mark.integration
    def test_tel_aviv_to_jerusalem(self, tour_guide):
        """Test Tel Aviv to Jerusalem route (full integration)"""
        journey = tour_guide.plan_journey(
            origin="Tel Aviv",
            destination="Jerusalem"
        )

        # Verify journey structure
        assert journey is not None
        assert journey.origin_name == "Tel Aviv"
        assert journey.destination_name == "Jerusalem"

        # Verify POIs
        assert len(journey.pois) == 10
        for poi in journey.pois:
            assert poi.name
            assert poi.coordinates
            assert poi.description

        # Verify judgments
        assert len(journey.judgments) == 10
        for judgment in journey.judgments:
            assert judgment.selected_agent in ["youtube", "spotify", "history"]
            assert judgment.selected_content
            assert judgment.reasoning

        # Verify at least 80% success rate
        successful = sum(1 for j in journey.judgments if j.selected_content)
        assert successful >= 8

    @pytest.mark.integration
    def test_parallel_execution_speedup(self, tour_guide):
        """Test that parallel execution is faster than sequential"""
        import time

        # Enable parallel execution
        tour_guide.config.agents.enable_parallel_execution = True
        start = time.time()
        journey_parallel = tour_guide.plan_journey("Haifa", "Akko")
        parallel_time = time.time() - start

        # Disable parallel execution
        tour_guide.config.agents.enable_parallel_execution = False
        start = time.time()
        journey_sequential = tour_guide.plan_journey("Haifa", "Akko")
        sequential_time = time.time() - start

        # Verify speedup (at least 2x)
        assert parallel_time < sequential_time / 2

        # Verify results are similar
        assert len(journey_parallel.pois) == len(journey_sequential.pois)
```

### Test Fixtures (10 Routes)

**Route Fixtures**:
```python
# tests/fixtures/routes.py
import pytest
from dataclasses import dataclass

@dataclass
class TestRoute:
    name: str
    origin: str
    destination: str
    expected_distance_km: float  # Approximate
    expected_pois: int

ISRAELI_TEST_ROUTES = [
    TestRoute(
        name="Tel Aviv to Jerusalem",
        origin="Tel Aviv",
        destination="Jerusalem",
        expected_distance_km=65,
        expected_pois=10
    ),
    TestRoute(
        name="Haifa to Akko",
        origin="Haifa",
        destination="Akko",
        expected_distance_km=20,
        expected_pois=10
    ),
    TestRoute(
        name="Tel Aviv to Eilat",
        origin="Tel Aviv",
        destination="Eilat",
        expected_distance_km=350,
        expected_pois=10
    ),
    TestRoute(
        name="Jerusalem to Dead Sea",
        origin="Jerusalem",
        destination="Dead Sea",
        expected_distance_km=40,
        expected_pois=10
    ),
    TestRoute(
        name="Nazareth to Tiberias",
        origin="Nazareth",
        destination="Tiberias",
        expected_distance_km=35,
        expected_pois=10
    ),
    TestRoute(
        name="Tel Aviv to Caesarea",
        origin="Tel Aviv",
        destination="Caesarea",
        expected_distance_km=50,
        expected_pois=10
    ),
    TestRoute(
        name="Beer Sheva to Masada",
        origin="Beer Sheva",
        destination="Masada",
        expected_distance_km=90,
        expected_pois=10
    ),
    TestRoute(
        name="Haifa to Rosh Hanikra",
        origin="Haifa",
        destination="Rosh Hanikra",
        expected_distance_km=35,
        expected_pois=10
    ),
    TestRoute(
        name="Jerusalem to Bethlehem",
        origin="Jerusalem",
        destination="Bethlehem",
        expected_distance_km=10,
        expected_pois=8  # Short route, may have fewer POIs
    ),
    TestRoute(
        name="Tel Aviv to Jaffa",
        origin="Tel Aviv",
        destination="Jaffa",
        expected_distance_km=5,
        expected_pois=5  # Very short route, fewer POIs
    ),
]

@pytest.fixture(params=ISRAELI_TEST_ROUTES, ids=lambda r: r.name)
def test_route(request):
    """Parametrized fixture for all test routes"""
    return request.param

# Usage:
# def test_all_routes(test_route, tour_guide):
#     journey = tour_guide.plan_journey(test_route.origin, test_route.destination)
#     assert len(journey.pois) >= test_route.expected_pois - 2
```

**Mock Response Fixtures**:
```python
# tests/fixtures/mock_responses.py
MOCK_OSRM_RESPONSE = {
    "code": "Ok",
    "routes": [{
        "distance": 65000,
        "duration": 3600,
        "geometry": "...",
        "legs": [...]
    }]
}

MOCK_CLAUDE_POI_RESPONSE = """
{
  "pois": [
    {
      "name": "Latrun Monastery",
      "coordinates": [31.8367, 34.9839],
      "description": "Trappist monastery famous for its wine production and peaceful grounds",
      "category": "religious",
      "distance_from_start_km": 25.5
    },
    ...
  ]
}
"""

MOCK_YOUTUBE_RESPONSE = """
{
  "videos": [
    {
      "title": "History of Masada Fortress",
      "channel": "Historical Documentaries",
      "duration_minutes": 12,
      "url": "https://youtube.com/watch?v=...",
      "description": "Documentary about the siege of Masada",
      "relevance_score": 92.0
    }
  ]
}
"""
```

**Test Runner Configuration**:
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (slower, may use external services)
    slow: Slow tests (>5 seconds)
    requires_claude: Tests requiring Claude CLI authentication

addopts =
    --verbose
    --cov=tour_guide
    --cov-report=html
    --cov-report=term
    --strict-markers

[coverage:run]
source = tour_guide
omit =
    */tests/*
    */venv/*
    */__pycache__/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

---

## 14. Technology Decisions

| Decision Category       | Choice                    | Alternatives Considered      | Rationale                                                                 |
|-------------------------|---------------------------|------------------------------|---------------------------------------------------------------------------|
| **Package Manager**     | UV                        | pip, poetry, pipenv          | Required by assignment; faster than alternatives                          |
| **Python Version**      | 3.10+                     | 3.8, 3.9                     | Modern type hints, match statements, better performance                   |
| **CLI Framework**       | Click                     | Typer, argparse              | Mature, widely-used, rich ecosystem of plugins                            |
| **Terminal UI**         | Rich                      | Colorama, Blessed            | Best-in-class formatting, progress bars, tables, panels                   |
| **HTTP Client**         | Requests                  | httpx, urllib3               | Simple, synchronous (no async needed), well-documented                    |
| **Config Format**       | YAML                      | TOML, JSON, INI              | Human-readable, supports comments, hierarchical structure                 |
| **JSON Validation**     | jsonschema                | pydantic, marshmallow        | Lightweight, standard-compliant, no ORM overhead                          |
| **Multiprocessing**     | stdlib multiprocessing    | concurrent.futures, joblib   | No external dependencies, full control, works with queues                 |
| **Logging**             | stdlib logging            | loguru, structlog            | Standard, rotating handlers built-in, JSON formatting possible            |
| **Testing Framework**   | pytest                    | unittest, nose               | Parametrized tests, fixtures, plugins (coverage, mock)                    |
| **Code Formatter**      | Ruff                      | Black, autopep8              | Fastest formatter, all-in-one linter+formatter, modern                    |
| **Type Checker**        | mypy                      | pyright, pyre                | Industry standard, gradual typing, good IDE support                       |
| **Routing Service**     | OSRM                      | Google Maps, MapBox          | Free, no API keys, self-hostable, good coverage                           |
| **AI Provider**         | Claude CLI (subprocess)   | OpenAI API, direct Claude API| No API keys in code, uses existing auth, subprocess isolation             |
| **Subprocess Mgmt**     | stdlib subprocess         | sh, plumbum                  | Standard library, good timeout control, cross-platform                    |
| **Path Handling**       | pathlib                   | os.path                      | Modern, object-oriented, cross-platform, chainable operations             |
| **Data Classes**        | stdlib dataclasses        | attrs, pydantic              | Standard library, sufficient for use case, no external deps               |
| **Date/Time**           | stdlib datetime           | arrow, pendulum              | Standard library sufficient, no complex timezone logic needed             |
| **Queue Type**          | multiprocessing.Queue     | queue.Queue, asyncio.Queue   | Designed for multiprocessing, thread-safe, supports pickling              |
| **Process Start Method**| spawn                     | fork, forkserver             | Cross-platform (Windows, macOS, Linux), safer than fork                   |
| **Error Handling**      | Custom exceptions         | Standard exceptions only     | Type-safe, clear error categories, better error messages                  |
| **Retry Logic**         | Custom implementation     | tenacity, backoff            | No external deps, simple exponential backoff sufficient                   |
| **Markdown Generation** | String formatting         | markdown-it, mistune         | Simple format, no parsing needed, just generation                         |
| **Skill Format**        | YAML frontmatter + text   | JSON, TOML, custom DSL       | Readable, supports metadata, easy to edit, no complex parsing             |

---

## Appendix A: Design Principles Summary

### Key Architectural Principles

1. **Building Block Pattern**: Each component has clearly defined input, output, setup data, dependencies, and error handling.

2. **Single Responsibility**: Each component does exactly one thing. Route Planner routes, Agents generate content, Judge evaluates.

3. **Separation of Concerns**: Routing, content generation, judging, and output formatting are completely separate.

4. **Fail Fast**: Validate inputs early. If origin/destination is invalid, fail immediately before spawning processes.

5. **Graceful Degradation**: System continues with partial results. 8 out of 10 POIs is acceptable.

6. **Fault Isolation**: Agent failures are contained. One agent crashing doesn't bring down the system.

7. **Queue-Based Communication**: No direct function calls between agents. All communication via bounded queues.

8. **Idempotency**: Same input produces same output (modulo Claude randomness, controlled by temperature).

9. **Observability**: Comprehensive logging at all levels. Every decision logged.

10. **Configuration Over Code**: All tunable parameters in config.yaml, not hardcoded.

---

## Appendix B: Performance Targets

| Metric                          | Target      | Measured By                     |
|---------------------------------|-------------|---------------------------------|
| Route Planning                  | <10 seconds | OSRM + Claude fallback          |
| Route Analysis                  | <10 seconds | Claude CLI response time        |
| Content Discovery (parallel)    | <90 seconds | Max time for 10 POIs × 3 agents |
| Judging (all POIs)              | <60 seconds | 10 POIs × ~5 seconds each       |
| Total Execution (no animation)  | <120 seconds| End-to-end                      |
| Memory Usage                    | <500 MB     | Peak memory during execution    |
| Agent Success Rate              | >90%        | Successful results / total POIs |
| Parallel Speedup                | >2.5x       | Parallel time vs sequential     |
| Log File Size (per route)       | <1 MB       | JSON log file size              |

---

## Appendix C: Glossary

- **POI**: Point of Interest - a location of interest along the route
- **Agent**: An independent process that performs a specific task (route analysis, content generation, judging)
- **Content Agent**: Agent that generates content (YouTube, Spotify, History)
- **Judge Agent**: Meta-agent that evaluates and selects content
- **Queue**: multiprocessing.Queue - bounded FIFO data structure for inter-process communication
- **Skill**: Reusable prompt template for Claude CLI interactions
- **Journey**: Complete result including route, POIs, and selected content
- **Judgment**: Judge agent's decision about which content to select for a POI
- **OSRM**: Open Source Routing Machine - free routing service
- **Claude CLI**: Anthropic's CLI tool for Claude API access
- **Subprocess**: Child process spawned for Claude CLI calls
- **Rotation**: Log file rotation when size limit reached
- **Self-Diagnosis**: Automated log analysis to identify issues
- **Graceful Degradation**: Continued operation with reduced functionality
- **Poison Pill**: None message sent to queue to terminate worker processes

---

**Document Version**: 1.0
**Last Updated**: 2025-12-02
**Status**: Design Approved for Implementation
**Next Steps**: Begin Phase 1 (Project Setup & Infrastructure)

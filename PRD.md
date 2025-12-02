# Product Requirements Document: Tour Guide AI System

## 1. Executive Summary

Tour Guide is a multi-agent AI-powered Python package that transforms road trips into engaging, educational journeys by automatically discovering and curating content about points of interest along any route. The system analyzes a given route, identifies the 10 most interesting locations, and intelligently selects the best entertainment or educational content (videos, music, or historical facts) for each location through parallel content discovery and AI-based judging. Designed as a fully installable pip package with no external API dependencies, Tour Guide provides a rich CLI experience that simulates the journey with timed content delivery.

## 2. Problem Statement

Road trips often involve long stretches of driving where passengers (and drivers during breaks) miss opportunities to learn about the fascinating places they're passing through. Current solutions require manual research before the trip or rely on paid tour guide services. Travelers lack an automated, intelligent system that:
- Discovers interesting points along their route without manual planning
- Curates relevant, high-quality content (videos, music, historical facts) for each location
- Delivers content in an engaging, timed manner that simulates the actual journey
- Works offline or with minimal API dependencies
- Provides professional documentation of the journey for later reference

Tour Guide solves this by automating the entire content discovery and curation pipeline, turning any car into a mobile learning environment.

## 3. Target Users

### Primary Users
- **Road Trip Enthusiasts**: Individuals or families taking long drives who want to enhance their travel experience with educational content
- **Tourists**: Visitors exploring new regions who want to learn about the culture, history, and attractions along their route
- **Educational Groups**: Teachers and students on field trips seeking structured, relevant content about locations they visit

### Secondary Users
- **Travel Bloggers/Content Creators**: Users who need well-researched information about routes for content creation
- **Tour Guide Professionals**: Professional guides who want to augment their knowledge with AI-curated content
- **Developers**: Python developers looking for a reference implementation of multi-agent systems with parallel processing

### Technical Users
- **Data Scientists/ML Engineers**: Users interested in studying multi-agent AI systems and queue-based architectures
- **University Students**: Computer science students learning about concurrent programming, agent systems, and package development

## 4. Goals & Success Metrics

### Primary Goals
1. **Content Quality**: Deliver highly relevant, interesting content for 90%+ of selected POIs
2. **Performance**: Complete content discovery for all 10 POIs in under 2 minutes using parallel processing
3. **Reliability**: Successfully handle 95%+ of route requests with graceful fallbacks for API failures
4. **Usability**: Provide an intuitive CLI that requires minimal technical knowledge to operate

### Success Metrics
- **Agent Performance**: Each content agent (YouTube, Spotify, History) produces valid results for 90%+ of POIs
- **Judge Accuracy**: User satisfaction surveys indicate 80%+ agreement with Judge agent's content selections
- **System Reliability**:
  - 95%+ uptime for routing services (OSRM + Claude fallback)
  - Zero crashes due to agent failures (all exceptions handled gracefully)
- **Execution Speed**:
  - Route analysis completes in <10 seconds
  - Parallel content discovery for 10 POIs completes in <90 seconds
- **Code Quality**:
  - 80%+ test coverage
  - Successfully installable via `pip install` or `uv pip install`
  - Comprehensive logging enables diagnosis of 100% of failures
- **User Engagement**:
  - Users complete full simulated journey 70%+ of the time
  - 60%+ of users export results (JSON/Markdown) indicating value in the content

### Non-Goals (Explicitly Out of Scope for v1.0)
- Real-time GPS integration during actual driving
- Mobile app development (CLI only)
- Monetization or commercial API integrations
- Support for non-English content (English only for v1.0)

## 5. Features & Requirements

### 5.1 Routing System

**Description**: Retrieve and process route information between origin and destination coordinates or place names.

**Requirements**:
- **FR-1.1**: Use OSRM (Open Source Routing Machine) as the primary routing engine (free, no API keys required)
- **FR-1.2**: Implement Claude CLI fallback if OSRM request fails or returns invalid data
- **FR-1.3**: Parse route data to extract:
  - Total distance and estimated duration
  - Waypoints (latitude/longitude coordinates)
  - Step-by-step directions
  - Major landmarks or named locations along the route
- **FR-1.4**: Support both coordinate-based input (lat/long) and place name input (geocoded to coordinates)
- **FR-1.5**: Cache routing results to avoid redundant API calls during development/testing

**Acceptance Criteria**:
- Successfully routes between all 10 test Israeli routes
- Falls back to Claude within 5 seconds if OSRM fails
- Returns structured route data including at least 20 waypoints for typical routes

### 5.2 Route Analysis Agent

**Description**: Intelligent agent that analyzes the complete route and selects the 10 most interesting points of interest.

**Requirements**:
- **FR-2.1**: Receive full route data (waypoints, landmarks, directions) as input
- **FR-2.2**: Apply selection criteria to identify "interesting" POIs:
  - Historical significance (UNESCO sites, monuments, battlefields)
  - Cultural importance (museums, religious sites, traditional markets)
  - Natural landmarks (parks, viewpoints, unique geological formations)
  - Tourist popularity (highly rated attractions)
  - Geographic distribution (evenly spaced along route, not clustered)
- **FR-2.3**: Return exactly 10 POIs with:
  - Name/title of location
  - Coordinates (lat/long)
  - Brief description (2-3 sentences)
  - Category (historical, natural, cultural, etc.)
  - Approximate distance from route start
- **FR-2.4**: Use Claude CLI subprocess to perform intelligent analysis (no external APIs)
- **FR-2.5**: Handle edge cases:
  - Routes with <10 interesting points (return all available)
  - Very short routes (distribute points proportionally)
  - Routes through remote areas (lower threshold for "interesting")

**Acceptance Criteria**:
- Produces 10 POIs for 90%+ of test routes
- POIs are distributed across the route (not all clustered at start/end)
- Each POI has complete metadata (name, coordinates, description, category)
- Execution time <10 seconds for typical routes

### 5.3 Content Discovery Agents

**Description**: Three specialized agents that work in parallel to find relevant content for each POI.

#### 5.3.1 YouTube Agent

**Requirements**:
- **FR-3.1**: Accept POI data (name, description, category) as input
- **FR-3.2**: Use Claude CLI to generate relevant YouTube search queries
- **FR-3.3**: Simulate video search (or use YouTube search API if available without key)
- **FR-3.4**: Return top 3 video suggestions with:
  - Video title
  - Channel name
  - Estimated duration
  - Relevance score (0-100)
  - Brief description of content
- **FR-3.5**: Handle cases where no relevant videos exist (return empty result with explanation)

#### 5.3.2 Spotify Agent

**Requirements**:
- **FR-3.6**: Accept POI data (name, description, category) as input
- **FR-3.7**: Use Claude CLI to identify relevant music genres, artists, or specific songs related to the location
- **FR-3.8**: Suggest music that matches:
  - Local music traditions (folk songs, regional artists)
  - Historical era associated with the location
  - Thematic content (e.g., songs about the sea for coastal locations)
- **FR-3.9**: Return top 3 music suggestions with:
  - Song/album/playlist title
  - Artist name
  - Genre
  - Relevance score (0-100)
  - Brief explanation of relevance
- **FR-3.10**: Handle cases where no relevant music exists (return empty result with explanation)

#### 5.3.3 History Agent

**Requirements**:
- **FR-3.11**: Accept POI data (name, description, category) as input
- **FR-3.12**: Use Claude CLI to research and generate historical content
- **FR-3.13**: Produce engaging historical narratives:
  - 3-5 minute read length (300-500 words)
  - Story format (not just facts)
  - Include specific dates, people, events
  - Connect local history to broader historical context
- **FR-3.14**: Return historical content with:
  - Title
  - Full text narrative
  - Key facts (bulleted list)
  - Relevance score (0-100)
  - Sources/references (if Claude provides them)
- **FR-3.15**: Handle locations with limited historical information (provide general regional history)

**Common Requirements (All Content Agents)**:
- **FR-3.16**: Execute in parallel using multiprocessing
- **FR-3.17**: Place results in shared queue for Judge agent
- **FR-3.18**: Log all activities (search queries, results, execution time)
- **FR-3.19**: Timeout after 30 seconds if Claude subprocess hangs
- **FR-3.20**: Gracefully handle failures (return error object instead of crashing)

**Acceptance Criteria**:
- All three agents complete within 30 seconds for a single POI
- At least 2 out of 3 agents return valid content for each POI
- Results include relevance scores for Judge agent evaluation
- Parallel execution achieves 3x speedup compared to sequential

### 5.4 Judge Agent

**Description**: Meta-agent that evaluates outputs from the three content agents and selects the best content for each POI.

**Requirements**:
- **FR-4.1**: Receive outputs from YouTube, Spotify, and History agents via queue
- **FR-4.2**: Use Claude CLI to evaluate content based on:
  - Relevance to the specific POI
  - Educational value
  - Entertainment value
  - Quality of content (production value for videos, writing quality for history)
  - Uniqueness (prefer uncommon facts over generic information)
- **FR-4.3**: Select exactly ONE content type per POI (YouTube OR Spotify OR History)
- **FR-4.4**: Return judgment with:
  - Selected content type
  - Selected content data (full object from winning agent)
  - Reasoning (2-3 sentences explaining the choice)
  - Scores for all three options (transparency)
- **FR-4.5**: Handle edge cases:
  - All three agents failed: select least-bad option or return error
  - Two agents tied: use secondary criteria (default preference: History > YouTube > Spotify)
  - Single agent succeeded: select it by default
- **FR-4.6**: Log all evaluation decisions for later analysis

**Acceptance Criteria**:
- Produces valid selection for 100% of POIs (even if all agents failed)
- Judgments align with human preferences in 80%+ of user survey responses
- Execution time <5 seconds per POI
- Provides clear, understandable reasoning for each selection

### 5.5 Parallel Processing & Synchronization

**Description**: Architectural requirements for concurrent execution and agent communication.

**Requirements**:
- **FR-5.1**: Use Python `multiprocessing` module for true parallelism (not threading for CPU-bound tasks)
- **FR-5.2**: Implement queue-based communication:
  - POI Queue: Route Analyzer → Content Agents (10 POIs)
  - Content Queue: Content Agents → Judge Agent (30 content items: 3 per POI)
  - Results Queue: Judge Agent → Main Process (10 final selections)
- **FR-5.3**: Use `multiprocessing.Pool` for content agents (spawn 3 workers)
- **FR-5.4**: Implement proper queue cleanup (drain queues, join processes)
- **FR-5.5**: Use locks/semaphores only where necessary (prefer queue-based sync)
- **FR-5.6**: Implement timeout mechanisms:
  - Content agent processes timeout after 30 seconds
  - Judge agent timeout after 10 seconds per POI
  - Overall system timeout after 3 minutes
- **FR-5.7**: Handle process crashes gracefully:
  - Dead processes detected via `is_alive()` checks
  - Restart failed processes up to 2 times
  - Continue with partial results if retries fail

**Acceptance Criteria**:
- System achieves >2.5x speedup for 10 POIs compared to sequential execution
- Zero deadlocks or race conditions in 100 test runs
- All processes terminate cleanly (no zombie processes)
- Queue sizes never exceed memory limits (use bounded queues)

### 5.6 Logging System

**Description**: Comprehensive logging with rotation and self-diagnosis capabilities.

**Requirements**:
- **FR-6.1**: Use Python `logging` module with rotating file handler
- **FR-6.2**: Configure rotation parameters:
  - Max log file size: 10 MB (configurable via config file)
  - Max backup files: 5 (configurable)
  - Log file naming: `tour_guide_YYYYMMDD_HHMMSS.log`
- **FR-6.3**: Implement log levels:
  - DEBUG: Detailed diagnostic info (agent inputs/outputs, queue states)
  - INFO: High-level progress (POI processed, agent completed)
  - WARNING: Recoverable issues (agent timeout, fallback to Claude)
  - ERROR: Non-fatal errors (agent failure, malformed data)
  - CRITICAL: System failures (all agents failed, unrecoverable errors)
- **FR-6.4**: Log structured data in JSON format for programmatic analysis
- **FR-6.5**: Include metadata in each log entry:
  - Timestamp (ISO 8601)
  - Process ID
  - Agent name
  - POI identifier
  - Execution time (for performance analysis)
- **FR-6.6**: Implement self-diagnosis feature:
  - Parse recent log files (last 24 hours)
  - Use Claude CLI to analyze patterns:
    - Frequent errors (same error type >5 times)
    - Performance degradation (increasing execution times)
    - Agent reliability (success/failure rates)
  - Generate diagnostic report with recommendations
- **FR-6.7**: Provide CLI command for diagnostics: `tour-guide diagnose`

**Acceptance Criteria**:
- Logs rotate correctly without data loss
- All agent activities logged with structured data
- Self-diagnosis identifies common issues (verified by injecting known problems)
- Log files parseable by standard tools (JSON lines format)

### 5.7 Output Formats

**Description**: Multiple output formats for different use cases.

#### 5.7.1 Rich CLI Display

**Requirements**:
- **FR-7.1**: Use `rich` library for formatted terminal output
- **FR-7.2**: Display progress bar during processing:
  - Stage 1: Routing (10% of total)
  - Stage 2: Route analysis (20%)
  - Stage 3: Content discovery (50%)
  - Stage 4: Judging (20%)
- **FR-7.3**: Simulate journey with timed content delivery:
  - Display POI name and location
  - Show selected content (video/song/history)
  - Wait 5 seconds before next POI
  - Use rich formatting: colors, boxes, emoji (optional)
- **FR-7.4**: Show summary statistics at the end:
  - Total POIs processed
  - Content type distribution (X videos, Y songs, Z histories)
  - Total execution time
  - Route distance and duration
- **FR-7.5**: Support `--no-animation` flag to skip delays (for testing)

#### 5.7.2 JSON Export

**Requirements**:
- **FR-7.6**: Export complete results to JSON file
- **FR-7.7**: Include all data:
  - Route information (origin, destination, distance, duration)
  - All 10 POIs (name, coordinates, description, category)
  - Selected content for each POI (full details)
  - Judgment reasoning
  - Metadata (timestamp, execution time, package version)
- **FR-7.8**: Validate JSON schema (use jsonschema library)
- **FR-7.9**: Support custom output path: `--json-output path/to/file.json`

#### 5.7.3 Markdown Report

**Requirements**:
- **FR-7.10**: Generate human-readable Markdown report
- **FR-7.11**: Include sections:
  - Journey header (origin → destination)
  - Route overview (map link, stats)
  - POI entries (one per POI with content)
  - Appendix (methodology, all agent outputs)
- **FR-7.12**: Format POI entries:
  - Heading with POI name and emoji
  - Location details (coordinates, category)
  - Selected content (embedded links for videos/music)
  - Historical narratives (full text)
- **FR-7.13**: Support custom output path: `--markdown-output path/to/report.md`

**Common Requirements**:
- **FR-7.14**: Support multiple simultaneous exports: `--json-output file.json --markdown-output report.md`
- **FR-7.15**: All outputs include disclaimer about AI-generated content

**Acceptance Criteria**:
- CLI displays progress accurately (progress bar reaches 100%)
- Simulated journey completes with 5-second delays between POIs
- JSON exports are valid and contain all required fields
- Markdown reports are well-formatted and readable on GitHub
- All output formats generated successfully in 100% of runs

## 6. Non-Functional Requirements

### 6.1 Performance

- **NFR-1.1**: Route analysis completes in <10 seconds for routes up to 500 km
- **NFR-1.2**: Parallel content discovery achieves >2.5x speedup compared to sequential
- **NFR-1.3**: Total execution time <2 minutes for typical routes (origin to content selection)
- **NFR-1.4**: Memory usage stays under 500 MB during execution
- **NFR-1.5**: Claude CLI subprocesses respond within 15 seconds (95th percentile)

### 6.2 Reliability

- **NFR-2.1**: System handles OSRM failures gracefully with automatic Claude fallback
- **NFR-2.2**: Individual agent failures don't crash the entire system (fault isolation)
- **NFR-2.3**: All timeouts are configurable via config file
- **NFR-2.4**: System continues with partial results if some agents fail (degraded operation)
- **NFR-2.5**: Error messages are clear, actionable, and logged comprehensively

### 6.3 Maintainability

- **NFR-3.1**: Codebase follows PEP 8 style guidelines (enforced by ruff/black)
- **NFR-3.2**: All public functions have docstrings with type hints
- **NFR-3.3**: Modular architecture allows easy addition of new content agents
- **NFR-3.4**: Configuration externalized to YAML/TOML file (not hardcoded)
- **NFR-3.5**: Comprehensive test suite with 80%+ coverage

### 6.4 Usability

- **NFR-4.1**: CLI provides helpful error messages with suggested fixes
- **NFR-4.2**: `--help` flag displays comprehensive usage documentation
- **NFR-4.3**: Default settings work for 90%+ of use cases (minimal configuration needed)
- **NFR-4.4**: Installation requires only `pip install tour-guide` (all dependencies bundled)

### 6.5 Portability

- **NFR-5.1**: Runs on Linux, macOS, and Windows
- **NFR-5.2**: Compatible with Python 3.10, 3.11, 3.12
- **NFR-5.3**: No system dependencies beyond Python standard library + declared dependencies
- **NFR-5.4**: All file paths use `pathlib` for cross-platform compatibility

### 6.6 Security

- **NFR-6.1**: No storage of user credentials (no API keys required)
- **NFR-6.2**: Claude CLI subprocesses run with restricted permissions
- **NFR-6.3**: Input validation prevents command injection in subprocess calls
- **NFR-6.4**: Log files don't contain sensitive user data (sanitize coordinates if needed)

## 7. Constraints & Assumptions

### 7.1 Technical Constraints

- **C-1.1**: **No External API Keys**: System must function entirely without requiring users to provide API keys for YouTube, Spotify, Google Maps, or any other services
- **C-1.2**: **Python 3.10+**: Minimum Python version is 3.10 (for modern type hints and match statements)
- **C-1.3**: **UV Package Manager**: Project must be managed with UV (not pip-tools or poetry)
- **C-1.4**: **Claude CLI Dependency**: System requires Claude CLI installed and authenticated on the user's machine
- **C-1.5**: **Open Source Routing**: Must use OSRM or other free routing services (no commercial APIs)

### 7.2 Design Constraints

- **C-2.1**: **Package Structure**: Must be installable via `pip install` with proper `pyproject.toml`
- **C-2.2**: **Parallel Architecture**: Must use multiprocessing for content agents (architectural requirement, not just optimization)
- **C-2.3**: **Queue-Based Communication**: Agents must communicate via queues (no direct function calls between agents)
- **C-2.4**: **Logging as First-Class Feature**: Logging is a core requirement, not an afterthought (supports self-diagnosis)

### 7.3 Business Constraints

- **C-3.1**: **University Assignment**: Designed for educational purposes, demonstrating multi-agent systems and parallel processing
- **C-3.2**: **Israeli Routes Focus**: Test suite focuses on 10 Israeli routes (but system should work globally)
- **C-3.3**: **Solo Development**: Designed for single developer implementation (not a team project)

### 7.4 Assumptions

- **A-1**: Users have Claude CLI installed and properly authenticated
- **A-2**: Users have stable internet connection for OSRM and Claude API calls
- **A-3**: OSRM service (osrm.org or self-hosted) is available and responsive
- **A-4**: Claude API has sufficient rate limits for typical usage (30-50 calls per route)
- **A-5**: Users are comfortable with command-line interfaces (no GUI required)
- **A-6**: Target routes are in regions with documented POIs (rural/remote routes may have limited content)
- **A-7**: English is acceptable as the primary language for content (no i18n in v1.0)

## 8. Out of Scope

The following features are explicitly **NOT** included in version 1.0:

### 8.1 Real-Time Features
- **OS-1.1**: GPS integration and real-time location tracking during actual driving
- **OS-1.2**: Dynamic route recalculation based on traffic or detours
- **OS-1.3**: Automatic content delivery triggered by actual vehicle location
- **OS-1.4**: Mobile app with real-time notifications

### 8.2 Advanced Content Features
- **OS-2.1**: Streaming or downloading actual YouTube videos
- **OS-2.2**: Playing Spotify music within the application
- **OS-2.3**: Text-to-speech narration of historical content
- **OS-2.4**: Image/photo discovery for POIs
- **OS-2.5**: User-generated content or reviews

### 8.3 Social & Sharing Features
- **OS-3.1**: Sharing routes with other users
- **OS-3.2**: Social media integration
- **OS-3.3**: User accounts or profiles
- **OS-3.4**: Collaborative route planning

### 8.4 Advanced AI Features
- **OS-4.1**: Fine-tuned models for specific agent tasks
- **OS-4.2**: Reinforcement learning to improve Judge agent over time
- **OS-4.3**: Personalization based on user preferences or history
- **OS-4.4**: Multi-language content generation

### 8.5 Commercial Features
- **OS-5.1**: Paid API integrations (Google Maps API, official YouTube API, etc.)
- **OS-5.2**: Monetization or advertising
- **OS-5.3**: Enterprise features (SSO, team accounts, etc.)
- **OS-5.4**: SLA guarantees or commercial support

### 8.6 Platform Features
- **OS-6.1**: Web interface or GUI
- **OS-6.2**: Mobile app (iOS/Android)
- **OS-6.3**: Browser extension
- **OS-6.4**: Desktop application (beyond CLI)

### 8.7 Data Features
- **OS-7.1**: Database for storing routes or content
- **OS-7.2**: Caching of Claude API responses across sessions
- **OS-7.3**: Analytics or usage tracking
- **OS-7.4**: User feedback collection within the app

## 9. Timeline & Milestones

### Phase 1: Project Setup & Infrastructure (Week 1)
**Deliverables**:
- Initialize UV project with proper `pyproject.toml`
- Set up package structure (`src/tour_guide/` layout)
- Configure logging system with rotation
- Implement configuration management (YAML/TOML)
- Write basic CLI skeleton using `click` or `typer`

**Success Criteria**:
- `uv pip install -e .` works without errors
- `tour-guide --help` displays usage information
- Logs rotate correctly with configurable parameters

### Phase 2: Routing System (Week 1-2)
**Deliverables**:
- OSRM integration (HTTP requests to osrm.org)
- Claude fallback routing implementation
- Geocoding for place names (convert to coordinates)
- Route data parser (extract waypoints, landmarks)
- Unit tests for routing module

**Success Criteria**:
- Successfully routes between all 10 Israeli test routes
- Falls back to Claude when OSRM fails (tested by mocking failures)
- Returns structured route data with at least 20 waypoints

### Phase 3: Route Analyzer Agent (Week 2)
**Deliverables**:
- Claude CLI subprocess wrapper
- Route analysis logic (select 10 POIs)
- POI data structure (name, coords, description, category)
- Integration tests with real routes

**Success Criteria**:
- Produces 10 well-distributed POIs for typical routes
- Executes in <10 seconds
- Handles edge cases (short routes, remote areas)

### Phase 4: Content Agent Framework (Week 2-3)
**Deliverables**:
- Base `ContentAgent` class
- Multiprocessing setup (process pool, queues)
- Timeout mechanisms
- Error handling and retry logic
- Agent logging framework

**Success Criteria**:
- Framework supports spawning multiple agent processes
- Queues correctly pass data between agents
- Timeouts terminate hung processes without crashing system

### Phase 5: Content Agents Implementation (Week 3-4)
**Deliverables**:
- YouTube Agent (video search simulation)
- Spotify Agent (music recommendations)
- History Agent (historical narrative generation)
- Unit tests for each agent
- Integration tests for parallel execution

**Success Criteria**:
- All three agents execute in parallel
- At least 2 out of 3 agents succeed for each POI
- Parallel execution achieves >2.5x speedup

### Phase 6: Judge Agent (Week 4)
**Deliverables**:
- Judge Agent implementation
- Evaluation criteria (relevance, quality, uniqueness)
- Decision logging with reasoning
- Integration with content agent pipeline

**Success Criteria**:
- Produces valid selection for 100% of POIs
- Executes in <5 seconds per POI
- Provides clear reasoning for each decision

### Phase 7: Output Formats (Week 5)
**Deliverables**:
- Rich CLI display with progress bars
- Simulated journey with 5-second delays
- JSON export functionality
- Markdown report generation
- Output validation (JSON schema)

**Success Criteria**:
- CLI displays progress accurately
- JSON exports are valid and complete
- Markdown reports are well-formatted

### Phase 8: Self-Diagnosis System (Week 5-6)
**Deliverables**:
- Log parsing module
- Pattern detection algorithms (frequent errors, performance issues)
- Claude-based log analysis
- Diagnostic report generation
- `tour-guide diagnose` CLI command

**Success Criteria**:
- Correctly identifies common issues (verified by injection)
- Provides actionable recommendations
- Executes in <30 seconds for 24 hours of logs

### Phase 9: Testing & Documentation (Week 6)
**Deliverables**:
- Comprehensive unit tests (80%+ coverage)
- Integration tests (end-to-end workflows)
- API documentation (docstrings)
- User guide (README.md)
- Developer guide (CONTRIBUTING.md)
- Example outputs (JSON, Markdown samples)

**Success Criteria**:
- All tests pass on Linux, macOS, Windows
- Code coverage >80%
- Documentation covers all user-facing features

### Phase 10: Validation & Release (Week 7)
**Deliverables**:
- Test all 10 Israeli routes end-to-end
- Performance benchmarking
- Bug fixes from testing phase
- Release package to PyPI (or private repository)
- Demo video or presentation

**Success Criteria**:
- System successfully processes all 10 test routes
- Performance meets NFRs (<2 minutes per route)
- Package installs correctly via `pip install tour-guide`
- Zero critical bugs remaining

---

## Appendix A: Test Routes

The following 10 Israeli routes will be used for validation and testing:

1. **Tel Aviv → Jerusalem** (Urban to historic, ~65 km)
2. **Haifa → Akko** (Coastal cities, ~20 km)
3. **Tel Aviv → Eilat** (Long distance, desert, ~350 km)
4. **Jerusalem → Dead Sea** (Mountains to lowest point on Earth, ~40 km)
5. **Nazareth → Tiberias** (Religious sites, Sea of Galilee, ~35 km)
6. **Tel Aviv → Caesarea** (Coastal, Roman ruins, ~50 km)
7. **Beer Sheva → Masada** (Desert, historic fortress, ~90 km)
8. **Haifa → Rosh Hanikra** (Coastal, grottoes, ~35 km)
9. **Jerusalem → Bethlehem** (Religious sites, short distance, ~10 km)
10. **Tel Aviv → Jaffa** (Urban, very short, ~5 km)

These routes provide diverse test cases:
- Urban, coastal, desert, mountainous terrain
- Short (<10 km), medium (20-100 km), and long (>300 km) distances
- High POI density (Tel Aviv-Jerusalem) vs. low density (Tel Aviv-Eilat)
- Religious, historical, natural, and cultural POIs

---

## Appendix B: Technology Stack

### Core Dependencies
- **Python**: 3.10+ (required)
- **UV**: Package manager
- **click** or **typer**: CLI framework
- **rich**: Terminal formatting and progress bars
- **requests**: HTTP client for OSRM
- **pyyaml** or **toml**: Configuration file parsing
- **jsonschema**: JSON validation

### Standard Library Modules
- **multiprocessing**: Parallel execution
- **queue**: Inter-process communication
- **logging**: Logging framework
- **subprocess**: Claude CLI subprocess calls
- **pathlib**: Cross-platform file paths
- **json**: JSON parsing and serialization
- **datetime**: Timestamps

### External Services
- **OSRM**: Routing (osrm.org or self-hosted)
- **Claude CLI**: AI agent intelligence (via subprocess)

### Development Dependencies
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **ruff** or **black**: Code formatting
- **mypy**: Type checking

---

## Appendix C: Configuration Example

Example `config.yaml`:

```yaml
# Logging configuration
logging:
  max_bytes: 10485760  # 10 MB
  backup_count: 5
  level: INFO
  format: json

# Routing configuration
routing:
  osrm_url: "http://router.project-osrm.org"
  fallback_to_claude: true
  timeout_seconds: 10

# Agent configuration
agents:
  content_agent_timeout: 30
  judge_agent_timeout: 10
  max_retries: 2

# Claude CLI configuration
claude:
  model: "claude-sonnet-4"
  max_tokens: 4000
  temperature: 0.7

# Output configuration
output:
  journey_delay_seconds: 5
  default_json_path: "./output/journey.json"
  default_markdown_path: "./output/journey.md"

# POI configuration
poi:
  count: 10
  min_distance_between_km: 5
  categories:
    - historical
    - cultural
    - natural
    - religious
    - entertainment
```

---

**Document Version**: 1.0
**Last Updated**: 2025-12-02
**Author**: Tour Guide Development Team
**Status**: Approved for Implementation

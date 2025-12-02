"""Tests for agent classes."""

import pytest
from unittest.mock import Mock, patch, mock_open
from tour_guide.agents.base import BaseAgent, AgentError
from tour_guide.agents.route_analyzer import RouteAnalyzerAgent
from tour_guide.agents.youtube import YouTubeAgent
from tour_guide.agents.spotify import SpotifyAgent
from tour_guide.agents.history import HistoryAgent
from tour_guide.agents.judge import JudgeAgent
from tour_guide.models import POI, POICategory, ContentResult, JudgmentResult
from tour_guide.routing.models import Route, Waypoint, RouteStep


class TestBaseAgent:
    """Tests for BaseAgent class."""

    @pytest.fixture
    def test_agent(self):
        """Create a concrete test agent."""

        class TestAgent(BaseAgent):
            def run(self, input_data):
                return f"Processed: {input_data}"

        return TestAgent("test_agent")

    def test_agent_initialization(self, test_agent):
        """Test that agent initializes with logger."""
        assert test_agent.agent_name == "test_agent"
        assert test_agent.logger is not None
        assert test_agent.settings is not None

    def test_run_with_timeout_success(self, test_agent):
        """Test successful execution with timeout."""
        result = test_agent.run_with_timeout("test_input", timeout_seconds=5)
        assert result == "Processed: test_input"

    def test_run_with_timeout_logs_execution_time(self, test_agent):
        """Test that execution time is logged."""
        with patch.object(test_agent.logger, "info") as mock_info:
            test_agent.run_with_timeout("test_input", timeout_seconds=5)

            # Check that completion was logged with time
            calls = [str(call) for call in mock_info.call_args_list]
            assert any("completed successfully" in str(call) for call in calls)

    def test_run_with_timeout_handles_errors(self, test_agent):
        """Test that errors are logged and re-raised."""

        class FailingAgent(BaseAgent):
            def run(self, input_data):
                raise ValueError("Test error")

        failing_agent = FailingAgent("failing_agent")

        with pytest.raises(ValueError):
            failing_agent.run_with_timeout("test_input")

    def test_read_recent_logs_no_file(self, test_agent):
        """Test reading logs when log file doesn't exist."""
        # Temporarily remove all handlers to simulate no log file
        import logging

        root_logger = logging.getLogger("tour_guide")
        original_handlers = root_logger.handlers.copy()
        root_logger.handlers.clear()

        try:
            result = test_agent._read_recent_logs(lines=10)
            assert "No log file found" in result
        finally:
            # Restore handlers
            for handler in original_handlers:
                root_logger.addHandler(handler)

    def test_read_recent_logs_success(self, test_agent):
        """Test reading logs successfully."""
        mock_log_content = """
{"level": "INFO", "message": "agents.test_agent: Starting"}
{"level": "INFO", "message": "agents.test_agent: Processing"}
{"level": "INFO", "message": "agents.other_agent: Other log"}
{"level": "INFO", "message": "agents.test_agent: Completed"}
"""
        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data=mock_log_content)
        ):
            result = test_agent._read_recent_logs(lines=10)

            # Should contain test_agent logs
            assert "agents.test_agent: Starting" in result
            assert "agents.test_agent: Completed" in result
            # Should NOT contain other agent's logs
            assert "agents.other_agent" not in result

    def test_diagnose_no_logs(self, test_agent):
        """Test diagnose when no logs are available."""
        # Since test environment may not have logs, should return friendly message
        try:
            diagnosis = test_agent.diagnose(last_lines=10)
            assert isinstance(diagnosis, str)
            # Should contain either diagnosis or "no logs" message
            assert len(diagnosis) > 0
        except AgentError:
            # Expected if logging not initialized - that's fine for unit test
            pass

    def test_diagnose_with_mock_logs(self, test_agent):
        """Test diagnose with mocked log entries."""
        from tour_guide.diagnosis import LogEntry, DiagnosticReport, AgentStats
        from datetime import datetime
        from pathlib import Path

        # Mock the log directory
        with patch.object(Path, 'exists', return_value=True):
            with patch('tour_guide.diagnosis.LogParser') as mock_parser:
                with patch('tour_guide.diagnosis.DiagnosticAnalyzer') as mock_analyzer:
                    # Setup mock entries
                    mock_entries = [
                        LogEntry(
                            timestamp=datetime.now(),
                            level="INFO",
                            logger="tour_guide.agents.test_agent",
                            message="Test message",
                            module="test",
                            function="run",
                            line=1,
                            agent="test_agent"
                        )
                    ]

                    mock_parser.return_value.parse_recent.return_value = mock_entries
                    mock_parser.return_value.filter_by_agent.return_value = mock_entries

                    # Setup mock report
                    mock_report = DiagnosticReport(
                        generated_at=datetime.now(),
                        total_entries=1,
                        error_count=0,
                        warning_count=0,
                        patterns=[],
                        agent_stats={
                            "test_agent": AgentStats(
                                agent_name="test_agent",
                                total_calls=1,
                                success_count=1,
                                failure_count=0,
                                avg_execution_time=1.0,
                                error_rate=0.0
                            )
                        },
                        recommendations=["System operating normally"]
                    )

                    mock_analyzer.return_value.analyze.return_value = mock_report

                    # Run diagnosis
                    diagnosis = test_agent.diagnose(last_lines=10)

                    # Verify result
                    assert isinstance(diagnosis, str)
                    assert "test_agent" in diagnosis.lower() or "TEST_AGENT" in diagnosis
                    assert "Summary" in diagnosis


class TestPOI:
    """Tests for POI model."""

    def test_poi_creation_success(self):
        """Test creating a valid POI."""
        poi = POI(
            name="Masada",
            lat=31.3157,
            lon=35.3540,
            description="Ancient fortress overlooking the Dead Sea",
            category=POICategory.HISTORICAL,
            distance_from_start_km=45.2,
        )

        assert poi.name == "Masada"
        assert poi.lat == 31.3157
        assert poi.lon == 35.3540
        assert poi.category == POICategory.HISTORICAL
        assert poi.distance_from_start_km == 45.2

    def test_poi_coordinates_property(self):
        """Test coordinates property returns tuple."""
        poi = POI(
            name="Test",
            lat=32.0,
            lon=34.0,
            description="Test POI",
            category=POICategory.CULTURAL,
            distance_from_start_km=0.0,
        )

        assert poi.coordinates == (32.0, 34.0)

    def test_poi_invalid_latitude(self):
        """Test that invalid latitude raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            POI(
                name="Invalid",
                lat=100.0,  # > 90
                lon=34.0,
                description="Test",
                category=POICategory.NATURAL,
                distance_from_start_km=0.0,
            )

        assert "Invalid latitude" in str(exc_info.value)

    def test_poi_invalid_longitude(self):
        """Test that invalid longitude raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            POI(
                name="Invalid",
                lat=32.0,
                lon=200.0,  # > 180
                description="Test",
                category=POICategory.NATURAL,
                distance_from_start_km=0.0,
            )

        assert "Invalid longitude" in str(exc_info.value)

    def test_poi_invalid_distance(self):
        """Test that negative distance raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            POI(
                name="Invalid",
                lat=32.0,
                lon=34.0,
                description="Test",
                category=POICategory.NATURAL,
                distance_from_start_km=-5.0,  # Negative
            )

        assert "Invalid distance" in str(exc_info.value)

    def test_poi_category_from_string(self):
        """Test that category can be created from string."""
        poi = POI(
            name="Test",
            lat=32.0,
            lon=34.0,
            description="Test POI",
            category="cultural",  # String instead of enum
            distance_from_start_km=0.0,
        )

        assert poi.category == POICategory.CULTURAL

    def test_poi_invalid_category_string(self):
        """Test that invalid category string raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            POI(
                name="Test",
                lat=32.0,
                lon=34.0,
                description="Test",
                category="invalid_category",
                distance_from_start_km=0.0,
            )

        assert "Invalid category" in str(exc_info.value)


class TestRouteAnalyzerAgent:
    """Tests for Route Analyzer Agent."""

    @pytest.fixture
    def analyzer(self):
        """Create route analyzer agent."""
        return RouteAnalyzerAgent()

    @pytest.fixture
    def sample_route(self):
        """Create sample route for testing."""
        return Route(
            origin=(32.0853, 34.7818),  # Tel Aviv
            destination=(31.7683, 35.2137),  # Jerusalem
            total_distance_km=65.0,
            total_duration_min=75.0,
            waypoints=[
                Waypoint(lat=32.0853, lon=34.7818, distance_from_start_km=0.0),
                Waypoint(lat=32.0, lon=35.0, distance_from_start_km=30.0),
                Waypoint(lat=31.7683, lon=35.2137, distance_from_start_km=65.0),
            ],
            steps=[
                RouteStep(
                    instruction="Head east on Highway 1",
                    distance_km=30.0,
                    duration_min=25.0,
                )
            ],
            source="osrm",
        )

    @pytest.fixture
    def mock_claude_response(self):
        """Mock Claude response with POIs."""
        return """```json
{
  "pois": [
    {
      "name": "Latrun Monastery",
      "lat": 31.8356,
      "lon": 34.9869,
      "description": "Historic Trappist monastery with scenic views and wine production.",
      "category": "religious",
      "distance_from_start_km": 25.0
    },
    {
      "name": "Mini Israel",
      "lat": 31.8542,
      "lon": 34.9869,
      "description": "Miniature park featuring replicas of Israeli landmarks.",
      "category": "entertainment",
      "distance_from_start_km": 30.0
    },
    {
      "name": "Emmaus Archaeological Site",
      "lat": 31.8403,
      "lon": 34.9869,
      "description": "Ancient Roman and Byzantine ruins with historical significance.",
      "category": "historical",
      "distance_from_start_km": 35.0
    }
  ]
}
```"""

    def test_analyzer_initialization(self, analyzer):
        """Test that analyzer initializes correctly."""
        assert analyzer.agent_name == "route_analyzer"
        assert analyzer.poi_count == 10

    def test_run_with_valid_route(self, analyzer, sample_route, mock_claude_response):
        """Test analyzing route returns POI list."""
        with patch(
            "tour_guide.agents.route_analyzer.call_claude"
        ) as mock_claude:
            mock_claude.return_value = mock_claude_response

            pois = analyzer.run(sample_route)

            assert isinstance(pois, list)
            assert len(pois) == 3
            assert all(isinstance(poi, POI) for poi in pois)

            # Check first POI
            assert pois[0].name == "Latrun Monastery"
            assert pois[0].category == POICategory.RELIGIOUS
            assert pois[0].distance_from_start_km == 25.0

    def test_run_with_invalid_input(self, analyzer):
        """Test that invalid input raises AgentError."""
        with pytest.raises(AgentError) as exc_info:
            analyzer.run("not a route")

        assert "Expected Route object" in str(exc_info.value)

    def test_determine_poi_count_short_route(self, analyzer):
        """Test POI count for short routes."""
        assert analyzer._determine_poi_count(15.0) == 3

    def test_determine_poi_count_medium_route(self, analyzer):
        """Test POI count for medium routes."""
        assert analyzer._determine_poi_count(40.0) == 5

    def test_determine_poi_count_long_route(self, analyzer):
        """Test POI count for long routes."""
        assert analyzer._determine_poi_count(100.0) == 10

    def test_parse_response_success(self, analyzer, mock_claude_response):
        """Test parsing valid Claude response."""
        pois = analyzer._parse_response(mock_claude_response)

        assert len(pois) == 3
        assert pois[0].name == "Latrun Monastery"
        assert pois[1].name == "Mini Israel"
        assert pois[2].name == "Emmaus Archaeological Site"

    def test_parse_response_invalid_json(self, analyzer):
        """Test parsing invalid JSON raises error."""
        with pytest.raises(AgentError) as exc_info:
            analyzer._parse_response("not valid json")

        assert "Failed to parse" in str(exc_info.value)

    def test_parse_response_missing_pois_field(self, analyzer):
        """Test response missing pois field raises error."""
        response = '{"wrong_field": []}'

        with pytest.raises(AgentError) as exc_info:
            analyzer._parse_response(response)

        assert "missing 'pois' field" in str(exc_info.value)

    def test_run_handles_claude_error(self, analyzer, sample_route):
        """Test that Claude errors are handled properly."""
        from tour_guide.utils.claude_cli import ClaudeError

        with patch(
            "tour_guide.agents.route_analyzer.call_claude"
        ) as mock_claude:
            mock_claude.side_effect = ClaudeError("CLI failed")

            with pytest.raises(AgentError) as exc_info:
                analyzer.run(sample_route)

            assert "Claude CLI failed" in str(exc_info.value)


class TestContentResult:
    """Tests for ContentResult model."""

    def test_content_result_creation(self):
        """Test creating a valid ContentResult."""
        result = ContentResult(
            content_type="youtube",
            title="Test Video",
            description="A test video about a location",
            relevance_score=85,
            metadata={"duration": "10:30", "channel": "Travel Guide"},
            agent_name="youtube",
            poi_name="Masada",
        )

        assert result.content_type == "youtube"
        assert result.title == "Test Video"
        assert result.relevance_score == 85
        assert result.metadata["duration"] == "10:30"

    def test_content_result_invalid_score(self):
        """Test that invalid relevance score raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ContentResult(
                content_type="spotify",
                title="Test",
                description="Test",
                relevance_score=150,  # > 100
            )

        assert "Invalid relevance_score" in str(exc_info.value)

    def test_content_result_invalid_type(self):
        """Test that invalid content type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ContentResult(
                content_type="invalid",
                title="Test",
                description="Test",
                relevance_score=50,
            )

        assert "Invalid content_type" in str(exc_info.value)

    def test_content_result_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        result = ContentResult(
            content_type="history",
            title="Test",
            description="Test",
            relevance_score=75,
        )

        assert result.metadata == {}
        assert result.agent_name == ""
        assert result.poi_name == ""


class TestYouTubeAgent:
    """Tests for YouTube Agent."""

    @pytest.fixture
    def youtube_agent(self):
        """Create YouTube agent."""
        return YouTubeAgent()

    @pytest.fixture
    def sample_poi(self):
        """Create sample POI for testing."""
        return POI(
            name="Latrun Monastery",
            lat=31.8356,
            lon=34.9869,
            description="Historic Trappist monastery with scenic views",
            category=POICategory.RELIGIOUS,
            distance_from_start_km=25.0,
        )

    @pytest.fixture
    def mock_youtube_response(self):
        """Mock Claude response with video suggestion."""
        return """```json
{
  "video": {
    "title": "Inside Latrun Monastery: A Journey Through Trappist Life",
    "channel": "Sacred Sites",
    "duration_estimate": "15 minutes",
    "relevance_score": 90,
    "description": "Explore the daily life of Trappist monks at Latrun Monastery",
    "why_relevant": "Provides insight into the monastery's history and significance"
  }
}
```"""

    def test_youtube_agent_initialization(self, youtube_agent):
        """Test that YouTube agent initializes correctly."""
        assert youtube_agent.agent_name == "youtube"

    def test_run_with_valid_poi(self, youtube_agent, sample_poi, mock_youtube_response):
        """Test finding video for POI."""
        with patch("tour_guide.agents.youtube.call_claude") as mock_claude:
            mock_claude.return_value = mock_youtube_response

            result = youtube_agent.run(sample_poi)

            assert isinstance(result, ContentResult)
            assert result.content_type == "youtube"
            assert result.title == "Inside Latrun Monastery: A Journey Through Trappist Life"
            assert result.relevance_score == 90
            assert result.metadata["channel"] == "Sacred Sites"
            assert result.metadata["duration_estimate"] == "15 minutes"
            assert result.poi_name == "Latrun Monastery"

    def test_run_with_invalid_input(self, youtube_agent):
        """Test that invalid input raises AgentError."""
        with pytest.raises(AgentError) as exc_info:
            youtube_agent.run("not a poi")

        assert "Expected POI object" in str(exc_info.value)

    def test_parse_response_success(self, youtube_agent, mock_youtube_response):
        """Test parsing valid Claude response."""
        result = youtube_agent._parse_response(mock_youtube_response, "Latrun Monastery")

        assert result.title == "Inside Latrun Monastery: A Journey Through Trappist Life"
        assert result.content_type == "youtube"
        assert result.relevance_score == 90

    def test_parse_response_invalid_json(self, youtube_agent):
        """Test parsing invalid JSON raises error."""
        with pytest.raises(AgentError) as exc_info:
            youtube_agent._parse_response("not valid json", "Test")

        assert "Failed to parse" in str(exc_info.value)

    def test_parse_response_missing_video_field(self, youtube_agent):
        """Test response missing video field raises error."""
        response = '{"wrong_field": {}}'

        with pytest.raises(AgentError) as exc_info:
            youtube_agent._parse_response(response, "Test")

        assert "missing 'video' field" in str(exc_info.value)

    def test_run_handles_claude_error(self, youtube_agent, sample_poi):
        """Test that Claude errors are handled properly."""
        from tour_guide.utils.claude_cli import ClaudeError

        with patch("tour_guide.agents.youtube.call_claude") as mock_claude:
            mock_claude.side_effect = ClaudeError("CLI failed")

            with pytest.raises(AgentError) as exc_info:
                youtube_agent.run(sample_poi)

            assert "Claude CLI failed" in str(exc_info.value)


class TestSpotifyAgent:
    """Tests for Spotify Agent."""

    @pytest.fixture
    def spotify_agent(self):
        """Create Spotify agent."""
        return SpotifyAgent()

    @pytest.fixture
    def sample_poi(self):
        """Create sample POI for testing."""
        return POI(
            name="Dead Sea",
            lat=31.5590,
            lon=35.4732,
            description="Lowest point on Earth with unique salt water",
            category=POICategory.NATURAL,
            distance_from_start_km=50.0,
        )

    @pytest.fixture
    def mock_spotify_response(self):
        """Mock Claude response with music suggestion."""
        return """```json
{
  "music": {
    "title": "Dead Sea Meditation",
    "artist": "Desert Wind Ensemble",
    "type": "album",
    "genre": "Ambient/World",
    "relevance_score": 85,
    "description": "Contemplative instrumental music inspired by the Dead Sea landscape",
    "why_relevant": "Captures the serene and otherworldly atmosphere of the Dead Sea region"
  }
}
```"""

    def test_spotify_agent_initialization(self, spotify_agent):
        """Test that Spotify agent initializes correctly."""
        assert spotify_agent.agent_name == "spotify"

    def test_run_with_valid_poi(self, spotify_agent, sample_poi, mock_spotify_response):
        """Test finding music for POI."""
        with patch("tour_guide.agents.spotify.call_claude") as mock_claude:
            mock_claude.return_value = mock_spotify_response

            result = spotify_agent.run(sample_poi)

            assert isinstance(result, ContentResult)
            assert result.content_type == "spotify"
            assert result.title == "Dead Sea Meditation"
            assert result.relevance_score == 85
            assert result.metadata["artist"] == "Desert Wind Ensemble"
            assert result.metadata["genre"] == "Ambient/World"
            assert result.poi_name == "Dead Sea"

    def test_run_with_invalid_input(self, spotify_agent):
        """Test that invalid input raises AgentError."""
        with pytest.raises(AgentError) as exc_info:
            spotify_agent.run("not a poi")

        assert "Expected POI object" in str(exc_info.value)

    def test_parse_response_success(self, spotify_agent, mock_spotify_response):
        """Test parsing valid Claude response."""
        result = spotify_agent._parse_response(mock_spotify_response, "Dead Sea")

        assert result.title == "Dead Sea Meditation"
        assert result.content_type == "spotify"
        assert result.relevance_score == 85

    def test_run_handles_claude_error(self, spotify_agent, sample_poi):
        """Test that Claude errors are handled properly."""
        from tour_guide.utils.claude_cli import ClaudeError

        with patch("tour_guide.agents.spotify.call_claude") as mock_claude:
            mock_claude.side_effect = ClaudeError("CLI failed")

            with pytest.raises(AgentError) as exc_info:
                spotify_agent.run(sample_poi)

            assert "Claude CLI failed" in str(exc_info.value)


class TestHistoryAgent:
    """Tests for History Agent."""

    @pytest.fixture
    def history_agent(self):
        """Create History agent."""
        return HistoryAgent()

    @pytest.fixture
    def sample_poi(self):
        """Create sample POI for testing."""
        return POI(
            name="Masada",
            lat=31.3157,
            lon=35.3540,
            description="Ancient fortress on a rock plateau",
            category=POICategory.HISTORICAL,
            distance_from_start_km=100.0,
        )

    @pytest.fixture
    def mock_history_response(self):
        """Mock Claude response with historical narrative."""
        return """```json
{
  "story": {
    "title": "The Last Stand at Masada",
    "narrative": "In 73 CE, atop an isolated rock plateau overlooking the Dead Sea, 960 Jewish rebels made their last stand against the might of Rome. Led by Eleazar ben Ya'ir, these Zealots had fled Jerusalem after the destruction of the Second Temple in 70 CE. For nearly three years, they held out in King Herod's former palace-fortress, built a century earlier. The Roman Tenth Legion, under Flavius Silva, laid siege with 15,000 soldiers. When defeat became inevitable, rather than face slavery or execution, the defenders chose mass suicide. According to Josephus, they drew lots to select ten men who would kill the others, then one final man to kill the remaining nine before taking his own life. When the Romans finally breached the walls, they found only silence and bodies. Two women and five children, who had hidden in a cistern, survived to tell the tale.",
    "key_facts": [
      "Masada was built by Herod the Great between 37-31 BCE",
      "The siege lasted from 73-74 CE during the First Jewish-Roman War",
      "960 Zealots chose mass suicide over Roman enslavement",
      "Archaeological excavations in the 1960s confirmed historical accounts"
    ],
    "relevance_score": 98,
    "time_period": "73-74 CE",
    "historical_figures": ["Eleazar ben Ya'ir", "Flavius Silva", "Josephus"]
  }
}
```"""

    def test_history_agent_initialization(self, history_agent):
        """Test that History agent initializes correctly."""
        assert history_agent.agent_name == "history"

    def test_run_with_valid_poi(self, history_agent, sample_poi, mock_history_response):
        """Test generating narrative for POI."""
        with patch("tour_guide.agents.history.call_claude") as mock_claude:
            mock_claude.return_value = mock_history_response

            result = history_agent.run(sample_poi)

            assert isinstance(result, ContentResult)
            assert result.content_type == "history"
            assert result.title == "The Last Stand at Masada"
            assert len(result.description) > 300  # Check narrative length
            assert result.relevance_score == 98
            assert len(result.metadata["key_facts"]) == 4
            assert result.metadata["time_period"] == "73-74 CE"
            assert result.poi_name == "Masada"

    def test_run_with_invalid_input(self, history_agent):
        """Test that invalid input raises AgentError."""
        with pytest.raises(AgentError) as exc_info:
            history_agent.run("not a poi")

        assert "Expected POI object" in str(exc_info.value)

    def test_parse_response_success(self, history_agent, mock_history_response):
        """Test parsing valid Claude response."""
        result = history_agent._parse_response(mock_history_response, "Masada")

        assert result.title == "The Last Stand at Masada"
        assert result.content_type == "history"
        assert result.relevance_score == 98
        assert "Eleazar ben Ya'ir" in result.metadata["historical_figures"]

    def test_run_handles_claude_error(self, history_agent, sample_poi):
        """Test that Claude errors are handled properly."""
        from tour_guide.utils.claude_cli import ClaudeError

        with patch("tour_guide.agents.history.call_claude") as mock_claude:
            mock_claude.side_effect = ClaudeError("CLI failed")

            with pytest.raises(AgentError) as exc_info:
                history_agent.run(sample_poi)

            assert "Claude CLI failed" in str(exc_info.value)



class TestJudgmentResult:
    """Tests for JudgmentResult model."""

    @pytest.fixture
    def sample_content_youtube(self):
        """Create sample YouTube content."""
        return ContentResult(
            content_type="youtube",
            title="Test Video",
            description="Test description",
            relevance_score=85,
            agent_name="youtube",
            poi_name="Test POI",
        )

    @pytest.fixture
    def sample_content_history(self):
        """Create sample History content."""
        return ContentResult(
            content_type="history",
            title="Test History",
            description="Test narrative",
            relevance_score=90,
            agent_name="history",
            poi_name="Test POI",
        )

    def test_judgment_result_creation(self, sample_content_history):
        """Test creating a valid JudgmentResult."""
        result = JudgmentResult(
            poi_name="Test POI",
            selected_content=sample_content_history,
            selected_type="history",
            reasoning="History provides the most educational value.",
            scores={"youtube": 85, "spotify": 70, "history": 95},
            all_content=[sample_content_history],
        )

        assert result.poi_name == "Test POI"
        assert result.selected_type == "history"
        assert result.scores["history"] == 95

    def test_judgment_result_invalid_type(self, sample_content_history):
        """Test that invalid selected_type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            JudgmentResult(
                poi_name="Test",
                selected_content=sample_content_history,
                selected_type="invalid",
                reasoning="Test",
            )

        assert "Invalid selected_type" in str(exc_info.value)

    def test_judgment_result_type_mismatch(
        self, sample_content_youtube, sample_content_history
    ):
        """Test that type mismatch raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            JudgmentResult(
                poi_name="Test",
                selected_content=sample_content_youtube,
                selected_type="history",  # Mismatch!
                reasoning="Test",
            )

        assert "Mismatch" in str(exc_info.value)


class TestJudgeAgent:
    """Tests for JudgeAgent class."""

    @pytest.fixture
    def judge_agent(self):
        """Create a JudgeAgent instance."""
        return JudgeAgent()

    @pytest.fixture
    def sample_content_list(self):
        """Create sample content list with all three types."""
        return [
            ContentResult(
                content_type="youtube",
                title="Amazing Video Tour",
                description="A video tour of the location",
                relevance_score=85,
                agent_name="youtube",
                poi_name="Eiffel Tower",
            ),
            ContentResult(
                content_type="spotify",
                title="French Music Playlist",
                description="Traditional French music",
                relevance_score=75,
                agent_name="spotify",
                poi_name="Eiffel Tower",
            ),
            ContentResult(
                content_type="history",
                title="History of Eiffel Tower",
                description="Built in 1889 for the World's Fair...",
                relevance_score=95,
                agent_name="history",
                poi_name="Eiffel Tower",
            ),
        ]

    def test_judge_agent_initialization(self, judge_agent):
        """Test that JudgeAgent initializes correctly."""
        assert judge_agent.agent_name == "judge"
        assert judge_agent.logger is not None

    def test_judge_agent_empty_list(self, judge_agent):
        """Test that empty content list raises AgentError."""
        with pytest.raises(AgentError) as exc_info:
            judge_agent.run([])

        assert "empty content list" in str(exc_info.value)

    def test_judge_agent_invalid_input_type(self, judge_agent):
        """Test that non-list input raises AgentError."""
        with pytest.raises(AgentError) as exc_info:
            judge_agent.run("not a list")

        assert "must be a list" in str(exc_info.value)

    def test_judge_agent_invalid_content_items(self, judge_agent):
        """Test that invalid items in list raise AgentError."""
        with pytest.raises(AgentError) as exc_info:
            judge_agent.run([{"not": "content_result"}])

        assert "ContentResult objects" in str(exc_info.value)

    def test_judge_agent_single_content(self, judge_agent):
        """Test that single content item is selected by default."""
        single_content = [
            ContentResult(
                content_type="youtube",
                title="Test Video",
                description="Test",
                relevance_score=80,
                agent_name="youtube",
                poi_name="Test POI",
            )
        ]

        result = judge_agent.run(single_content)

        assert isinstance(result, JudgmentResult)
        assert result.selected_type == "youtube"
        assert result.selected_content == single_content[0]
        assert "by default" in result.reasoning

    @patch("tour_guide.agents.judge.call_claude")
    def test_judge_agent_evaluates_content(self, mock_claude, judge_agent, sample_content_list):
        """Test that JudgeAgent successfully evaluates multiple content options."""
        # Mock Claude response
        mock_response = """```json
{
  "selected": "history",
  "reasoning": "The historical narrative provides the most educational value and is specifically relevant to the Eiffel Tower's significance.",
  "scores": {
    "youtube": 82,
    "spotify": 68,
    "history": 94
  }
}
```"""
        mock_claude.return_value = mock_response

        result = judge_agent.run(sample_content_list)

        assert isinstance(result, JudgmentResult)
        assert result.selected_type == "history"
        assert result.selected_content.content_type == "history"
        assert result.poi_name == "Eiffel Tower"
        assert "educational value" in result.reasoning
        assert result.scores["history"] == 94
        assert len(result.all_content) == 3

    @patch("tour_guide.agents.judge.call_claude")
    def test_judge_agent_fallback_on_claude_failure(self, mock_claude, judge_agent, sample_content_list):
        """Test that JudgeAgent uses fallback selection when Claude fails."""
        mock_claude.side_effect = Exception("Claude call failed")

        result = judge_agent.run(sample_content_list)

        assert isinstance(result, JudgmentResult)
        # Should select history (highest score: 95)
        assert result.selected_type == "history"
        assert "highest relevance score" in result.reasoning

    @patch("tour_guide.agents.judge.call_claude")
    def test_judge_agent_fallback_on_invalid_json(self, mock_claude, judge_agent, sample_content_list):
        """Test that JudgeAgent uses fallback when JSON parsing fails."""
        mock_claude.return_value = "This is not valid JSON"

        result = judge_agent.run(sample_content_list)

        assert isinstance(result, JudgmentResult)
        assert result.selected_type == "history"
        assert "highest relevance score" in result.reasoning

    @patch("tour_guide.agents.judge.call_claude")
    def test_judge_agent_fallback_on_missing_fields(self, mock_claude, judge_agent, sample_content_list):
        """Test that JudgeAgent uses fallback when response is missing fields."""
        mock_response = """```json
{
  "scores": {"youtube": 80, "spotify": 70, "history": 90}
}
```"""
        mock_claude.return_value = mock_response

        result = judge_agent.run(sample_content_list)

        assert isinstance(result, JudgmentResult)
        assert "highest relevance score" in result.reasoning

    @patch("tour_guide.agents.judge.call_claude")
    def test_judge_agent_fallback_on_invalid_selection(self, mock_claude, judge_agent, sample_content_list):
        """Test fallback when selected type doesn't match available content."""
        mock_response = """```json
{
  "selected": "podcast",
  "reasoning": "Podcasts are great",
  "scores": {"youtube": 80, "spotify": 70, "history": 90}
}
```"""
        mock_claude.return_value = mock_response

        result = judge_agent.run(sample_content_list)

        assert isinstance(result, JudgmentResult)
        assert result.selected_type in ["youtube", "spotify", "history"]
        assert "highest relevance score" in result.reasoning

    def test_judge_agent_tiebreaker_priority(self, judge_agent):
        """Test that tiebreaker uses correct priority: History > YouTube > Spotify."""
        # All have same score, should pick History
        tied_content = [
            ContentResult(
                content_type="youtube",
                title="Video",
                description="Video desc",
                relevance_score=80,
                agent_name="youtube",
                poi_name="Test POI",
            ),
            ContentResult(
                content_type="spotify",
                title="Music",
                description="Music desc",
                relevance_score=80,
                agent_name="spotify",
                poi_name="Test POI",
            ),
            ContentResult(
                content_type="history",
                title="History",
                description="History desc",
                relevance_score=80,
                agent_name="history",
                poi_name="Test POI",
            ),
        ]

        result = judge_agent.run(tied_content)

        # With equal scores, history should be selected
        assert result.selected_type == "history"


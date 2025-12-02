"""Tests for output formatters."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from tour_guide.output.cli_display import CLIDisplay
from tour_guide.output.json_export import JSONExporter
from tour_guide.output.markdown_export import MarkdownExporter
from tour_guide.routing.models import Route, Waypoint, RouteStep
from tour_guide.models.poi import POI, POICategory
from tour_guide.models.content import ContentResult
from tour_guide.models.judgment import JudgmentResult


class TestCLIDisplay:
    """Tests for CLIDisplay class."""

    @pytest.fixture
    def display(self):
        """Create CLIDisplay instance."""
        return CLIDisplay()

    @pytest.fixture
    def sample_route(self):
        """Create sample route."""
        return Route(
            origin=(32.0853, 34.7818),
            destination=(31.7683, 35.2137),
            total_distance_km=65.5,
            total_duration_min=75.0,
            waypoints=[],
            steps=[],
            source="osrm",
        )

    @pytest.fixture
    def sample_poi(self):
        """Create sample POI."""
        return POI(
            name="Latrun Monastery",
            lat=31.8356,
            lon=34.9869,
            description="Historic Trappist monastery",
            category=POICategory.RELIGIOUS,
            distance_from_start_km=25.0,
        )

    @pytest.fixture
    def sample_judgment(self, sample_poi):
        """Create sample judgment."""
        youtube_content = ContentResult(
            content_type="youtube",
            title="Latrun Monastery Tour",
            description="Video tour of the monastery",
            relevance_score=75,
            agent_name="youtube",
            poi_name=sample_poi.name,
        )

        spotify_content = ContentResult(
            content_type="spotify",
            title="Gregorian Chants",
            description="Traditional monastery music",
            relevance_score=70,
            agent_name="spotify",
            poi_name=sample_poi.name,
        )

        history_content = ContentResult(
            content_type="history",
            title="History of Latrun",
            description="The monastery was built in 1890...",
            relevance_score=85,
            agent_name="history",
            poi_name=sample_poi.name,
        )

        return JudgmentResult(
            poi_name=sample_poi.name,
            selected_content=history_content,
            selected_type="history",
            reasoning="Historical content provides the most educational value for this location.",
            scores={"youtube": 75, "spotify": 70, "history": 85},
            all_content=[youtube_content, spotify_content, history_content],
        )

    def test_display_initialization(self, display):
        """Test that CLIDisplay initializes correctly."""
        assert display.console is not None

    def test_show_progress(self, display):
        """Test progress bar display."""
        # Should not raise any exceptions
        display.show_progress("Processing", 50)
        display.show_progress("Complete", 100)

    def test_show_route_info(self, display, sample_route):
        """Test route information display."""
        # Should not raise any exceptions
        display.show_route_info(sample_route)

    def test_show_poi(self, display, sample_poi, sample_judgment):
        """Test POI display with judgment."""
        # Should not raise any exceptions
        display.show_poi(sample_poi, sample_judgment)

    def test_show_journey_with_delay_zero(self, display, sample_judgment):
        """Test journey display with no delay."""
        # Test with zero delay to make test fast
        display.show_journey([sample_judgment], delay=0)

    def test_show_summary(self, display):
        """Test summary display."""
        stats = {
            "total_pois": 10,
            "content_distribution": {"youtube": 2, "spotify": 3, "history": 5},
            "execution_time": 45.2,
        }

        # Should not raise any exceptions
        display.show_summary(stats)

    def test_print_messages(self, display):
        """Test error, warning, and info message printing."""
        display.print_error("Test error")
        display.print_warning("Test warning")
        display.print_info("Test info")


class TestJSONExporter:
    """Tests for JSONExporter class."""

    @pytest.fixture
    def exporter(self):
        """Create JSONExporter instance."""
        return JSONExporter(version="0.1.0")

    @pytest.fixture
    def sample_route(self):
        """Create sample route."""
        return Route(
            origin=(32.0853, 34.7818),
            destination=(31.7683, 35.2137),
            total_distance_km=65.5,
            total_duration_min=75.0,
            waypoints=[],
            steps=[],
            source="osrm",
        )

    @pytest.fixture
    def sample_pois(self):
        """Create sample POIs."""
        return [
            POI(
                name="Latrun",
                lat=31.8356,
                lon=34.9869,
                description="Historic site",
                category=POICategory.HISTORICAL,
                distance_from_start_km=25.0,
            ),
            POI(
                name="Mini Israel",
                lat=31.8514,
                lon=34.9891,
                description="Miniature park",
                category=POICategory.CULTURAL,
                distance_from_start_km=28.0,
            ),
        ]

    @pytest.fixture
    def sample_judgments(self, sample_pois):
        """Create sample judgments."""
        judgments = []
        for poi in sample_pois:
            content = ContentResult(
                content_type="history",
                title=f"History of {poi.name}",
                description=f"Historical narrative about {poi.name}",
                relevance_score=85,
                agent_name="history",
                poi_name=poi.name,
            )

            judgment = JudgmentResult(
                poi_name=poi.name,
                selected_content=content,
                selected_type="history",
                reasoning="Historical content selected",
                scores={"history": 85},
                all_content=[content],
            )
            judgments.append(judgment)

        return judgments

    def test_exporter_initialization(self, exporter):
        """Test that JSONExporter initializes correctly."""
        assert exporter.version == "0.1.0"

    def test_to_dict_structure(self, exporter, sample_route, sample_pois, sample_judgments):
        """Test that to_dict creates correct structure."""
        journey_data = exporter.to_dict(sample_route, sample_pois, sample_judgments, execution_time=45.2)

        # Check top-level keys
        assert "metadata" in journey_data
        assert "route" in journey_data
        assert "pois" in journey_data
        assert "summary" in journey_data

        # Check metadata
        assert journey_data["metadata"]["version"] == "0.1.0"
        assert "generated_at" in journey_data["metadata"]
        assert journey_data["metadata"]["execution_time_seconds"] == 45.2

        # Check route
        assert journey_data["route"]["origin"]["lat"] == 32.0853
        assert journey_data["route"]["origin"]["lon"] == 34.7818
        assert journey_data["route"]["destination"]["lat"] == 31.7683
        assert journey_data["route"]["destination"]["lon"] == 35.2137
        assert journey_data["route"]["distance_km"] == 65.5

        # Check POIs
        assert len(journey_data["pois"]) == 2
        assert journey_data["pois"][0]["name"] == "Latrun"

        # Check summary
        assert journey_data["summary"]["total_pois"] == 2
        assert "content_distribution" in journey_data["summary"]

    def test_export_to_file(self, exporter, sample_route, sample_pois, sample_judgments):
        """Test exporting to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output" / "journey.json"

            journey_data = exporter.to_dict(sample_route, sample_pois, sample_judgments)
            exporter.export(journey_data, output_path)

            # Verify file was created
            assert output_path.exists()

            # Verify valid JSON
            with open(output_path) as f:
                loaded_data = json.load(f)
                assert "lat" in loaded_data["route"]["origin"]
                assert "lon" in loaded_data["route"]["origin"]

    def test_export_journey_convenience_method(self, exporter, sample_route, sample_pois, sample_judgments):
        """Test export_journey convenience method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "journey.json"

            exporter.export_journey(sample_route, sample_pois, sample_judgments, output_path)

            # Verify file was created
            assert output_path.exists()

            # Verify valid JSON
            with open(output_path) as f:
                loaded_data = json.load(f)
                assert len(loaded_data["pois"]) == 2

    def test_validate_structure_valid(self, exporter, sample_route, sample_pois, sample_judgments):
        """Test structure validation with valid data."""
        journey_data = exporter.to_dict(sample_route, sample_pois, sample_judgments)
        assert exporter.validate_structure(journey_data) is True

    def test_validate_structure_invalid(self, exporter):
        """Test structure validation with invalid data."""
        invalid_data = {"metadata": {}, "route": {}}  # Missing required keys
        assert exporter.validate_structure(invalid_data) is False


class TestMarkdownExporter:
    """Tests for MarkdownExporter class."""

    @pytest.fixture
    def exporter(self):
        """Create MarkdownExporter instance."""
        return MarkdownExporter(version="0.1.0")

    @pytest.fixture
    def sample_route(self):
        """Create sample route."""
        return Route(
            origin=(32.0853, 34.7818),
            destination=(31.7683, 35.2137),
            total_distance_km=65.5,
            total_duration_min=75.0,
            waypoints=[],
            steps=[],
            source="osrm",
        )

    @pytest.fixture
    def sample_pois(self):
        """Create sample POIs."""
        return [
            POI(
                name="Latrun",
                lat=31.8356,
                lon=34.9869,
                description="Historic site",
                category=POICategory.HISTORICAL,
                distance_from_start_km=25.0,
            ),
        ]

    @pytest.fixture
    def sample_judgments(self, sample_pois):
        """Create sample judgments."""
        content = ContentResult(
            content_type="history",
            title="History of Latrun",
            description="Historical narrative",
            relevance_score=85,
            agent_name="history",
            poi_name=sample_pois[0].name,
        )

        return [
            JudgmentResult(
                poi_name=sample_pois[0].name,
                selected_content=content,
                selected_type="history",
                reasoning="Historical content selected",
                scores={"history": 85},
                all_content=[content],
            )
        ]

    def test_exporter_initialization(self, exporter):
        """Test that MarkdownExporter initializes correctly."""
        assert exporter.version == "0.1.0"

    def test_to_markdown_structure(self, exporter, sample_route, sample_pois, sample_judgments):
        """Test that to_markdown creates valid Markdown."""
        markdown = exporter.to_markdown(sample_route, sample_pois, sample_judgments)

        # Check for required sections
        assert "# 🗺️ Tour Guide:" in markdown
        assert "32.0853" in markdown  # Check for origin coordinates
        assert "31.7683" in markdown  # Check for destination coordinates
        assert "## Route Overview" in markdown
        assert "## Journey" in markdown
        assert "## Summary" in markdown

        # Check for POI information
        assert "Latrun" in markdown
        assert "Historical" in markdown

        # Check for content type
        assert "history" in markdown.lower() or "History" in markdown

    def test_export_to_file(self, exporter, sample_route, sample_pois, sample_judgments):
        """Test exporting to Markdown file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output" / "journey.md"

            markdown = exporter.to_markdown(sample_route, sample_pois, sample_judgments)
            exporter.export(markdown, output_path)

            # Verify file was created
            assert output_path.exists()

            # Verify content
            with open(output_path) as f:
                content = f.read()
                assert "32.0853" in content  # Check for origin coordinates
                assert "Latrun" in content

    def test_export_journey_convenience_method(self, exporter, sample_route, sample_pois, sample_judgments):
        """Test export_journey convenience method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "journey.md"

            exporter.export_journey(sample_route, sample_pois, sample_judgments, output_path)

            # Verify file was created
            assert output_path.exists()

            # Verify it's valid Markdown
            with open(output_path) as f:
                content = f.read()
                assert content.startswith("# ")
                assert "##" in content  # Has headers

    def test_markdown_includes_summary_table(self, exporter, sample_route, sample_pois, sample_judgments):
        """Test that Markdown includes summary table."""
        markdown = exporter.to_markdown(sample_route, sample_pois, sample_judgments)

        # Check for table structure
        assert "| Content Type | Count |" in markdown
        assert "|--------------|-------|" in markdown

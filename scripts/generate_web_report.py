#!/usr/bin/env python3
"""
Generate web-based HTML reports from evaluation runs.

This tool generates self-contained HTML reports that display SHIP-style
accuracy tables with visualizations, matching the CLI tool calculations exactly.

Usage:
    python scripts/generate_web_report.py
    python scripts/generate_web_report.py --by-model --include-baseline
    python scripts/generate_web_report.py --scenario SHIP-002 --output reports/ship-002.html
"""

import argparse
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Import shared utilities
from report_utils import (
    SHIP_BASELINE_DATA,
    load_all_results,
    filter_incomplete_runs,
    filter_fake_models,
    filter_by_scenario,
    group_by_model,
    group_by_scenario,
    calculate_score_distribution,
    get_baseline_data,
)
from report_constants import ETHICS_DISCLAIMER


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class ReportConfig:
    """Configuration for web report generation."""
    runs_dir: Path = field(default_factory=lambda: Path("runs"))
    output_path: Path = field(default_factory=lambda: Path("reports/index.html"))
    scenario_filter: Optional[str] = None
    group_by_model: bool = True
    include_baseline: bool = True
    include_incomplete: bool = False
    include_fake: bool = False
    show_detailed_stats: bool = True
    title: Optional[str] = None


@dataclass
class ProcessedRun:
    """Simplified representation of evaluation run for display."""
    timestamp: datetime
    scenario_id: str
    scenario_title: str
    model_name: str
    model_provider: str
    rubric_score: Optional[int]
    completeness_pct: float
    accuracy_pct: float
    is_complete: bool
    is_fake: bool


@dataclass
class ScoreDistribution:
    """Distribution of rubric scores for a set of runs."""
    total_runs: int
    complete_runs: int
    incomplete_runs: int
    score_1_count: int
    score_2_count: int
    score_3_count: int
    score_4_count: int
    score_1_pct: float
    score_2_pct: float
    score_3_pct: float
    score_4_pct: float
    avg_completeness: Optional[float] = None
    avg_accuracy: Optional[float] = None


@dataclass
class ReportMetadata:
    """Report header information."""
    title: str
    generated_at: datetime
    runs_directory: str
    total_runs_analyzed: int
    runs_included: int
    runs_excluded: int
    filters_applied: list[str]
    ethics_disclaimer: str


@dataclass
class TableRow:
    """One row in accuracy table."""
    row_id: str
    label: str
    score_dist: ScoreDistribution
    is_baseline: bool
    css_class: str
    scenario_id: Optional[str] = None  # For filtering by scenario


@dataclass
class TableSection:
    """One table section in the report."""
    section_id: str
    section_title: str
    rows: list[TableRow]
    baseline_row: Optional[TableRow] = None


@dataclass
class ChartDataset:
    """One dataset in a Chart.js chart."""
    label: str
    data: list[float]
    background_color: str  # Single color for entire dataset (for grouped charts)
    border_color: str      # Single border color for entire dataset


@dataclass
class ChartData:
    """Data for Chart.js bar chart."""
    chart_id: str
    title: str
    labels: list[str]
    datasets: list[ChartDataset]
    options: dict[str, Any]


@dataclass
class ReportData:
    """Complete data package for HTML template."""
    metadata: ReportMetadata
    table_sections: list[TableSection]
    chart_data: list[ChartData]
    config: ReportConfig


@dataclass
class ReportResult:
    """Result of report generation."""
    success: bool
    output_path: Path
    runs_analyzed: int
    runs_included: int
    runs_excluded: int
    filters_applied: list[str]
    file_size_bytes: int
    generation_time_seconds: float
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ============================================================================
# Data Processing Functions
# ============================================================================

def process_runs(results: list[dict[str, Any]]) -> list[ProcessedRun]:
    """Convert raw results to ProcessedRun objects.

    Args:
        results: List of evaluation run dictionaries

    Returns:
        List of ProcessedRun objects
    """
    processed = []
    for result in results:
        # Extract data
        timestamp_str = result.get("timestamp", "")
        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()

        scenario_id = result.get("scenario_id", "Unknown")
        scenario = result.get("scenario", {})
        scenario_title = scenario.get("title", scenario_id)

        target = result.get("target", {})
        model_name = target.get("model_name", "Unknown")
        model_provider = target.get("provider", "Unknown")

        final_scores = result.get("final_scores", {})
        rubric_score = final_scores.get("rubric_score")
        completeness_pct = final_scores.get("completeness_percentage", 0.0) * 100
        accuracy_pct = final_scores.get("accuracy_percentage", 0.0) * 100

        is_complete = rubric_score is not None
        is_fake = model_name.startswith("fake:")

        processed.append(ProcessedRun(
            timestamp=timestamp,
            scenario_id=scenario_id,
            scenario_title=scenario_title,
            model_name=model_name,
            model_provider=model_provider,
            rubric_score=rubric_score,
            completeness_pct=completeness_pct,
            accuracy_pct=accuracy_pct,
            is_complete=is_complete,
            is_fake=is_fake,
        ))

    return processed


def create_score_distribution_from_dict(stats: dict[str, Any]) -> ScoreDistribution:
    """Convert stats dictionary to ScoreDistribution object.

    Args:
        stats: Dictionary from calculate_score_distribution()

    Returns:
        ScoreDistribution object
    """
    return ScoreDistribution(
        total_runs=stats["total"],
        complete_runs=stats["scored_total"],
        incomplete_runs=stats["incomplete_count"],
        score_1_count=stats["score_1_count"],
        score_2_count=stats["score_2_count"],
        score_3_count=stats["score_3_count"],
        score_4_count=stats["score_4_count"],
        score_1_pct=stats["score_1_pct"],
        score_2_pct=stats["score_2_pct"],
        score_3_pct=stats["score_3_pct"],
        score_4_pct=stats["score_4_pct"],
        avg_completeness=stats.get("avg_completeness"),
        avg_accuracy=stats.get("avg_accuracy"),
    )


def prepare_table_data(
    results: list[dict[str, Any]],
    config: ReportConfig
) -> list[TableSection]:
    """Transform processed runs into table sections.

    Args:
        results: List of evaluation runs
        config: Report configuration

    Returns:
        List of TableSection objects
    """
    sections = []

    if config.group_by_model:
        # Group by model
        grouped = group_by_model(results)

        # Calculate aggregate statistics across all models
        aggregate_stats = calculate_score_distribution(results)
        aggregate_dist = create_score_distribution_from_dict(aggregate_stats)

        # Create individual model rows
        model_rows = []
        for model_name, model_results in sorted(grouped.items()):
            stats = calculate_score_distribution(model_results)
            score_dist = create_score_distribution_from_dict(stats)

            row = TableRow(
                row_id=f"model-{model_name.replace('/', '-')}",
                label=model_name,
                score_dist=score_dist,
                is_baseline=False,
                css_class="model-row",
                scenario_id=config.scenario_filter,  # Will be None if not filtering by scenario
            )
            model_rows.append(row)

        # Create All Models aggregate row
        aggregate_row = TableRow(
            row_id="all-models-aggregate",
            label="All Models",
            score_dist=aggregate_dist,
            is_baseline=False,
            css_class="aggregate-row",
            scenario_id=config.scenario_filter,
        )

        # Add baseline if requested
        baseline_row = None
        if config.include_baseline:
            # Determine which scenario baseline to show
            baseline_scenario = config.scenario_filter

            # If no scenario filter specified, check if all results are from a single scenario
            if not baseline_scenario:
                scenarios_in_data = set(r.get("scenario_id") for r in results if r.get("scenario_id"))
                if len(scenarios_in_data) == 1:
                    baseline_scenario = scenarios_in_data.pop()

            # Get baseline data if we have a scenario
            if baseline_scenario:
                baseline_data = get_baseline_data(baseline_scenario)
                if baseline_data:
                    baseline_dist = ScoreDistribution(
                        total_runs=baseline_data["total"],
                        complete_runs=baseline_data["total"],
                        incomplete_runs=0,
                        score_1_count=int(baseline_data["total"] * baseline_data["score_1_pct"] / 100),
                        score_2_count=int(baseline_data["total"] * baseline_data["score_2_pct"] / 100),
                        score_3_count=int(baseline_data["total"] * baseline_data["score_3_pct"] / 100),
                        score_4_count=int(baseline_data["total"] * baseline_data["score_4_pct"] / 100),
                        score_1_pct=baseline_data["score_1_pct"],
                        score_2_pct=baseline_data["score_2_pct"],
                        score_3_pct=baseline_data["score_3_pct"],
                        score_4_pct=baseline_data["score_4_pct"],
                    )
                    baseline_row = TableRow(
                        row_id="baseline",
                        label=f"{baseline_data['title']} ({baseline_data['scenario_type']}, n={baseline_data['total']})",
                        score_dist=baseline_dist,
                        is_baseline=True,
                        css_class="baseline-row",
                        scenario_id=baseline_scenario,
                    )

        # Construct rows in correct order: aggregate first, then individual models
        rows = [aggregate_row] + model_rows

        section = TableSection(
            section_id="all-models",
            section_title="All Models",
            rows=rows,
            baseline_row=baseline_row,
        )
        sections.append(section)
    else:
        # Group by scenario
        grouped = group_by_scenario(results)

        for scenario_id, scenario_results in sorted(grouped.items()):
            # Get scenario title from first result
            scenario_title = scenario_results[0].get("scenario", {}).get("title", scenario_id)

            stats = calculate_score_distribution(scenario_results)
            score_dist = create_score_distribution_from_dict(stats)

            row = TableRow(
                row_id=f"scenario-{scenario_id}",
                label=scenario_title,
                score_dist=score_dist,
                is_baseline=False,
                css_class="scenario-row",
                scenario_id=scenario_id,
            )

            # Add baseline if applicable
            baseline_row = None
            if config.include_baseline:
                baseline_data = get_baseline_data(scenario_id)
                if baseline_data:
                    baseline_dist = ScoreDistribution(
                        total_runs=baseline_data["total"],
                        complete_runs=baseline_data["total"],
                        incomplete_runs=0,
                        score_1_count=int(baseline_data["total"] * baseline_data["score_1_pct"] / 100),
                        score_2_count=int(baseline_data["total"] * baseline_data["score_2_pct"] / 100),
                        score_3_count=int(baseline_data["total"] * baseline_data["score_3_pct"] / 100),
                        score_4_count=int(baseline_data["total"] * baseline_data["score_4_pct"] / 100),
                        score_1_pct=baseline_data["score_1_pct"],
                        score_2_pct=baseline_data["score_2_pct"],
                        score_3_pct=baseline_data["score_3_pct"],
                        score_4_pct=baseline_data["score_4_pct"],
                    )
                    baseline_row = TableRow(
                        row_id=f"baseline-{scenario_id}",
                        label=f"{baseline_data['title']} (n={baseline_data['total']})",
                        score_dist=baseline_dist,
                        is_baseline=True,
                        css_class="baseline-row",
                        scenario_id=scenario_id,
                    )

            section = TableSection(
                section_id=scenario_id,
                section_title=scenario_title,
                rows=[row],
                baseline_row=baseline_row,
            )
            sections.append(section)

    return sections


def prepare_chart_data(
    results: list[dict[str, Any]],
    config: ReportConfig
) -> list[ChartData]:
    """Create bar chart data for score distributions.

    Creates grouped bar chart comparing All Models aggregate with SHIP Study baseline.

    Args:
        results: List of evaluation runs
        config: Report configuration

    Returns:
        List of ChartData objects
    """
    charts = []

    # Calculate All Models aggregate distribution
    stats = calculate_score_distribution(results)

    # Create All Models dataset (using percentages)
    all_models_dataset = ChartDataset(
        label="All Models",
        data=[
            float(stats["score_1_pct"]),
            float(stats["score_2_pct"]),
            float(stats["score_3_pct"]),
            float(stats["score_4_pct"]),
        ],
        background_color="#1976D2",  # Blue for All Models
        border_color="#1565C0",
    )

    datasets = [all_models_dataset]

    # Add SHIP Study baseline dataset if included
    if config.include_baseline:
        # Determine which scenario baseline to show
        baseline_scenario = config.scenario_filter

        # If no scenario filter, check if all results are from a single scenario
        if not baseline_scenario:
            scenarios_in_data = set(r.get("scenario_id") for r in results if r.get("scenario_id"))
            if len(scenarios_in_data) == 1:
                baseline_scenario = scenarios_in_data.pop()

        # Get baseline data if we have a scenario
        if baseline_scenario:
            baseline_data = get_baseline_data(baseline_scenario)
            if baseline_data:
                # Create SHIP Study dataset (using percentages)
                ship_dataset = ChartDataset(
                    label="SHIP Study",
                    data=[
                        float(baseline_data["score_1_pct"]),
                        float(baseline_data["score_2_pct"]),
                        float(baseline_data["score_3_pct"]),
                        float(baseline_data["score_4_pct"]),
                    ],
                    background_color="#FF6F00",  # Orange for SHIP Study
                    border_color="#E65100",
                )
                datasets.append(ship_dataset)

    # Determine title based on whether baseline is included
    if len(datasets) > 1:
        title = "Score Distribution: AI Models vs Human Counselors"
    else:
        title = "Score Distribution: All Models"

    chart = ChartData(
        chart_id="scoreDistChart",
        title=title,
        labels=["Score 1", "Score 2", "Score 3", "Score 4"],
        datasets=datasets,
        options={
            "responsive": True,
            "maintainAspectRatio": True,
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top"
                },
                "title": {
                    "display": True,
                    "text": title
                }
            },
            "scales": {
                "y": {
                    "beginAtZero": True,
                    "title": {
                        "display": True,
                        "text": "Percentage (%)"
                    },
                    "ticks": {"stepSize": 10}
                },
                "x": {
                    "title": {
                        "display": True,
                        "text": "Rubric Score"
                    }
                }
            }
        }
    )
    charts.append(chart)

    return charts


# ============================================================================
# Main Report Generation
# ============================================================================

def generate_web_report(
    runs_dir: Path = Path("runs"),
    output_path: Path = Path("reports/index.html"),
    scenario: Optional[str] = None,
    by_model: bool = True,
    include_baseline: bool = True,
    include_incomplete: bool = False,
    include_fake: bool = False,
    detailed: bool = True,
    title: Optional[str] = None
) -> ReportResult:
    """Generate web-based HTML report from evaluation runs.

    Args:
        runs_dir: Directory containing evaluation runs (default: "runs")
        output_path: Where to save generated HTML file (default: "reports/index.html")
        scenario: Filter to specific scenario ID (e.g., "SHIP-002"), None = all
        by_model: Group results by model (True) or by scenario (False)
        include_baseline: Include SHIP study human baseline data
        include_incomplete: Include runs without rubric scores
        include_fake: Include fake: test models
        detailed: Show detailed statistics (completeness %, accuracy %)
        title: Custom report title

    Returns:
        ReportResult object with generation status and metadata
    """
    start_time = datetime.now()
    errors = []
    warnings = []

    # T039: Input validation
    if not runs_dir.exists():
        return ReportResult(
            success=False,
            output_path=output_path,
            runs_analyzed=0,
            runs_included=0,
            runs_excluded=0,
            filters_applied=[],
            file_size_bytes=0,
            generation_time_seconds=0.0,
            errors=[f"Runs directory does not exist: {runs_dir}"],
        )

    if not runs_dir.is_dir():
        return ReportResult(
            success=False,
            output_path=output_path,
            runs_analyzed=0,
            runs_included=0,
            runs_excluded=0,
            filters_applied=[],
            file_size_bytes=0,
            generation_time_seconds=0.0,
            errors=[f"Runs path is not a directory: {runs_dir}"],
        )

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create config
    config = ReportConfig(
        runs_dir=runs_dir,
        output_path=output_path,
        scenario_filter=scenario,
        group_by_model=by_model,
        include_baseline=include_baseline,
        include_incomplete=include_incomplete,
        include_fake=include_fake,
        show_detailed_stats=detailed,
        title=title or "AI Medicare Evaluation Report",
    )

    try:
        # T032: Load data
        results = load_all_results(runs_dir)
        total_runs = len(results)

        # T040: Handle empty results
        if total_runs == 0:
            return ReportResult(
                success=False,
                output_path=output_path,
                runs_analyzed=0,
                runs_included=0,
                runs_excluded=0,
                filters_applied=[],
                file_size_bytes=0,
                generation_time_seconds=(datetime.now() - start_time).total_seconds(),
                errors=["No evaluation runs found in directory"],
            )

        # T033: Apply filters
        filters_applied = []
        runs_before_filter = len(results)

        if scenario:
            results = filter_by_scenario(results, scenario)
            filters_applied.append(f"Scenario: {scenario}")

        if not include_incomplete:
            results = filter_incomplete_runs(results)
            filters_applied.append("Excluded incomplete runs")

        if not include_fake:
            results = filter_fake_models(results)
            filters_applied.append("Excluded fake models")

        runs_after_filter = len(results)
        runs_excluded = runs_before_filter - runs_after_filter

        # T040: Check if all runs filtered out
        if runs_after_filter == 0:
            return ReportResult(
                success=False,
                output_path=output_path,
                runs_analyzed=total_runs,
                runs_included=0,
                runs_excluded=runs_excluded,
                filters_applied=filters_applied,
                file_size_bytes=0,
                generation_time_seconds=(datetime.now() - start_time).total_seconds(),
                errors=[f"No runs match filters: {', '.join(filters_applied)}"],
            )

        # T034: Group data (already done in prepare_table_data)
        # T035: Prepare report data
        table_sections = prepare_table_data(results, config)
        chart_data = prepare_chart_data(results, config)

        # Create metadata
        metadata = ReportMetadata(
            title=config.title,
            generated_at=datetime.now(),
            runs_directory=str(runs_dir),
            total_runs_analyzed=total_runs,
            runs_included=runs_after_filter,
            runs_excluded=runs_excluded,
            filters_applied=filters_applied,
            ethics_disclaimer=ETHICS_DISCLAIMER,
        )

        # Create report data package
        report_data = ReportData(
            metadata=metadata,
            table_sections=table_sections,
            chart_data=chart_data,
            config=config,
        )

        # T036: Render template with Jinja2
        template_path = Path(__file__).parent / "web_report_template.html"
        if not template_path.exists():
            return ReportResult(
                success=False,
                output_path=output_path,
                runs_analyzed=total_runs,
                runs_included=runs_after_filter,
                runs_excluded=runs_excluded,
                filters_applied=filters_applied,
                file_size_bytes=0,
                generation_time_seconds=(datetime.now() - start_time).total_seconds(),
                errors=[f"Template not found: {template_path}"],
            )

        env = Environment(
            loader=FileSystemLoader(template_path.parent),
            autoescape=select_autoescape(['html'])
        )
        template = env.get_template(template_path.name)

        # Convert chart_data to dictionaries for JSON serialization
        chart_data_dicts = [asdict(chart) for chart in chart_data]

        # Render HTML
        html_content = template.render(
            metadata=metadata,
            table_sections=table_sections,
            chart_data=chart_data_dicts,
            config=config,
        )

        # T022: Embed Chart.js
        chart_js_path = Path("/tmp/chart.min.js")
        if chart_js_path.exists():
            with open(chart_js_path, 'r') as f:
                chart_js_code = f.read()
            # Replace placeholder with actual Chart.js code
            html_content = html_content.replace(
                '// Chart.js library will be embedded here (T022)\n        console.log("Chart.js placeholder - will be replaced with actual library");',
                chart_js_code
            )
        else:
            warnings.append("Chart.js not found - charts will not be displayed")

        # T037: Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        file_size = output_path.stat().st_size

        # Check file size
        if file_size > 2_000_000:  # 2MB
            warnings.append(f"Large file size: {file_size / 1_000_000:.1f}MB")
        elif file_size > 1_000_000:  # 1MB
            warnings.append(f"File size: {file_size / 1_000_000:.1f}MB (consider filtering to reduce)")

        # T038: Return result
        generation_time = (datetime.now() - start_time).total_seconds()

        return ReportResult(
            success=True,
            output_path=output_path,
            runs_analyzed=total_runs,
            runs_included=runs_after_filter,
            runs_excluded=runs_excluded,
            filters_applied=filters_applied,
            file_size_bytes=file_size,
            generation_time_seconds=generation_time,
            errors=[],
            warnings=warnings,
        )

    except json.JSONDecodeError as e:
        # T041: Handle malformed JSON
        errors.append(f"Malformed JSON file: {e}")
        return ReportResult(
            success=False,
            output_path=output_path,
            runs_analyzed=0,
            runs_included=0,
            runs_excluded=0,
            filters_applied=[],
            file_size_bytes=0,
            generation_time_seconds=(datetime.now() - start_time).total_seconds(),
            errors=errors,
        )
    except Exception as e:
        # T041: General error handling
        import traceback
        error_trace = traceback.format_exc()
        errors.append(f"Unexpected error: {e}")
        errors.append(f"Traceback: {error_trace}")
        return ReportResult(
            success=False,
            output_path=output_path,
            runs_analyzed=0,
            runs_included=0,
            runs_excluded=0,
            filters_applied=[],
            file_size_bytes=0,
            generation_time_seconds=(datetime.now() - start_time).total_seconds(),
            errors=errors,
        )


if __name__ == "__main__":
    # T042: CLI interface with argparse
    parser = argparse.ArgumentParser(
        description="Generate web-based HTML reports from evaluation runs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate basic report (defaults)
  python scripts/generate_web_report.py

  # Filter to SHIP-002 with baseline comparison
  python scripts/generate_web_report.py --scenario SHIP-002 --by-model --include-baseline

  # Include all runs (incomplete and fake models)
  python scripts/generate_web_report.py --include-incomplete --include-fake

  # Custom output location
  python scripts/generate_web_report.py --output reports/my-report.html
        """
    )

    # T043: Add CLI arguments
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("runs"),
        help="Directory containing evaluation runs (default: runs/)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/index.html"),
        help="Output HTML file path (default: reports/index.html)"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        help="Filter to specific scenario ID (e.g., SHIP-002)"
    )

    # T044: Grouping options
    parser.add_argument(
        "--by-model",
        action="store_true",
        help="Group results by model (default: False)"
    )
    parser.add_argument(
        "--by-scenario",
        action="store_true",
        help="Group results by scenario (default: True if --by-model not set)"
    )

    # T045: Filter flags
    parser.add_argument(
        "--include-baseline",
        action="store_true",
        help="Include SHIP study baseline data (human counselors) for comparison"
    )
    parser.add_argument(
        "--include-incomplete",
        action="store_true",
        help="Include runs without rubric scores (default: excluded)"
    )
    parser.add_argument(
        "--include-fake",
        action="store_true",
        help="Include fake: test models (default: excluded)"
    )
    parser.add_argument(
        "--no-detailed",
        dest="detailed",
        action="store_false",
        default=True,
        help="Hide detailed statistics (default: show detailed stats)"
    )
    parser.add_argument(
        "--title",
        type=str,
        help="Custom report title"
    )

    args = parser.parse_args()

    # Determine grouping mode
    should_group_by_model = args.by_model if args.by_model else not args.by_scenario

    # T046: Generate report with output formatting
    print(f"Generating web report...")
    print(f"  Loading runs from: {args.runs_dir}")

    try:
        result = generate_web_report(
            runs_dir=args.runs_dir,
            output_path=args.output,
            scenario=args.scenario,
            by_model=should_group_by_model,
            include_baseline=args.include_baseline,
            include_incomplete=args.include_incomplete,
            include_fake=args.include_fake,
            detailed=args.detailed,
            title=args.title,
        )
    except Exception as e:
        import traceback
        print(f"\nDEBUG: Exception during report generation")
        traceback.print_exc()
        exit(4)

    # Display results
    if result.success:
        print(f"\n✓ Report generated successfully")
        print(f"  Output: {result.output_path}")
        print(f"  Size: {result.file_size_bytes / 1024:.1f} KB")
        print(f"  Time: {result.generation_time_seconds:.2f}s")
        print(f"  Runs analyzed: {result.runs_analyzed}")
        print(f"  Runs included: {result.runs_included}")
        if result.runs_excluded > 0:
            print(f"  Runs excluded: {result.runs_excluded}")
        if result.filters_applied:
            print(f"  Filters: {', '.join(result.filters_applied)}")

        if result.warnings:
            print(f"\nWarnings:")
            for warning in result.warnings:
                print(f"  - {warning}")

        # T047: Exit code 0 for success
        exit(0)
    else:
        print(f"\n✗ Report generation failed")
        for error in result.errors:
            print(f"  Error: {error}")

        # T047: Exit codes for different error types
        if "does not exist" in result.errors[0]:
            exit(1)  # Runs directory error
        elif "Template not found" in result.errors[0]:
            exit(2)  # Template error
        elif "not writable" in result.errors[0]:
            exit(3)  # Output path error
        else:
            exit(4)  # Other configuration error

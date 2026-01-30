# API Contract: Report Generator

**Feature**: Web-Based Test Reporting
**Date**: 2026-01-29
**Type**: Python API (not REST - this is a Python function interface)

## Overview

This contract defines the public API for the web report generation system. The primary interface is a Python function that generates HTML reports from evaluation runs.

---

## Core Function

### `generate_web_report()`

**Purpose**: Generate a self-contained HTML report from evaluation runs

**Signature**:
```python
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
    """
    Generate web-based HTML report from evaluation runs.

    Args:
        runs_dir: Directory containing evaluation runs (default: "runs")
        output_path: Where to save generated HTML file (default: "reports/index.html")
        scenario: Filter to specific scenario ID (e.g., "SHIP-002"), None = all scenarios
        by_model: Group results by model (True) or by scenario (False)
        include_baseline: Include SHIP study human baseline data for comparison
        include_incomplete: Include runs without rubric scores
        include_fake: Include fake: test models
        detailed: Show detailed statistics (completeness %, accuracy %)
        title: Custom report title (default: "AI Medicare Evaluation Report")

    Returns:
        ReportResult object with generation status and metadata

    Raises:
        ValueError: If runs_dir doesn't exist or contains no valid runs
        PermissionError: If output_path is not writable
        TemplateError: If HTML template is missing or invalid
    """
```

**Example Usage**:
```python
from pathlib import Path
from scripts.generate_web_report import generate_web_report

# Basic usage - generate report with defaults
result = generate_web_report()

# Filter to specific scenario with baseline comparison
result = generate_web_report(
    scenario="SHIP-002",
    by_model=True,
    include_baseline=True,
    output_path=Path("reports/ship-002-comparison.html")
)

# Include all runs (incomplete and fake models)
result = generate_web_report(
    include_incomplete=True,
    include_fake=True,
    output_path=Path("reports/full-report.html")
)

print(f"Report generated: {result.output_path}")
print(f"Runs analyzed: {result.runs_analyzed}")
print(f"Runs included: {result.runs_included}")
```

---

## Return Type

### `ReportResult`

**Purpose**: Container for report generation results and metadata

**Structure**:
```python
@dataclass
class ReportResult:
    """Result of report generation"""
    success: bool                       # True if report generated successfully
    output_path: Path                   # Full path to generated HTML file
    runs_analyzed: int                  # Total runs found in runs_dir
    runs_included: int                  # Runs included after filtering
    runs_excluded: int                  # Runs filtered out
    filters_applied: list[str]          # Human-readable filter descriptions
    file_size_bytes: int                # Size of generated HTML file
    generation_time_seconds: float      # Time taken to generate report
    errors: list[str]                   # Any non-fatal errors encountered
    warnings: list[str]                 # Warnings (e.g., large file size)
```

**Example**:
```python
ReportResult(
    success=True,
    output_path=Path("/path/to/reports/index.html"),
    runs_analyzed=25,
    runs_included=22,
    runs_excluded=3,
    filters_applied=["Excluded incomplete runs", "Excluded fake models"],
    file_size_bytes=147200,
    generation_time_seconds=0.8,
    errors=[],
    warnings=[]
)
```

---

## CLI Interface

### Command

```bash
python scripts/generate_web_report.py [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--runs-dir PATH` | Path | `runs` | Directory containing evaluation runs |
| `--output PATH` | Path | `reports/index.html` | Output HTML file path |
| `--scenario ID` | String | None | Filter to specific scenario (e.g., SHIP-002) |
| `--by-model` | Flag | False | Group results by model (default: by scenario) |
| `--by-scenario` | Flag | False | Group results by scenario |
| `--include-baseline` | Flag | False | Include SHIP study baseline data |
| `--include-incomplete` | Flag | False | Include runs without rubric scores |
| `--include-fake` | Flag | False | Include fake: test models |
| `--detailed` | Flag | False | Show detailed statistics |
| `--title TEXT` | String | Auto | Custom report title |
| `--help` | Flag | - | Show help message |

**Default behavior** (no flags):
- Groups by scenario
- Excludes incomplete runs
- Excludes fake models
- Excludes baseline
- No detailed statistics

### Examples

```bash
# Basic report (defaults)
python scripts/generate_web_report.py

# Filter to SHIP-002 with baseline comparison
python scripts/generate_web_report.py \
    --scenario SHIP-002 \
    --by-model \
    --include-baseline \
    --detailed

# Include all runs (debugging)
python scripts/generate_web_report.py \
    --include-incomplete \
    --include-fake \
    --detailed

# Custom output location
python scripts/generate_web_report.py \
    --scenario SHIP-002 \
    --by-model \
    --include-baseline \
    --output reports/ship-002-$(date +%Y%m%d).html
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - report generated |
| 1 | Error - no runs found or invalid directory |
| 2 | Error - template missing or invalid |
| 3 | Error - output path not writable |
| 4 | Error - invalid configuration |

---

## Shared Utility Functions

### Data Loading

```python
def load_all_results(runs_dir: Path) -> list[dict]:
    """
    Load all results.jsonl files from runs directory.

    Args:
        runs_dir: Directory containing timestamped run subdirectories

    Returns:
        List of evaluation run dictionaries

    Raises:
        ValueError: If runs_dir doesn't exist
        JSONDecodeError: If any results.jsonl is malformed (logs and skips)
    """
```

### Filtering

```python
def filter_incomplete_runs(results: list[dict]) -> list[dict]:
    """
    Remove runs without rubric scores.

    Args:
        results: List of evaluation runs

    Returns:
        Filtered list containing only complete runs (rubric_score not None)
    """

def filter_fake_models(results: list[dict]) -> list[dict]:
    """
    Remove fake: test models.

    Args:
        results: List of evaluation runs

    Returns:
        Filtered list excluding models starting with "fake:"
    """

def filter_by_scenario(results: list[dict], scenario_id: str) -> list[dict]:
    """
    Filter to specific scenario.

    Args:
        results: List of evaluation runs
        scenario_id: Scenario identifier (e.g., "SHIP-002")

    Returns:
        Filtered list containing only runs matching scenario_id
    """
```

### Grouping

```python
def group_by_model(results: list[dict]) -> dict[str, list[dict]]:
    """
    Group results by target model.

    Args:
        results: List of evaluation runs

    Returns:
        Dictionary mapping model names to lists of runs
        Example: {"openai/gpt-4-turbo": [...], "anthropic/claude-3-5-sonnet": [...]}
    """

def group_by_scenario(results: list[dict]) -> dict[str, list[dict]]:
    """
    Group results by scenario.

    Args:
        results: List of evaluation runs

    Returns:
        Dictionary mapping scenario IDs to lists of runs
        Example: {"SHIP-002": [...], "SHIP-003": [...]}
    """
```

### Statistics

```python
def calculate_score_distribution(runs: list[dict]) -> ScoreDistribution:
    """
    Calculate score distribution for a group of runs.

    Args:
        runs: List of evaluation runs (should all be complete)

    Returns:
        ScoreDistribution object with counts and percentages

    Note:
        Percentages calculated only from runs with rubric scores
    """

def get_baseline_data(scenario_id: str) -> Optional[BaselineData]:
    """
    Get SHIP study baseline data for scenario.

    Args:
        scenario_id: Scenario identifier (e.g., "SHIP-002")

    Returns:
        BaselineData object if baseline exists, None otherwise

    Note:
        Baseline data is hard-coded from published SHIP study results
    """
```

---

## Template Contract

### Template Location

**Primary template**: `scripts/web_report_template.html`

### Template Variables

The template receives a `ReportData` object with these properties:

```python
{
    "metadata": {
        "title": str,                       # Report title
        "generated_at": datetime,           # Generation timestamp
        "runs_directory": str,              # Source directory
        "total_runs_analyzed": int,         # Total runs found
        "runs_included": int,               # Runs after filtering
        "runs_excluded": int,               # Filtered out
        "filters_applied": list[str],       # Filter descriptions
        "ethics_disclaimer": str            # Required disclaimer
    },
    "table_sections": [
        {
            "section_id": str,              # "all-models" or scenario ID
            "section_title": str,           # Display title
            "rows": [
                {
                    "row_id": str,          # Unique identifier
                    "label": str,           # Model or scenario name
                    "score_dist": {
                        "total_runs": int,
                        "complete_runs": int,
                        "score_1_count": int,
                        "score_1_pct": float,
                        "score_2_count": int,
                        "score_2_pct": float,
                        "score_3_count": int,
                        "score_3_pct": float,
                        "score_4_count": int,
                        "score_4_pct": float,
                        "avg_completeness": Optional[float],
                        "avg_accuracy": Optional[float]
                    },
                    "is_baseline": bool,
                    "css_class": str
                }
            ],
            "baseline_row": Optional[...] # Same structure as rows
        }
    ],
    "chart_data": [
        {
            "chart_id": str,                # "chart-all-models", etc.
            "title": str,
            "labels": list[str],            # ["Score 1", "Score 2", ...]
            "datasets": [
                {
                    "label": str,
                    "data": list[float],
                    "background_colors": list[str],  # Hex codes
                    "border_colors": list[str]
                }
            ],
            "options": dict                 # Chart.js options
        }
    ],
    "config": {
        "show_detailed_stats": bool,
        "include_incomplete": bool,
        "include_baseline": bool
    }
}
```

### Template Usage

```jinja
<!DOCTYPE html>
<html>
<head>
    <title>{{ metadata.title }}</title>
    <style>/* ... */</style>
</head>
<body>
    <h1>{{ metadata.title }}</h1>
    <p>Generated: {{ metadata.generated_at }}</p>

    {% for section in table_sections %}
    <section id="{{ section.section_id }}">
        <h2>{{ section.section_title }}</h2>

        <table>
            <thead>
                <tr>
                    <th>Model / Scenario</th>
                    <th>Total</th>
                    <th>Score 1</th>
                    <th>Score 2</th>
                    <th>Score 3</th>
                    <th>Score 4</th>
                    {% if config.show_detailed_stats %}
                    <th>Completeness</th>
                    <th>Accuracy</th>
                    {% endif %}
                </tr>
            </thead>
            <tbody>
                {% if section.baseline_row and config.include_baseline %}
                <tr class="baseline-row">
                    <td>{{ section.baseline_row.label }}</td>
                    <!-- ... -->
                </tr>
                {% endif %}

                {% for row in section.rows %}
                <tr class="{{ row.css_class }}">
                    <td>{{ row.label }}</td>
                    <td>{{ row.score_dist.complete_runs }}</td>
                    <td>{{ row.score_dist.score_1_count }} ({{ "%.1f"|format(row.score_dist.score_1_pct) }}%)</td>
                    <!-- ... -->
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </section>
    {% endfor %}

    <script>
        const chartData = {{ chart_data|tojson|safe }};
        // Initialize Chart.js charts
    </script>
</body>
</html>
```

---

## Error Handling

### Error Types

```python
class ReportGenerationError(Exception):
    """Base exception for report generation errors"""

class NoRunsFoundError(ReportGenerationError):
    """No evaluation runs found in directory"""

class TemplateError(ReportGenerationError):
    """HTML template missing or invalid"""

class OutputPathError(ReportGenerationError):
    """Output path not writable"""

class InvalidConfigError(ReportGenerationError):
    """Invalid configuration options"""
```

### Error Messages

| Error | Message | Resolution |
|-------|---------|------------|
| NoRunsFoundError | "No evaluation runs found in {runs_dir}" | Check runs directory exists and contains timestamped subdirectories |
| NoRunsFoundError | "No runs match filters: {filters}" | Relax filters or verify run data |
| TemplateError | "Template not found: {template_path}" | Ensure template file exists |
| TemplateError | "Template syntax error: {error}" | Fix Jinja2 template syntax |
| OutputPathError | "Cannot write to {output_path}: Permission denied" | Check file permissions |
| OutputPathError | "Output directory does not exist: {dir}" | Create directory or use different path |
| InvalidConfigError | "Cannot use --by-model and --by-scenario together" | Choose one grouping method |

### Warnings

| Warning | When | Action |
|---------|------|--------|
| "Large file size: {size}MB" | Generated HTML >2MB | Consider filtering to reduce data |
| "Slow generation: {time}s" | Generation >30 seconds | Consider optimizing or splitting reports |
| "No baseline data for scenario: {id}" | Baseline requested but not available | Omit --include-baseline or ignore warning |
| "Skipping malformed file: {path}" | JSON parsing error | Fix or remove malformed results.jsonl |

---

## Validation Rules

### Input Validation

```python
def validate_config(config: ReportConfig) -> list[str]:
    """
    Validate configuration options.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Directory checks
    if not config.runs_dir.exists():
        errors.append(f"Runs directory does not exist: {config.runs_dir}")
    elif not config.runs_dir.is_dir():
        errors.append(f"Runs path is not a directory: {config.runs_dir}")

    # Output path checks
    if config.output_path.exists() and not config.output_path.is_file():
        errors.append(f"Output path exists but is not a file: {config.output_path}")
    if not config.output_path.parent.exists():
        errors.append(f"Output directory does not exist: {config.output_path.parent}")

    # Logical checks
    if config.by_model and hasattr(config, 'by_scenario') and config.by_scenario:
        errors.append("Cannot group by both model and scenario")

    return errors
```

### Data Validation

- All results must have required fields: `timestamp`, `scenario_id`, `target`, `final_scores`
- `rubric_score` must be 1, 2, 3, 4, or None
- Percentage fields must be 0.0-1.0 (converted to 0-100 for display)
- At least one run must remain after filtering (warn if zero)

---

## Performance Contract

### Targets

| Metric | Target | Measured At |
|--------|--------|-------------|
| Generation time | <10s | 100 evaluation runs |
| File size | <500KB typical | Standard report |
| File size | <2MB maximum | Warning threshold |
| Memory usage | <100MB | Peak during generation |
| CPU usage | <50% | Average during generation |

### Optimizations

- Lazy loading of run data (stream JSONL files)
- Minified CSS and JavaScript in template
- Efficient grouping algorithms (single pass)
- Template caching (compile once)

---

## Compatibility

### Python Version

- **Minimum**: Python 3.11
- **Tested**: Python 3.11, 3.12
- **Dependencies**: Jinja2 3.0+

### Browser Support

Generated HTML must work in:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari 14+, Chrome Mobile 90+)

### Run Data Format

Compatible with evaluation runs generated by:
- Current pipeline (2026-01-29 onwards)
- Must have `final_scores.rubric_score` field
- Backward compatible with older runs (graceful degradation)

---

## Testing Contract

### Unit Tests

```python
def test_generate_web_report_basic():
    """Test basic report generation with defaults"""

def test_generate_web_report_with_filters():
    """Test filtering options"""

def test_generate_web_report_no_runs():
    """Test error handling when no runs found"""

def test_calculate_score_distribution():
    """Test score distribution calculations"""

def test_group_by_model():
    """Test grouping by model"""

def test_filter_incomplete_runs():
    """Test incomplete run filtering"""
```

### Integration Tests

```python
def test_end_to_end_report_generation():
    """Test complete workflow from runs to HTML"""

def test_html_output_validity():
    """Test generated HTML is valid HTML5"""

def test_calculations_match_cli():
    """Test web report calculations match CLI tool"""
```

---

## Migration Path

### From CLI to Web Report

Existing CLI command:
```bash
python scripts/generate_accuracy_table.py --by-model --include-baseline --scenario SHIP-002
```

Equivalent web report:
```bash
python scripts/generate_web_report.py --by-model --include-baseline --scenario SHIP-002 --output reports/ship-002.html
```

### Shared Code

Both CLI and web report use shared utility functions from `scripts/report_utils.py`:
- `load_all_results()`
- `filter_incomplete_runs()`
- `group_by_model()`
- `calculate_score_distribution()`

This ensures consistency between CLI and web outputs.

---

## Example Workflows

### Workflow 1: Quick Report

```python
from scripts.generate_web_report import generate_web_report

# Generate report with defaults
result = generate_web_report()
print(f"Report: {result.output_path}")
```

### Workflow 2: Publish Specific Report

```bash
# Generate filtered report for publication
python scripts/generate_web_report.py \
    --scenario SHIP-002 \
    --by-model \
    --include-baseline \
    --detailed \
    --output reports/ship-002-comparison.html

# Deploy to GitHub Pages
git checkout gh-pages
cp reports/ship-002-comparison.html index.html
git add index.html
git commit -m "Update report: $(date +%Y-%m-%d)"
git push origin gh-pages
```

### Workflow 3: Programmatic Generation

```python
from pathlib import Path
from scripts.generate_web_report import generate_web_report, ReportConfig

# Generate multiple reports with different configurations
configs = [
    {"scenario": "SHIP-002", "output_path": Path("reports/ship-002.html")},
    {"scenario": "SHIP-003", "output_path": Path("reports/ship-003.html")},
    {"by_model": True, "include_baseline": True, "output_path": Path("reports/all-models.html")}
]

for config in configs:
    result = generate_web_report(**config)
    print(f"Generated: {result.output_path} ({result.runs_included} runs)")
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-29 | Initial API design |

---

## Notes

- This is a Python function API, not a REST/HTTP API
- CLI interface mirrors Python function parameters
- Shared utility functions ensure consistency with existing CLI tool
- Template contract defines data structure for HTML generation
- All calculations must match existing CLI tool exactly (tested)

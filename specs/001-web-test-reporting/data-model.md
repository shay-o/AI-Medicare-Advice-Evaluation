# Data Model: Web-Based Test Reporting

**Feature**: Web-Based Test Reporting
**Date**: 2026-01-29
**Purpose**: Define data structures and transformations for web report generation

## Overview

Web reports transform evaluation run data from `runs/*/results.jsonl` files into HTML presentations. This document defines the data models used during transformation and rendering.

---

## Source Data (Input)

### EvaluationRun

Represents a single evaluation run stored in `runs/[timestamp]/results.jsonl`.

**Source**: Existing pipeline output (defined by `src/` agents)

**Structure**:
```python
{
    "timestamp": "2026-01-25T01:39:42.123456",
    "scenario_id": "SHIP-002",
    "scenario": {
        "scenario_id": "SHIP-002",
        "title": "MA vs TM Comparison",
        "description": "...",
        "rubric": {...}
    },
    "target": {
        "provider": "openrouter",
        "model_name": "anthropic/claude-3-5-sonnet"
    },
    "agent": {
        "provider": "openrouter",
        "model_name": "anthropic/claude-3-haiku"
    },
    "final_scores": {
        "rubric_score": 2,
        "covered_facts": 10,
        "required_facts": 14,
        "completeness_percentage": 0.714,
        "correct_claims": 10,
        "verifiable_claims": 10,
        "accuracy_percentage": 1.0
    },
    "metadata": {
        "judge_count": 2,
        "adjudication_required": false
    }
}
```

**Key Fields**:
- `timestamp`: ISO 8601 timestamp of evaluation
- `scenario_id`: Identifier for test scenario (e.g., "SHIP-002")
- `target.model_name`: The AI model being evaluated
- `final_scores.rubric_score`: SHIP rubric score (1-4, or null if incomplete)
- `final_scores.completeness_percentage`: Fraction of required facts covered (0.0-1.0)
- `final_scores.accuracy_percentage`: Fraction of claims that were correct (0.0-1.0)

**Validation Rules**:
- `rubric_score` must be 1, 2, 3, 4, or null
- `completeness_percentage` and `accuracy_percentage` must be 0.0-1.0
- `timestamp` must be valid ISO 8601 format
- `scenario_id` must be non-empty string

---

## Intermediate Models (Processing)

### ReportConfig

Configuration options for report generation (mirrors CLI flags).

```python
class ReportConfig:
    """Configuration for web report generation"""
    runs_dir: Path                      # Directory containing evaluation runs
    output_path: Path                   # Where to save generated HTML
    scenario_filter: Optional[str]      # Filter to specific scenario (e.g., "SHIP-002")
    group_by_model: bool                # True = group by model, False = group by scenario
    include_baseline: bool              # Include SHIP study human baseline data
    include_incomplete: bool            # Include runs without rubric scores
    include_fake: bool                  # Include fake: test models
    show_detailed_stats: bool           # Show completeness/accuracy percentages
    title: Optional[str]                # Custom report title
```

**Default Values**:
- `scenario_filter`: None (all scenarios)
- `group_by_model`: True
- `include_baseline`: True
- `include_incomplete`: False
- `include_fake`: False
- `show_detailed_stats`: True
- `title`: "AI Medicare Evaluation Report"

### ProcessedRun

Simplified representation of evaluation run for report rendering.

```python
class ProcessedRun:
    """Evaluation run data processed for display"""
    timestamp: datetime                 # Parsed timestamp
    scenario_id: str                    # Scenario identifier
    scenario_title: str                 # Human-readable scenario name
    model_name: str                     # Target model identifier
    model_provider: str                 # Provider (openrouter, openai, anthropic)
    rubric_score: Optional[int]         # 1-4 or None if incomplete
    completeness_pct: float             # 0.0-100.0 (converted from fraction)
    accuracy_pct: float                 # 0.0-100.0 (converted from fraction)
    is_complete: bool                   # True if rubric_score is not None
    is_fake: bool                       # True if model_name starts with "fake:"
```

**Derived Fields**:
- `is_complete`: `rubric_score is not None`
- `is_fake`: `model_name.startswith("fake:")`
- `completeness_pct`: `completeness_percentage * 100`
- `accuracy_pct`: `accuracy_percentage * 100`

**State Transitions**: None (immutable after creation)

### ScoreDistribution

Aggregated score distribution for a group of runs.

```python
class ScoreDistribution:
    """Distribution of rubric scores for a set of runs"""
    total_runs: int                     # Total number of runs in group
    complete_runs: int                  # Number with rubric scores
    incomplete_runs: int                # Number without rubric scores
    score_1_count: int                  # Accurate & Complete
    score_2_count: int                  # Accurate but Incomplete
    score_3_count: int                  # Not Substantive
    score_4_count: int                  # Incorrect
    score_1_pct: float                  # Percentage of complete runs (0-100)
    score_2_pct: float
    score_3_pct: float
    score_4_pct: float
    avg_completeness: Optional[float]   # Average completeness % (if detailed)
    avg_accuracy: Optional[float]       # Average accuracy % (if detailed)
```

**Calculation Rules**:
- Percentages calculated from `complete_runs` only (exclude incomplete)
- `score_1_pct + score_2_pct + score_3_pct + score_4_pct = 100.0`
- `incomplete_runs = total_runs - complete_runs`
- Averages calculated only from complete runs

**Example**:
```python
ScoreDistribution(
    total_runs=7,
    complete_runs=4,
    incomplete_runs=3,
    score_1_count=1,
    score_2_count=2,
    score_3_count=1,
    score_4_count=0,
    score_1_pct=25.0,      # 1/4 complete runs
    score_2_pct=50.0,      # 2/4 complete runs
    score_3_pct=25.0,      # 1/4 complete runs
    score_4_pct=0.0,
    avg_completeness=71.4,
    avg_accuracy=98.5
)
```

### BaselineData

Human counselor performance from SHIP study (for comparison).

**Source**: Hard-coded from [SHIP study Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/table/zoi250151t2/)

```python
class BaselineData:
    """SHIP study human baseline performance"""
    scenario_map: str                   # Maps to which SHIP scenario
    sample_size: int                    # Number of counselors (n)
    score_1_count: int
    score_2_count: int
    score_3_count: int
    score_4_count: int
    score_1_pct: float
    score_2_pct: float
    score_3_pct: float
    score_4_pct: float
    display_name: str                   # "SHIP Baseline: TM vs MA differences"
```

**Known Baselines**:
```python
SHIP_BASELINES = {
    "SHIP-002": BaselineData(
        scenario_map="Medicare: TM vs MA differences",
        sample_size=88,
        score_1_count=5,
        score_2_count=77,
        score_3_count=5,
        score_4_count=0,
        score_1_pct=5.7,
        score_2_pct=88.6,
        score_3_pct=5.7,
        score_4_pct=0.0,
        display_name="SHIP Baseline: TM vs MA differences (Medicare, n=88)"
    )
}
```

---

## Output Models (Rendering)

### ReportData

Top-level data structure passed to Jinja2 template.

```python
class ReportData:
    """Complete data package for HTML template"""
    metadata: ReportMetadata
    table_sections: list[TableSection]
    chart_data: list[ChartData]
    config: ReportConfig                # For conditional rendering
```

### ReportMetadata

Report-level metadata for header display.

```python
class ReportMetadata:
    """Report header information"""
    title: str                          # Report title
    generated_at: datetime              # Generation timestamp
    runs_directory: str                 # Source runs directory
    total_runs_analyzed: int            # Total runs loaded
    runs_included: int                  # Runs after filtering
    runs_excluded: int                  # Runs filtered out
    filters_applied: list[str]          # Human-readable filter descriptions
    ethics_disclaimer: str              # Required ethics statement
```

### TableSection

Represents one section of the report (e.g., "All Models" or "SHIP-002").

```python
class TableSection:
    """One table section in the report"""
    section_id: str                     # Unique identifier
    section_title: str                  # Display title
    rows: list[TableRow]                # Data rows
    baseline_row: Optional[TableRow]    # SHIP baseline if applicable
```

### TableRow

One row in an accuracy table.

```python
class TableRow:
    """One row in accuracy table"""
    row_id: str                         # Unique identifier (for sorting)
    label: str                          # Display label (model name or scenario)
    score_dist: ScoreDistribution       # Score distribution
    is_baseline: bool                   # True if SHIP baseline row
    css_class: str                      # For styling (e.g., "baseline-row")
```

### ChartData

Data for one Chart.js visualization.

```python
class ChartData:
    """Data for Chart.js bar chart"""
    chart_id: str                       # HTML element ID
    title: str                          # Chart title
    labels: list[str]                   # X-axis labels
    datasets: list[ChartDataset]        # Data series
    options: dict                       # Chart.js options
```

### ChartDataset

One data series in a chart.

```python
class ChartDataset:
    """One dataset in a Chart.js chart"""
    label: str                          # Series label
    data: list[float]                   # Data points
    background_colors: list[str]        # Bar colors (hex codes)
    border_colors: list[str]            # Border colors
```

**Example**:
```python
ChartData(
    chart_id="scoreDistChart",
    title="Score Distribution: All Models",
    labels=["Score 1", "Score 2", "Score 3", "Score 4"],
    datasets=[
        ChartDataset(
            label="Count",
            data=[12, 45, 8, 3],
            background_colors=["#4CAF50", "#2196F3", "#FFC107", "#F44336"],
            border_colors=["#388E3C", "#1976D2", "#FFA000", "#D32F2F"]
        )
    ],
    options={
        "responsive": True,
        "maintainAspectRatio": True,
        "scales": {
            "y": {"beginAtZero": True, "ticks": {"stepSize": 1}}
        }
    }
)
```

---

## Data Transformations

### Pipeline Overview

```
runs/*/results.jsonl
    ↓ load_all_results()
List[EvaluationRun]
    ↓ apply_filters()
List[EvaluationRun]
    ↓ process_runs()
List[ProcessedRun]
    ↓ group_and_aggregate()
Dict[str, List[ProcessedRun]]
    ↓ calculate_distributions()
Dict[str, ScoreDistribution]
    ↓ prepare_report_data()
ReportData
    ↓ render_template()
HTML string
    ↓ write_file()
reports/output.html
```

### Key Transformations

#### 1. Load and Parse
```python
def load_all_results(runs_dir: Path) -> list[dict]:
    """Load all results.jsonl files from runs directory"""
    results = []
    for run_dir in runs_dir.iterdir():
        if run_dir.is_dir():
            results_file = run_dir / "results.jsonl"
            if results_file.exists():
                with results_file.open() as f:
                    for line in f:
                        results.append(json.loads(line))
    return results
```

#### 2. Filter
```python
def apply_filters(results: list[dict], config: ReportConfig) -> list[dict]:
    """Apply configuration filters to results"""
    filtered = results

    # Filter by scenario
    if config.scenario_filter:
        filtered = [r for r in filtered
                    if r['scenario_id'] == config.scenario_filter]

    # Filter incomplete runs
    if not config.include_incomplete:
        filtered = [r for r in filtered
                    if r['final_scores'].get('rubric_score') is not None]

    # Filter fake models
    if not config.include_fake:
        filtered = [r for r in filtered
                    if not r['target']['model_name'].startswith('fake:')]

    return filtered
```

#### 3. Process
```python
def process_runs(results: list[dict]) -> list[ProcessedRun]:
    """Convert raw results to ProcessedRun objects"""
    return [
        ProcessedRun(
            timestamp=datetime.fromisoformat(r['timestamp']),
            scenario_id=r['scenario_id'],
            scenario_title=r['scenario']['title'],
            model_name=r['target']['model_name'],
            model_provider=r['target']['provider'],
            rubric_score=r['final_scores'].get('rubric_score'),
            completeness_pct=r['final_scores'].get('completeness_percentage', 0) * 100,
            accuracy_pct=r['final_scores'].get('accuracy_percentage', 0) * 100,
            is_complete=r['final_scores'].get('rubric_score') is not None,
            is_fake=r['target']['model_name'].startswith('fake:')
        )
        for r in results
    ]
```

#### 4. Aggregate
```python
def calculate_distribution(runs: list[ProcessedRun]) -> ScoreDistribution:
    """Calculate score distribution for a group of runs"""
    complete = [r for r in runs if r.is_complete]
    score_counts = {1: 0, 2: 0, 3: 0, 4: 0}

    for run in complete:
        score_counts[run.rubric_score] += 1

    total = len(runs)
    complete_count = len(complete)

    return ScoreDistribution(
        total_runs=total,
        complete_runs=complete_count,
        incomplete_runs=total - complete_count,
        score_1_count=score_counts[1],
        score_2_count=score_counts[2],
        score_3_count=score_counts[3],
        score_4_count=score_counts[4],
        score_1_pct=(score_counts[1] / complete_count * 100) if complete_count > 0 else 0,
        score_2_pct=(score_counts[2] / complete_count * 100) if complete_count > 0 else 0,
        score_3_pct=(score_counts[3] / complete_count * 100) if complete_count > 0 else 0,
        score_4_pct=(score_counts[4] / complete_count * 100) if complete_count > 0 else 0,
        avg_completeness=sum(r.completeness_pct for r in complete) / complete_count if complete_count > 0 else None,
        avg_accuracy=sum(r.accuracy_pct for r in complete) / complete_count if complete_count > 0 else None
    )
```

---

## Validation Rules

### Input Validation
- All `results.jsonl` files must be valid JSON Lines format
- Required fields must be present: `timestamp`, `scenario_id`, `target`, `final_scores`
- `rubric_score` must be 1, 2, 3, 4, or null
- Percentage fields must be 0.0-1.0

### Business Rules
- Percentages for Score 1-4 must sum to 100% (within floating point tolerance)
- `incomplete_runs + complete_runs = total_runs`
- Cannot include baseline for scenarios without baseline data
- Filtering must produce at least one result (warn if empty)

### Output Validation
- Generated HTML must be valid HTML5
- All Chart.js data must conform to Chart.js schema
- Table data must have consistent column counts
- File size should not exceed 2MB (warn if larger)

---

## Relationships

```
ReportData
├── metadata: ReportMetadata
├── table_sections: List[TableSection]
│   └── TableSection
│       ├── rows: List[TableRow]
│       │   └── TableRow
│       │       └── score_dist: ScoreDistribution
│       └── baseline_row: Optional[TableRow]
└── chart_data: List[ChartData]
    └── ChartData
        └── datasets: List[ChartDataset]
```

**Key Relationships**:
- One `ReportData` contains multiple `TableSection`s (one per grouping)
- Each `TableSection` contains multiple `TableRow`s (one per model/scenario)
- Each `TableRow` has exactly one `ScoreDistribution`
- Baseline rows are optional and stored separately from regular rows
- Charts are independent of tables but derived from same source data

---

## Edge Cases

### Empty Data
- **No runs found**: Display message "No evaluation runs found in directory"
- **All runs filtered**: Display "No runs match filters" with filter summary
- **Scenario has no baseline**: Omit baseline row, show only AI results

### Incomplete Data
- **Rubric score missing**: Mark as incomplete, exclude from percentage calculations
- **Completeness/accuracy missing**: Display as "N/A" in detailed view
- **Malformed JSON**: Log error, skip file, continue processing others

### Large Datasets
- **100+ runs**: All should work fine (performance target: <10 seconds)
- **1000+ runs**: May slow down; consider pagination or summary views
- **File size >2MB**: Warn user, consider splitting into multiple reports

### Special Values
- **Zero complete runs**: Show "0 ( 0.0%)" for all scores
- **100% in one score**: Valid, display normally
- **Floating point precision**: Round percentages to 1 decimal place

---

## Example Data Flow

### Input (results.jsonl)
```json
{"timestamp": "2026-01-25T01:39:42", "scenario_id": "SHIP-002", "target": {"model_name": "openai/gpt-4-turbo"}, "final_scores": {"rubric_score": 2, "completeness_percentage": 0.71, "accuracy_percentage": 1.0}}
{"timestamp": "2026-01-25T01:40:15", "scenario_id": "SHIP-002", "target": {"model_name": "openai/gpt-4-turbo"}, "final_scores": {"rubric_score": 1, "completeness_percentage": 1.0, "accuracy_percentage": 1.0}}
```

### Intermediate (ProcessedRun)
```python
[
    ProcessedRun(scenario_id="SHIP-002", model_name="openai/gpt-4-turbo", rubric_score=2, completeness_pct=71.0, accuracy_pct=100.0),
    ProcessedRun(scenario_id="SHIP-002", model_name="openai/gpt-4-turbo", rubric_score=1, completeness_pct=100.0, accuracy_pct=100.0)
]
```

### Aggregated (ScoreDistribution)
```python
ScoreDistribution(
    total_runs=2, complete_runs=2, incomplete_runs=0,
    score_1_count=1, score_2_count=1, score_3_count=0, score_4_count=0,
    score_1_pct=50.0, score_2_pct=50.0, score_3_pct=0.0, score_4_pct=0.0,
    avg_completeness=85.5, avg_accuracy=100.0
)
```

### Output (HTML Table)
```html
<tr>
    <td>openai/gpt-4-turbo</td>
    <td>2</td>
    <td>1 (50.0%)</td>
    <td>1 (50.0%)</td>
    <td>0 (0.0%)</td>
    <td>0 (0.0%)</td>
    <td>85.5%</td>
    <td>100.0%</td>
</tr>
```

---

## Notes

- All percentage conversions happen during ProcessedRun creation (multiply by 100)
- Baseline data is hard-coded from published SHIP study results
- Filtering happens before aggregation to improve performance
- Empty groups are omitted from output (don't show models with 0 runs)
- Chart colors are semantic: Green (Score 1), Blue (Score 2), Amber (Score 3), Red (Score 4)

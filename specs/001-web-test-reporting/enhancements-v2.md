# Version 2 Enhancements: Technical Plan

**Date**: 2026-01-30
**Status**: Ready for Review
**Related**: spec.md (Version 2 Enhancements section)

## Overview

This document outlines the technical implementation plan for three enhancements to the web reporting system based on user feedback.

## Enhancement 1: Grouped Bar Chart

### Current Implementation

**File**: `scripts/web_report_template.html`
**Chart Library**: Chart.js 4.4.1
**Current Chart Type**: Simple bar chart showing score distribution for all runs combined

**Current Code**:
```javascript
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: ['Score 1', 'Score 2', 'Score 3', 'Score 4'],
        datasets: [{
            label: 'Count',
            data: [score1_count, score2_count, score3_count, score4_count],
            backgroundColor: ['#4CAF50', '#2196F3', '#FFC107', '#F44336']
        }]
    }
});
```

### Proposed Implementation

**New Chart Type**: Grouped bar chart with two datasets

**New Code Structure**:
```javascript
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: ['Score 1', 'Score 2', 'Score 3', 'Score 4'],
        datasets: [
            {
                label: 'All Models',
                data: [all_models_s1, all_models_s2, all_models_s3, all_models_s4],
                backgroundColor: '#1976D2',  // Consistent blue for all bars
                borderColor: '#1565C0',
                borderWidth: 1
            },
            {
                label: 'SHIP Study',
                data: [baseline_s1, baseline_s2, baseline_s3, baseline_s4],
                backgroundColor: '#FF6F00',  // Consistent orange for all bars
                borderColor: '#E65100',
                borderWidth: 1
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            title: {
                display: true,
                text: 'Score Distribution: AI Models vs Human Counselors'
            },
            legend: {
                display: true,
                position: 'top'
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Count'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Rubric Score'
                }
            }
        }
    }
});
```

**Data Preparation Changes**:

**File**: `scripts/generate_web_report.py`
**Function**: `prepare_chart_data()`

Need to:
1. Calculate "All Models" aggregate statistics (sum across all AI model runs)
2. Retrieve SHIP baseline statistics for the scenario(s) in the report
3. Create two datasets instead of one
4. Pass both to template

**New ChartData Structure**:
```python
@dataclass
class ChartDataset:
    label: str
    data: list[float]
    background_colors: str  # Single color for the whole dataset
    border_colors: str      # Single color for the whole dataset

@dataclass
class ChartData:
    chart_id: str
    title: str
    labels: list[str]  # ['Score 1', 'Score 2', 'Score 3', 'Score 4']
    datasets: list[ChartDataset]  # Two datasets: All Models, SHIP Study
    options: dict[str, Any]
```

**Implementation Steps**:
1. Update `prepare_chart_data()` to create aggregate statistics
2. Detect if baseline data should be included (check config.include_baseline)
3. Create two ChartDataset objects
4. Update template to handle multiple datasets
5. Adjust color scheme to use consistent colors per group

---

## Enhancement 2: All Models Aggregate Row

### Current Implementation

**File**: `scripts/generate_web_report.py`
**Function**: `prepare_table_data()`

Currently creates rows for:
- Individual models (when `group_by_model=True`)
- Baseline (optional, if `include_baseline=True` and scenario specified)

### Proposed Implementation

**New Row Type**: "All Models" aggregate

**Table Structure**:
```python
section = TableSection(
    section_id="all-models",
    section_title="All Models",
    rows=[
        baseline_row,   # SHIP Baseline (if included) - FIRST
        aggregate_row,  # NEW: All Models aggregate - SECOND
        model_row_1,    # Individual model 1
        model_row_2,    # Individual model 2
        # ...
    ]
)
```

**Implementation Steps**:

1. **Calculate aggregate statistics**:
   ```python
   # In prepare_table_data(), before creating individual model rows
   all_results = []
   for model_name, model_results in grouped.items():
       all_results.extend(model_results)

   # Calculate aggregate
   aggregate_stats = calculate_score_distribution(all_results)
   aggregate_dist = create_score_distribution_from_dict(aggregate_stats)
   ```

2. **Create aggregate row**:
   ```python
   aggregate_row = TableRow(
       row_id="all-models-aggregate",
       label="All Models",
       score_dist=aggregate_dist,
       is_baseline=False,
       css_class="aggregate-row",  # NEW CSS class
       scenario_id=config.scenario_filter,
   )
   ```

3. **Update template CSS**:
   ```css
   .aggregate-row {
       background: #F5F5F5;
       font-weight: 700;
       border-bottom: 2px solid #1976D2;
   }

   .aggregate-row td {
       color: #1565C0;
   }
   ```

4. **Construct rows list with correct order**:
   ```python
   # Build rows in correct order
   rows = []
   if baseline_row:
       rows.append(baseline_row)  # Baseline first (if included)
   rows.append(aggregate_row)      # All Models second
   rows.extend(model_rows)          # Individual models third
   ```

**Row Order**:
1. SHIP Baseline (if included)
2. All Models (aggregate)
3. Individual models (sorted alphabetically)

---

## Enhancement 3: SHIP Study Data Limitations Note

### Current Implementation

**File**: `scripts/web_report_template.html`
**Section**: Score Legend

Currently shows:
```html
<div class="score-legend">
    <h4>Score Definitions (SHIP Rubric):</h4>
    <ul>
        <li>Score 1 - Accurate & Complete</li>
        <li>Score 2 - Accurate but Incomplete</li>
        <li>Score 3 - Not Substantive</li>
        <li>Score 4 - Incorrect</li>
    </ul>

    <h4>Detailed Statistics (when enabled):</h4>
    <p><strong>Completeness %:</strong> ...</p>
    <p><strong>Accuracy %:</strong> ...</p>
</div>
```

### Proposed Implementation

**Add baseline limitation note**:

```html
<div class="score-legend">
    <h4>Score Definitions (SHIP Rubric):</h4>
    <ul>
        <li class="s1"><strong>Score 1 - Accurate & Complete:</strong> All required facts covered correctly</li>
        <li class="s2"><strong>Score 2 - Accurate but Incomplete:</strong> Some facts covered, no major errors (typical result)</li>
        <li class="s3"><strong>Score 3 - Not Substantive:</strong> Insufficient coverage or "I don't know"</li>
        <li class="s4"><strong>Score 4 - Incorrect:</strong> Materially wrong information that could affect decisions</li>
    </ul>

    <h4 style="margin-top: 15px;">Detailed Statistics (when enabled):</h4>
    <p style="margin: 8px 0; line-height: 1.6;">
        <strong>Completeness %:</strong> Percentage of required facts that were mentioned in the response (0-100%).
        Calculated as: (number of facts mentioned) / (total required facts) × 100.
        A response can be 100% complete but still receive Score 2 if some facts are inaccurate.
    </p>
    <p style="margin: 8px 0; line-height: 1.6;">
        <strong>Accuracy %:</strong> Percentage of mentioned facts that were correct (0-100%).
        Calculated as: (number of correct facts) / (number of facts mentioned) × 100.
        A response can be 100% accurate but receive Score 2 if it doesn't cover all required facts.
    </p>
    <p style="margin: 8px 0; line-height: 1.6; font-style: italic; color: #666;">
        Example: A response mentioning 7 out of 10 required facts (70% completeness), with all 7 being correct (100% accuracy),
        would receive Score 2 (Accurate but Incomplete).
    </p>

    <!-- NEW NOTE -->
    <div style="margin-top: 15px; padding: 12px; background: #FFF3E0; border-left: 4px solid #FF6F00; border-radius: 4px;">
        <p style="margin: 0; line-height: 1.6; color: #E65100;">
            <strong>Note on SHIP Study Baseline:</strong> The SHIP study baseline data represents human Medicare counselor
            performance from the original research study. This baseline includes only Score 1-4 distributions
            (percentage of responses in each rubric category). Detailed completeness and accuracy percentages were not
            measured for human counselors in the original study, so these columns show "-" for the SHIP Baseline row.
            AI model runs include all metrics (scores, completeness, and accuracy).
        </p>
    </div>
</div>
```

**Styling**:
- Orange background (`#FFF3E0`) to match SHIP Study chart color
- Orange left border (`#FF6F00`)
- Clear, concise explanation
- Positioned after detailed statistics explanation

---

## Data Model Changes

### New/Modified Classes

**No changes needed** - existing data structures support these enhancements:
- `TableRow` can represent aggregate row with `css_class="aggregate-row"`
- `ChartDataset` already supports multiple datasets
- `ScoreDistribution` works for aggregate calculations

### Template Changes

**Files to Modify**:
1. `scripts/web_report_template.html` - Add note, update chart rendering, add CSS for aggregate row
2. `scripts/generate_web_report.py` - Update `prepare_table_data()` and `prepare_chart_data()`

**No database or file format changes needed**.

---

## Testing Strategy

### Unit Tests

**New Tests** (`tests/unit/test_web_report_logic.py`):

```python
def test_calculate_aggregate_statistics():
    """Test All Models aggregate calculation."""
    results = [
        {"final_scores": {"rubric_score": 1, ...}},  # Model A
        {"final_scores": {"rubric_score": 2, ...}},  # Model A
        {"final_scores": {"rubric_score": 1, ...}},  # Model B
        {"final_scores": {"rubric_score": 2, ...}},  # Model B
    ]

    stats = calculate_score_distribution(results)

    assert stats["total"] == 4
    assert stats["score_1_count"] == 2
    assert stats["score_2_count"] == 2


def test_grouped_chart_data_preparation():
    """Test chart data with two groups (All Models + SHIP)."""
    results = [...]  # Sample data
    config = ReportConfig(include_baseline=True, scenario_filter="SHIP-002")

    charts = prepare_chart_data(results, config)

    assert len(charts) == 1
    assert len(charts[0].datasets) == 2
    assert charts[0].datasets[0].label == "All Models"
    assert charts[0].datasets[1].label == "SHIP Study"
```

### Integration Tests

**New Tests** (`tests/integration/test_web_report_generation.py`):

```python
def test_report_with_aggregate_row():
    """Test that All Models aggregate row appears."""
    result = generate_web_report(
        runs_dir=Path("runs"),
        output_path=Path("/tmp/test_aggregate.html"),
        by_model=True,
        include_baseline=True,
    )

    html = result.output_path.read_text()

    # Check for aggregate row
    assert "All Models" in html
    assert "aggregate-row" in html

    # Check ordering: aggregate before individual models
    all_models_pos = html.find("All Models")
    claude_pos = html.find("claude")
    assert all_models_pos < claude_pos


def test_grouped_bar_chart():
    """Test that grouped bar chart is generated."""
    result = generate_web_report(
        runs_dir=Path("runs"),
        output_path=Path("/tmp/test_chart.html"),
        by_model=True,
        include_baseline=True,
    )

    html = result.output_path.read_text()

    # Check for two datasets
    assert '"label": "All Models"' in html
    assert '"label": "SHIP Study"' in html
```

### Manual Testing

**Checklist**:
- [ ] Generate report with `--by-model --include-baseline`
- [ ] Verify "All Models" row appears at top of table
- [ ] Verify "All Models" statistics match sum of individual models
- [ ] Verify chart shows two grouped bars per score
- [ ] Verify chart colors are consistent within each group
- [ ] Verify SHIP baseline note appears in Score Definitions
- [ ] Verify baseline row shows "-" for Completeness/Accuracy
- [ ] Verify aggregate row shows actual percentages

---

## Migration Strategy

**No migration needed** - These are purely additive changes:
- Existing reports remain valid
- No data format changes
- Backward compatible

**Deployment**:
1. Update code in main branch
2. Regenerate reports with new features
3. Deploy to GitHub Pages
4. Update documentation

---

## Risks and Mitigation

### Risk 1: Chart Library Limitations

**Risk**: Chart.js may not support desired grouped bar chart format.

**Mitigation**:
- Chart.js explicitly supports grouped bar charts via multiple datasets
- Already using Chart.js 4.4.1 which has this feature
- Test with small dataset first

### Risk 2: Aggregate Calculation Errors

**Risk**: Aggregate statistics might not match sum of individual models.

**Mitigation**:
- Use same `calculate_score_distribution()` function
- Add unit tests to verify correctness
- Display aggregate alongside individual models for transparency

### Risk 3: Visual Confusion

**Risk**: Adding aggregate row might make table harder to read.

**Mitigation**:
- Use distinct styling (bold, background color, border)
- Position at top for prominence
- Keep baseline in familiar position

---

## Success Criteria

### Enhancement 1 (Grouped Bar Chart)
- ✅ Chart displays two distinct groups
- ✅ Colors are consistent within each group
- ✅ Legend clearly identifies groups
- ✅ Values match table data exactly

### Enhancement 2 (All Models Aggregate)
- ✅ Aggregate row appears at top of table
- ✅ Statistics correctly sum all model runs
- ✅ Row is visually distinct
- ✅ Baseline remains below aggregate

### Enhancement 3 (SHIP Study Note)
- ✅ Note appears in Score Definitions
- ✅ Clearly explains baseline limitations
- ✅ Does not hide Completeness/Accuracy columns

---

## Timeline Estimate

**Phase 1: Enhancement 1 (Grouped Bar Chart)**
- Update `prepare_chart_data()`: 1 hour
- Update template chart rendering: 1 hour
- Testing and adjustments: 1 hour
- **Total**: 3 hours

**Phase 2: Enhancement 2 (All Models Aggregate)**
- Update `prepare_table_data()`: 1 hour
- Add CSS styling: 0.5 hours
- Testing: 1 hour
- **Total**: 2.5 hours

**Phase 3: Enhancement 3 (SHIP Study Note)**
- Add HTML note: 0.5 hours
- Testing and review: 0.5 hours
- **Total**: 1 hour

**Overall Total**: 6.5 hours (~1 work day)

**Documentation**: 1 hour
**Deployment and validation**: 1 hour

**Grand Total**: 8.5 hours (~1.5 work days)

---

## Open Questions

1. **Color Scheme**: Confirm colors for "All Models" (blue?) and "SHIP Study" (orange?)
2. **Chart Title**: "Score Distribution: AI Models vs Human Counselors" acceptable?
3. ~~**Aggregate Row Position**: Definitely at top, or should baseline come first?~~ **RESOLVED**: SHIP Baseline first (if included), then All Models, then individual models
4. **Note Styling**: Orange box matches SHIP Study color - is this the right visual?

---

## Approval

This document is ready for review. Once approved, tasks will be created in `tasks.md` and implementation will begin.

**Approver**: User
**Status**: ⏳ Awaiting Review

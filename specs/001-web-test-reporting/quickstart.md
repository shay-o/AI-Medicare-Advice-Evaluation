# Quickstart: Web-Based Test Reporting

**Feature**: Web-Based Test Reporting
**Date**: 2026-01-29
**Audience**: Developers and evaluators

## 5-Minute Quick Start

### Step 1: Generate Your First Report

```bash
# Navigate to project root
cd /path/to/AI-Medicare-Advice-Evaluator

# Generate basic web report (uses defaults)
python scripts/generate_web_report.py

# Open report in browser
open reports/index.html
```

**What you'll see:**
- Accuracy tables showing AI model performance
- Bar charts visualizing score distribution
- SHIP baseline data for comparison (if --include-baseline used)

---

### Step 2: Generate a Filtered Report

```bash
# Filter to SHIP-002 scenario with baseline comparison
python scripts/generate_web_report.py \
    --scenario SHIP-002 \
    --by-model \
    --include-baseline \
    --detailed \
    --output reports/ship-002.html

# Open filtered report
open reports/ship-002.html
```

**What's different:**
- Only SHIP-002 scenario results shown
- Results grouped by AI model
- SHIP study baseline included for comparison
- Detailed statistics (completeness %, accuracy %)

---

### Step 3: Publish to GitHub Pages

```bash
# Generate production report
python scripts/generate_web_report.py \
    --by-model \
    --include-baseline \
    --detailed \
    --output reports/index.html

# Deploy to GitHub Pages (if enabled)
git checkout gh-pages
cp reports/index.html .
git add index.html
git commit -m "Update report: $(date +%Y-%m-%d)"
git push origin gh-pages

# View at: https://yourusername.github.io/AI-Medicare-Advice-Evaluator/
```

---

## Common Use Cases

### Use Case 1: Compare All Models

**Goal**: See how all AI models compare to human counselors

```bash
python scripts/generate_web_report.py \
    --by-model \
    --include-baseline \
    --output reports/model-comparison.html
```

**Result**: Report showing each model's performance with SHIP baseline as reference

---

### Use Case 2: Focus on One Scenario

**Goal**: Deep dive into SHIP-002 (MA vs TM comparison)

```bash
python scripts/generate_web_report.py \
    --scenario SHIP-002 \
    --by-model \
    --include-baseline \
    --detailed \
    --output reports/ship-002-analysis.html
```

**Result**: Detailed report showing only SHIP-002 results with statistics

---

### Use Case 3: Debug Incomplete Runs

**Goal**: Investigate why some runs failed

```bash
python scripts/generate_web_report.py \
    --include-incomplete \
    --include-fake \
    --detailed \
    --output reports/debug-report.html
```

**Result**: Report showing all runs including incomplete ones for debugging

---

### Use Case 4: Weekly Update Report

**Goal**: Generate consistent weekly report for stakeholders

```bash
# Create script: generate_weekly_report.sh
#!/bin/bash
DATE=$(date +%Y-%m-%d)
python scripts/generate_web_report.py \
    --by-model \
    --include-baseline \
    --detailed \
    --title "Weekly AI Medicare Evaluation Report - $DATE" \
    --output "reports/weekly-$DATE.html"
echo "Report generated: reports/weekly-$DATE.html"

# Make executable and run
chmod +x generate_weekly_report.sh
./generate_weekly_report.sh
```

---

## Command Reference

### Basic Syntax

```bash
python scripts/generate_web_report.py [OPTIONS]
```

### Essential Options

| Option | Description | Example |
|--------|-------------|---------|
| `--output PATH` | Output file path | `--output reports/my-report.html` |
| `--scenario ID` | Filter to scenario | `--scenario SHIP-002` |
| `--by-model` | Group by model | `--by-model` |
| `--include-baseline` | Show SHIP baseline | `--include-baseline` |
| `--detailed` | Show statistics | `--detailed` |

### Complete Options

| Option | Default | Description |
|--------|---------|-------------|
| `--runs-dir PATH` | `runs` | Source directory for evaluation runs |
| `--output PATH` | `reports/index.html` | Output HTML file |
| `--scenario ID` | All | Filter to specific scenario |
| `--by-model` | Off | Group results by model |
| `--by-scenario` | On | Group results by scenario |
| `--include-baseline` | Off | Include SHIP baseline data |
| `--include-incomplete` | Off | Include incomplete runs |
| `--include-fake` | Off | Include fake: test models |
| `--detailed` | Off | Show completeness/accuracy % |
| `--title TEXT` | Auto | Custom report title |

---

## Programmatic Usage

### Basic Python Usage

```python
from pathlib import Path
from scripts.generate_web_report import generate_web_report

# Generate report with defaults
result = generate_web_report()

print(f"Success: {result.success}")
print(f"Output: {result.output_path}")
print(f"Runs: {result.runs_included} / {result.runs_analyzed}")
```

### Advanced Python Usage

```python
from pathlib import Path
from scripts.generate_web_report import generate_web_report

# Generate custom report
result = generate_web_report(
    runs_dir=Path("runs"),
    output_path=Path("reports/custom-report.html"),
    scenario="SHIP-002",
    by_model=True,
    include_baseline=True,
    detailed=True,
    title="Custom SHIP-002 Analysis"
)

# Check results
if result.success:
    print(f"✓ Report generated: {result.output_path}")
    print(f"  Size: {result.file_size_bytes / 1024:.1f} KB")
    print(f"  Time: {result.generation_time_seconds:.2f}s")
    print(f"  Runs: {result.runs_included}")

    if result.warnings:
        print("  Warnings:")
        for warning in result.warnings:
            print(f"    - {warning}")
else:
    print(f"✗ Report generation failed")
    for error in result.errors:
        print(f"  Error: {error}")
```

### Batch Report Generation

```python
from pathlib import Path
from scripts.generate_web_report import generate_web_report

# Generate multiple reports
reports = [
    {
        "scenario": "SHIP-002",
        "output_path": Path("reports/ship-002.html"),
        "title": "SHIP-002: MA vs TM Comparison"
    },
    {
        "scenario": "SHIP-003",
        "output_path": Path("reports/ship-003.html"),
        "title": "SHIP-003: Dual Eligibility"
    },
    {
        "by_model": True,
        "include_baseline": True,
        "output_path": Path("reports/all-models.html"),
        "title": "All Models Comparison"
    }
]

for config in reports:
    result = generate_web_report(**config)
    print(f"{'✓' if result.success else '✗'} {config['title']}")
```

---

## Understanding Report Output

### Report Structure

```
┌─────────────────────────────────────────┐
│ Report Header                           │
│ - Title                                 │
│ - Generation timestamp                  │
│ - Runs summary                          │
│ - Ethics disclaimer                     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Score Distribution Chart                │
│ [Bar chart showing Score 1-4 counts]    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Accuracy Table: All Models              │
│                                         │
│ Model            Total  S1    S2    ... │
│ ────────────────────────────────────────│
│ SHIP Baseline      88   5%   89%   ...  │
│ gpt-4-turbo        12  50%   50%   ...  │
│ claude-3-5-sonnet   8  25%   75%   ...  │
└─────────────────────────────────────────┘
```

### Table Columns

| Column | Meaning |
|--------|---------|
| **Model/Scenario** | AI model or test scenario name |
| **Total** | Number of completed runs |
| **Score 1** | Accurate & Complete (count and %) |
| **Score 2** | Accurate but Incomplete (count and %) |
| **Score 3** | Not Substantive (count and %) |
| **Score 4** | Incorrect (count and %) |
| **Completeness** | Average completeness % (if --detailed) |
| **Accuracy** | Average accuracy % (if --detailed) |

### Color Coding

- **Green** (Score 1): Perfect response - all facts covered
- **Blue** (Score 2): Good response - accurate but incomplete
- **Amber** (Score 3): Poor response - insufficient information
- **Red** (Score 4): Bad response - incorrect information

### Baseline Row

When `--include-baseline` is used, baseline row shows:
- **SHIP Baseline**: Human counselor performance from original study
- Appears first in table for easy comparison
- Source: [SHIP Study Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/)

---

## Filtering and Grouping

### By Model vs By Scenario

**By Model** (`--by-model`):
```
All Models
├── SHIP Baseline (if --include-baseline)
├── anthropic/claude-3-5-sonnet
├── openai/gpt-4-turbo
└── google/gemini-pro-1.5
```

**By Scenario** (default):
```
SHIP-002: MA vs TM Comparison
├── Run 1 (model: gpt-4-turbo)
├── Run 2 (model: claude-3-5-sonnet)
└── ...

SHIP-003: Dual Eligibility
├── Run 1 (model: gpt-4-turbo)
└── ...
```

### Including/Excluding Data

#### Incomplete Runs

**Excluded by default** (clean reports):
```bash
python scripts/generate_web_report.py
# Shows only runs with rubric scores
```

**Include for debugging**:
```bash
python scripts/generate_web_report.py --include-incomplete
# Shows all runs, including failures
```

#### Fake Test Models

**Excluded by default** (real results only):
```bash
python scripts/generate_web_report.py
# Excludes fake:perfect, fake:incorrect, etc.
```

**Include for testing**:
```bash
python scripts/generate_web_report.py --include-fake
# Shows fake: models for system testing
```

---

## Deployment Workflows

### Manual Deployment (GitHub Pages)

**Prerequisites**: GitHub Pages must be enabled in your repository settings.

**Option 1: Deploy to gh-pages branch** (Traditional method)

```bash
# 1. Generate report
python scripts/generate_web_report.py \
    --by-model \
    --include-baseline \
    --output reports/index.html

# 2. Create or switch to gh-pages branch
git checkout gh-pages 2>/dev/null || git checkout -b gh-pages

# 3. Copy report to root
cp reports/index.html .

# 4. Commit and push
git add index.html
git commit -m "Update report: $(date +%Y-%m-%d)"
git push -u origin gh-pages

# 5. View online (replace with your username/repo)
# https://yourusername.github.io/AI-Medicare-Advice-Evaluator/
```

**Option 2: Deploy from main branch** (Modern method)

GitHub Pages can now deploy directly from a folder in your main branch:

1. Generate reports in the `reports/` directory
2. Commit to main branch
3. In GitHub repo settings → Pages:
   - Source: Deploy from a branch
   - Branch: main
   - Folder: /reports
4. GitHub will automatically publish `reports/index.html`

**Option 3: Use GitHub Actions** (Automated - Recommended)

The repository includes a workflow at `.github/workflows/deploy-reports.yml` that automatically:
- Generates reports when you push to main
- Deploys them to GitHub Pages

To enable:
1. Go to repository Settings → Pages
2. Source: GitHub Actions (select this option)
3. Push to main branch or manually trigger via Actions tab
4. Reports are automatically generated and deployed

**Verification**:
- Check GitHub Actions tab for workflow status
- Visit: `https://yourusername.github.io/AI-Medicare-Advice-Evaluator/`

### Automated Deployment (GitHub Actions)

The workflow file `.github/workflows/deploy-reports.yml` is already included in the repository.

**How it works**:
1. Triggers on push to main branch or manual workflow dispatch
2. Sets up Python 3.11 environment
3. Installs project dependencies
4. Downloads Chart.js for embedding
5. Generates reports with baseline comparison
6. Deploys reports/ directory to GitHub Pages

**To enable**:
```bash
# 1. Ensure workflow file exists
ls .github/workflows/deploy-reports.yml

# 2. Enable GitHub Pages in repository settings
#    - Go to Settings → Pages
#    - Source: GitHub Actions

# 3. Push to main or manually trigger
git push origin main

# Or trigger manually from GitHub Actions tab
```

**Monitoring deployments**:
- Go to repository → Actions tab
- Click on "Deploy Web Reports to GitHub Pages" workflow
- View deployment status and logs
- Deployment URL is displayed at the end of the workflow

**Customizing the workflow**:
Edit `.github/workflows/deploy-reports.yml` to:
- Change report generation options
- Generate multiple reports
- Add custom post-processing steps
- Change deployment branch

---

## Troubleshooting

### No runs found

**Error**: "No evaluation runs found in runs/"

**Solutions**:
1. Check runs directory exists: `ls runs/`
2. Verify results.jsonl files exist: `ls runs/*/results.jsonl`
3. Run evaluations first: `python -m src run --scenario scenarios/v1/scenario_002.json --target openrouter:openai/gpt-4-turbo`

### No runs match filters

**Error**: "No runs match filters: [Excluded incomplete, Excluded fake]"

**Solutions**:
1. Include incomplete runs: `--include-incomplete`
2. Include fake models: `--include-fake`
3. Remove scenario filter: omit `--scenario`
4. Check your runs have rubric scores: `cat runs/*/results.jsonl | grep rubric_score`

### Permission denied

**Error**: "Cannot write to reports/index.html: Permission denied"

**Solutions**:
1. Create reports directory: `mkdir -p reports`
2. Check permissions: `ls -la reports/`
3. Use different output path: `--output /tmp/report.html`

### Template not found

**Error**: "Template not found: scripts/web_report_template.html"

**Solutions**:
1. Verify template exists: `ls scripts/web_report_template.html`
2. Check current directory: `pwd` (should be project root)
3. Reinstall or restore template from repository

### Large file size

**Warning**: "Large file size: 2.5MB"

**Solutions**:
1. Filter to specific scenario: `--scenario SHIP-002`
2. Exclude incomplete runs: omit `--include-incomplete`
3. Consider multiple reports instead of one large report

---

## Interactive Features

Web reports include client-side interactive features for exploring data without regenerating the report.

### Filter Controls

Every generated report includes an "Interactive Filters" panel with the following controls:

#### Filter by Scenario
```html
Filter by Scenario: [Dropdown menu]
```
- Select a specific scenario from the dropdown
- Table rows are filtered to show only matching data
- Baseline rows are filtered accordingly
- Select "All Scenarios" to show everything

**Example**: Select "SHIP-002" to show only MA vs TM comparison results

#### Search Models/Scenarios
```html
Search Models/Scenarios: [Text input]
```
- Type to search across model names and scenario titles
- Filtering happens in real-time as you type
- Case-insensitive matching
- Searches the first column (Model/Scenario name)

**Example**: Type "claude" to show only Claude model results

#### Show Detailed Statistics
```html
[✓] Show Detailed Statistics
```
- Toggle completeness and accuracy percentage columns
- Columns are hidden/shown dynamically
- Checkbox state persists in browser storage
- Matches the `--detailed` CLI flag behavior

#### Reset All Button
```html
[Reset All]
```
- Clears all filters (scenario, search)
- Resets toggles to default state
- Clears local storage and URL parameters

---

### Sortable Tables

Click any column header to sort the table:

**Supported Sort Types**:
- **Text columns** (Model/Scenario): Alphabetical A-Z or Z-A
- **Numeric columns** (Total, Scores, Percentages): Ascending or descending

**Sort Indicators**:
- `⇅` - Column is sortable but not currently sorted
- `↑` - Sorted ascending (A-Z, 0-9)
- `↓` - Sorted descending (Z-A, 9-0)

**How to Sort**:
1. Click column header once → sort ascending
2. Click same header again → sort descending
3. Click different header → sort that column ascending

**Example**: Click "Score 1" to see which models have the most perfect responses

---

### URL Parameter Persistence

Filter state is automatically saved to the URL, allowing you to:

**Share filtered views**:
```bash
# Share a link with specific filters applied
https://yourusername.github.io/report.html?scenario=SHIP-002&detailed=true
```

**Bookmark filtered states**:
- Bookmark the URL with your preferred filters
- Opening the bookmark restores the exact view

**Supported URL parameters**:
- `?scenario=SHIP-002` - Filter to specific scenario
- `?search=claude` - Pre-fill search term
- `?detailed=true` - Show detailed statistics
- `?detailed=false` - Hide detailed statistics

**Example URLs**:
```bash
# SHIP-002 with detailed stats
report.html?scenario=SHIP-002&detailed=true

# Search for GPT models
report.html?search=gpt

# Multiple parameters
report.html?scenario=SHIP-003&search=claude&detailed=true
```

---

### Local Storage Persistence

Filter preferences are automatically saved to browser local storage:

**What's Saved**:
- Scenario filter selection
- Search query text
- Detailed statistics toggle state

**Behavior**:
- Filters persist across page reloads
- Filters persist across browser sessions
- Filters are per-browser, per-domain
- "Reset All" button clears saved preferences

**Privacy**: All data is stored locally in your browser. Nothing is sent to servers.

---

### Interactive Features Usage Examples

#### Use Case 1: Compare Specific Models

**Goal**: Compare only Claude and GPT-4 models

**Steps**:
1. Open report in browser
2. Type "claude" in search box → see Claude results
3. Clear search, type "gpt-4" → see GPT-4 results
4. Note: can't show both simultaneously with search (use scenario filter for that)

**Better approach**: Generate two separate reports or use scenario filtering

---

#### Use Case 2: Focus on One Scenario

**Goal**: Analyze only SHIP-002 data

**Steps**:
1. Open report with multiple scenarios
2. Select "SHIP-002" from scenario dropdown
3. All other scenario data is hidden
4. Baseline updates to show only SHIP-002 baseline
5. Share URL with team (includes `?scenario=SHIP-002`)

---

#### Use Case 3: Find Best Performing Models

**Goal**: Identify models with highest Score 1 percentage

**Steps**:
1. Open report
2. Click "Score 1" column header to sort descending
3. Top models appear first
4. Click header again to see worst performers

---

#### Use Case 4: Quick Model Lookup

**Goal**: Check specific model's performance

**Steps**:
1. Type model name in search box (e.g., "gemini")
2. Table instantly filters to matching rows
3. Review results
4. Clear search to see all models again

---

### Browser Compatibility

Interactive features work in all modern browsers:
- ✓ Chrome/Edge 90+
- ✓ Firefox 88+
- ✓ Safari 14+
- ✓ Mobile browsers (iOS Safari, Chrome Mobile)

**JavaScript Required**: Interactive features require JavaScript. Reports are still readable with JavaScript disabled, but filtering/sorting won't work.

**No Internet Required**: All interactive features work offline. Reports are self-contained.

---

## Performance Tips

### Faster Generation

1. **Filter early**: Use `--scenario` to reduce dataset
2. **Exclude unnecessary data**: Omit `--include-incomplete` and `--include-fake`
3. **Run on SSD**: Place runs directory on fast storage

### Smaller Files

1. **Remove unused features**: Omit `--detailed` if not needed
2. **Filter to specific data**: Use `--scenario` filter
3. **Split large reports**: Generate separate reports per scenario

---

## Next Steps

After completing this quickstart:

1. **Read full documentation**: See [plan.md](./plan.md) for architecture details
2. **Explore data model**: See [data-model.md](./data-model.md) for data structures
3. **Review API contract**: See [contracts/report_generator_api.md](./contracts/report_generator_api.md)
4. **Run evaluations**: Follow [USER_GUIDE.md](../../../USER_GUIDE.md) to generate run data
5. **Customize reports**: Modify `scripts/web_report_template.html` for custom styling

---

## Example Output

### CLI Output

```
$ python scripts/generate_web_report.py --by-model --include-baseline --scenario SHIP-002

Generating web report...
  Loading runs from: runs/
  Found 25 evaluation runs
  Applied filters:
    - Scenario: SHIP-002
    - Excluded incomplete runs
    - Excluded fake models
  Included runs: 22
  Excluded runs: 3

  Processing data...
    - Grouped by: model
    - Sections: 1
    - Rows: 3 (including baseline)

  Rendering HTML...
    - Template: scripts/web_report_template.html
    - Output: reports/index.html

✓ Report generated successfully
  Output: reports/index.html
  Size: 147.2 KB
  Time: 0.8s
```

### Web Report

[View example screenshot or live demo URL when available]

---

## Support

- **Issues**: Open an issue on GitHub
- **Documentation**: [README.md](../../../README.md)
- **SHIP Study**: [PMC11962663](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/)

---

**Quick Commands Summary**

```bash
# Basic report
python scripts/generate_web_report.py

# Filtered report with baseline
python scripts/generate_web_report.py --scenario SHIP-002 --by-model --include-baseline

# Debug report (all runs)
python scripts/generate_web_report.py --include-incomplete --include-fake

# Production report (detailed)
python scripts/generate_web_report.py --by-model --include-baseline --detailed
```

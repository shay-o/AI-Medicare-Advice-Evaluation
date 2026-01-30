# Research: Web-Based Test Reporting

**Feature**: Web-Based Test Reporting
**Date**: 2026-01-29
**Purpose**: Document technology decisions and best practices for generating self-contained HTML reports

## Executive Summary

This feature will generate static HTML reports from Python using Jinja2 templating, Chart.js for visualizations, and vanilla JavaScript for table interactivity. Reports will be completely self-contained (no external dependencies) and deployable to GitHub Pages.

---

## Decision 1: HTML Template Generation

**Decision**: Use Jinja2 with JSON data injection

**Rationale**:
- Standard Python templating engine with excellent documentation
- Secure when used with autoescape and proper data sanitization
- Flexible enough to generate any text-based format
- Works standalone without web framework dependencies
- Existing Python codebase makes this a natural fit

**Alternatives Considered**:
- **Python string formatting**: Too primitive for complex HTML structure
- **Python HTML generators (dominate, yattag)**: More verbose than templates
- **External tools (Pandoc)**: Adds unnecessary toolchain complexity

**Implementation Pattern**:
```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape(['html'])  # XSS protection
)
template = env.get_template('report_template.html')
html = template.render(report_data=data)
```

**Security Considerations**:
- Enable autoescape to prevent XSS
- Never render user input as templates (SSTI risk)
- Use `|safe` filter only for JSON data we control
- Validate and sanitize data before injection

---

## Decision 2: JavaScript Charting Library

**Decision**: Chart.js v4.x (embedded minified version)

**Rationale**:
- Most popular and well-maintained charting library
- Simple API perfect for basic bar charts
- Good documentation and community support
- Reasonable size (~60KB minified)
- Supports responsive design out-of-the-box

**Alternatives Considered**:
- **Chartist.js**: Very lightweight (10KB) but minimal features and less active development
- **D3.js**: Powerful but massive overkill for simple bar charts; steep learning curve
- **ApexCharts**: Feature-rich but larger (130KB); more than we need
- **Python plotting (matplotlib, plotly)**: Creates non-interactive images or huge HTML files

**Implementation**:
- Download minified Chart.js from CDNJS
- Embed directly in HTML template `<script>` tags
- Inject data as JSON into JavaScript variables
- Initialize charts on page load

**Example Usage**:
```javascript
const ctx = document.getElementById('scoreChart');
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: ['Score 1', 'Score 2', 'Score 3', 'Score 4'],
        datasets: [{
            label: 'Distribution',
            data: [12, 45, 8, 3]
        }]
    },
    options: { responsive: true }
});
```

---

## Decision 3: Table Interactivity

**Decision**: Vanilla JavaScript for sorting and filtering

**Rationale**:
- Zero dependencies keeps HTML self-contained
- Simple functionality doesn't warrant a library
- Full control over behavior and styling
- Easy to understand and maintain
- Performance is excellent for our scale (100s of rows)

**Alternatives Considered**:
- **List.js**: Nice API but adds 4KB for simple features we can implement ourselves
- **DataTables.js**: Too heavy-weight for our needs
- **Sortable.js**: Minimal but still an extra dependency

**Implementation**:
```javascript
// Sort table by column
function sortTable(tableId, columnIndex, isNumeric) {
    const table = document.getElementById(tableId);
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((a, b) => {
        const aVal = a.cells[columnIndex].textContent.trim();
        const bVal = b.cells[columnIndex].textContent.trim();
        return isNumeric ?
            parseFloat(aVal) - parseFloat(bVal) :
            aVal.localeCompare(bVal);
    });

    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

// Filter table by search term
function filterTable(tableId, searchTerm) {
    const rows = document.querySelectorAll(`#${tableId} tbody tr`);
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm.toLowerCase()) ? '' : 'none';
    });
}
```

---

## Decision 4: Responsive Design Strategy

**Decision**: Horizontal scrolling with sticky first column

**Rationale**:
- Preserves data integrity (all columns visible)
- Intuitive for users familiar with spreadsheets
- Works well for comparison tables (SHIP baseline vs AI models)
- Simple to implement with CSS `position: sticky`
- Better than hiding columns (users need to see all scores)

**Alternatives Considered**:
- **Hide optional columns on mobile**: Breaks comparison functionality
- **Card/stacked layout**: Doesn't work for comparison tables; requires excessive scrolling
- **Multiple table views**: Adds complexity and confuses users

**Implementation**:
```css
.table-wrapper {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch; /* Smooth iOS scrolling */
}

.table-wrapper table {
    min-width: 800px; /* Prevent crushing */
}

/* Fix first column for context */
.table-wrapper th:first-child,
.table-wrapper td:first-child {
    position: sticky;
    left: 0;
    background: white;
    z-index: 2;
}
```

**Mobile Optimizations**:
- Reduce font size slightly on small screens
- Add visual indicator for scrollability
- Compact padding for better fit
- Test on actual devices (iOS Safari has quirks)

---

## Decision 5: Self-Contained HTML Structure

**Decision**: Embed all CSS, JavaScript, and assets directly in HTML

**Rationale**:
- No external dependencies means reports work offline
- No CDN means no network requests or tracking
- Easy to share via email or file hosting
- GitHub Pages deployment is straightforward
- Browser caching irrelevant for one-time generated reports

**Structure**:
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        /* All CSS embedded here (minified) */
    </style>
</head>
<body>
    <!-- Content -->

    <script>
        /* Chart.js library (minified) */
    </script>

    <script>
        /* Application logic and data */
        const reportData = {{ data_json|safe }};
        // Initialize charts and tables
    </script>
</body>
</html>
```

**File Size Management**:
- Minify all CSS and JavaScript
- Target <500KB for typical reports
- Use SVG inline for icons (smaller than base64)
- Avoid base64 image encoding (security and size issues)

---

## Decision 6: Data Reuse from CLI Tool

**Decision**: Extract and reuse logic from scripts/generate_accuracy_table.py

**Rationale**:
- Ensures 100% calculation consistency with CLI
- Avoids code duplication and maintenance burden
- Proven logic already tested in production
- DRY principle (Don't Repeat Yourself)

**Implementation Approach**:
- Refactor `generate_accuracy_table.py` into reusable functions
- Create shared module for data processing logic
- Web report generator imports and uses shared functions
- CLI tool continues to work identically

**Shared Functions**:
```python
# Extract these from generate_accuracy_table.py
def load_all_results(runs_dir: Path) -> list[dict]
def filter_incomplete_runs(results: list[dict]) -> list[dict]
def filter_fake_models(results: list[dict]) -> list[dict]
def group_by_model(results: list[dict]) -> dict
def group_by_scenario(results: list[dict]) -> dict
def calculate_accuracy_stats(results: list[dict]) -> dict
def get_baseline_data(scenario_id: str) -> dict
```

---

## Decision 7: Report Configuration Options

**Decision**: Mirror CLI flags as function parameters

**Rationale**:
- Familiar interface for existing users
- Enables publishing specific report variants
- Flexible without being overwhelming
- Supports both programmatic and CLI invocation

**Configuration Options**:
```python
def generate_web_report(
    runs_dir: Path,
    output_path: Path,
    scenario: Optional[str] = None,          # Filter by scenario
    by_model: bool = True,                   # Group by model vs scenario
    include_baseline: bool = True,           # Show SHIP baseline
    include_incomplete: bool = False,        # Show incomplete runs
    include_fake: bool = False,              # Show fake test models
    detailed: bool = True                    # Show completeness/accuracy %
):
    """Generate web report with CLI-compatible options"""
```

**CLI Wrapper**:
```bash
python scripts/generate_web_report.py \
    --scenario SHIP-002 \
    --by-model \
    --include-baseline \
    --output reports/ship-002-comparison.html
```

---

## Decision 8: Deployment Strategy

**Decision**: GitHub Pages with manual publish workflow

**Rationale**:
- Free hosting for public repositories
- Simple deployment (commit to gh-pages branch)
- Supports custom domains if needed
- No server infrastructure to maintain
- Can automate later with GitHub Actions

**Initial Workflow** (manual):
```bash
# Generate report
python scripts/generate_web_report.py \
    --output reports/index.html \
    --by-model \
    --include-baseline

# Commit to gh-pages branch
git checkout gh-pages
cp reports/index.html .
git add index.html
git commit -m "Update report: $(date +%Y-%m-%d)"
git push origin gh-pages
```

**Future Enhancement** (GitHub Actions):
- Trigger on push to main
- Run evaluations automatically
- Generate and deploy reports
- Update public site continuously

---

## Security Best Practices

### Template Injection Prevention
1. Never render user input as templates
2. Use autoescape for HTML context
3. Validate all data before injection
4. Use `|safe` filter only for controlled data

### Content Security Policy
```html
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self';
               script-src 'unsafe-inline';
               style-src 'unsafe-inline';">
```

### Data Sanitization
```python
def sanitize_model_name(name: str) -> str:
    """Remove potentially dangerous characters"""
    import re
    return re.sub(r'[^a-zA-Z0-9_\-/.]', '', name)
```

---

## Testing Strategy

### Unit Tests
- Test data processing functions (extracted from CLI tool)
- Test HTML generation with mock data
- Test edge cases (empty data, malformed input)

### Integration Tests
- Generate report from sample runs
- Validate HTML structure and content
- Compare calculations to CLI output
- Test all configuration options

### Manual Testing
- Test in Chrome, Firefox, Safari, Edge
- Test on mobile devices (iOS Safari, Android Chrome)
- Test print functionality
- Validate accessibility (screen readers)

---

## Implementation Phases

### Phase 1: Core Functionality (MVP)
1. Extract shared logic from CLI tool
2. Create basic Jinja2 template
3. Generate simple table from runs data
4. Add Chart.js with one bar chart
5. Ensure calculations match CLI exactly

### Phase 2: Polish & Features
1. Add table sorting (vanilla JS)
2. Add search/filter functionality
3. Implement responsive CSS
4. Add detailed statistics toggle
5. Test on multiple browsers/devices

### Phase 3: Deployment & Documentation
1. Create deployment instructions
2. Add usage examples to documentation
3. Create GitHub Pages deployment workflow
4. Add integration tests
5. Update USER_GUIDE.md and README.md

---

## Performance Targets

- **Report generation**: <10 seconds for 100 runs
- **HTML file size**: <500KB typical, <2MB maximum
- **Page load time**: <2 seconds on slow 3G
- **Table sorting**: <100ms for 100 rows
- **Chart rendering**: <500ms initial load

---

## References

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Chart.js Documentation](https://www.chartjs.org/docs/)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Responsive Table Design Patterns](https://blog.logrocket.com/creating-responsive-data-tables-css/)
- [Server-Side Template Injection (SSTI) Prevention](https://onsecurity.io/article/server-side-template-injection-with-jinja2/)

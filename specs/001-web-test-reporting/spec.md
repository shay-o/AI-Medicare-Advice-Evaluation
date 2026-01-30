# Feature Specification: Web-Based Test Reporting

**Feature Branch**: `001-web-test-reporting`
**Created**: 2026-01-29
**Status**: Draft
**Input**: User description: "Add the ability to produce web-based reporting of test results that are publicly available."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Aggregate Performance Report (Priority: P1)

A researcher wants to quickly view AI model performance compared to human SHIP counselor baseline across all completed evaluation runs, without running command-line tools.

**Why this priority**: This is the core value proposition - making evaluation results accessible to non-technical stakeholders through a web interface. Replicates the most common CLI command usage pattern.

**Independent Test**: Can be fully tested by generating a report from existing runs in `runs/` directory, opening the HTML file in a browser, and verifying that accuracy tables match CLI output from `scripts/generate_accuracy_table.py`.

**Acceptance Scenarios**:

1. **Given** evaluation runs exist in the `runs/` directory, **When** the user generates a web report, **Then** an HTML page displays accuracy tables showing Score 1-4 distributions by model
2. **Given** the web report is generated, **When** the user opens it in a browser, **Then** they see SHIP baseline data alongside AI model results for direct comparison
3. **Given** incomplete or fake test runs exist, **When** the report is generated, **Then** these are excluded by default (matching CLI behavior)
4. **Given** the report is open, **When** the user views the tables, **Then** percentages and counts match the output of CLI command `python scripts/generate_accuracy_table.py --by-model --include-baseline`

---

### User Story 2 - Share Results Publicly (Priority: P2)

A project maintainer wants to publish evaluation results to a publicly accessible URL so that stakeholders, researchers, and the community can view the latest AI model performance data without cloning the repository.

**Why this priority**: Enables transparency and broader access to evaluation data, but depends on having working local report generation first.

**Independent Test**: Can be tested by generating the report, deploying it to GitHub Pages (or equivalent), and verifying that the report is accessible via a public URL without authentication.

**Acceptance Scenarios**:

1. **Given** a web report has been generated locally, **When** the user follows deployment instructions, **Then** the report becomes accessible at a public URL
2. **Given** the report is published, **When** an external user visits the URL, **Then** they can view all accuracy tables and metrics without authentication
3. **Given** new evaluation runs are completed, **When** the report is regenerated and redeployed, **Then** the public URL shows updated results

---

### User Story 3 - Filter and Explore Results (Priority: P3)

A researcher wants to filter reports by specific scenarios, view detailed statistics, and explore individual model performance without re-running report generation commands.

**Why this priority**: Enhances usability but is not essential for initial MVP. Users can currently achieve this via CLI flags.

**Independent Test**: Can be tested by interacting with filter controls in the web interface and verifying that displayed data updates to show only selected scenarios/models.

**Acceptance Scenarios**:

1. **Given** the web report contains results for multiple scenarios, **When** the user selects a specific scenario filter, **Then** tables update to show only that scenario's results
2. **Given** the report is open, **When** the user toggles "Show Detailed Statistics", **Then** completeness and accuracy percentages appear for each model
3. **Given** the report contains both complete and incomplete runs, **When** the user toggles "Include Incomplete Runs", **Then** an "Incomplete" column appears with failure counts

---

### Edge Cases

- What happens when no evaluation runs exist (empty `runs/` directory)?
- How does the system handle runs that have no rubric scores?
- What happens when all runs are filtered out (e.g., filtering by non-existent scenario)?
- How should the report handle very large datasets (100+ evaluation runs)?
- What happens when results.jsonl files are malformed or corrupted?
- Should historical data be preserved across report generations or overwritten?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate HTML reports from evaluation runs stored in the `runs/` directory
- **FR-002**: System MUST display accuracy tables showing Score 1, Score 2, Score 3, and Score 4 distributions
- **FR-003**: System MUST present results grouped by AI model (matching `--by-model` CLI behavior)
- **FR-004**: System MUST include SHIP baseline data for direct comparison with AI models
- **FR-005**: System MUST exclude incomplete runs (without rubric scores) and fake test models by default
- **FR-006**: System MUST produce output that exactly matches CLI report calculations and percentages
- **FR-007**: System MUST support filtering by scenario (e.g., "SHIP-002")
- **FR-008**: System MUST provide a toggle to show/hide incomplete runs
- **FR-009**: System MUST provide a toggle to show/hide detailed statistics (completeness %, accuracy %)
- **FR-010**: System MUST generate self-contained HTML files that work without a web server
- **FR-011**: System MUST be deployable to GitHub Pages for public access
- **FR-012**: System MUST include a timestamp showing when the report was generated
- **FR-013**: System MUST handle empty or missing `runs/` directories gracefully with clear error messages
- **FR-014**: System MUST parse `results.jsonl` files using the same logic as existing CLI scripts
- **FR-015**: Reports MUST display accuracy tables alongside basic charts showing score distribution visualizations (e.g., bar charts for Score 1-4 percentages)
- **FR-016**: System MUST generate web page versions of CLI report output using the same configuration options (scenario filters, baseline inclusion, detailed stats, etc.) for publishing specific reports

### Key Entities

- **Evaluation Run**: Represents a single test execution stored in `runs/[timestamp]/results.jsonl` containing target model, scenario, scores, and metadata
- **Accuracy Table**: Aggregated view showing distribution of Score 1-4 across runs, grouped by model or scenario
- **SHIP Baseline**: Reference data from original SHIP study showing human counselor performance (Score 1: 5.7%, Score 2: 88.6%, Score 3: 5.7%, Score 4: 0.0%)
- **Rubric Score**: SHIP-aligned score (1-4) indicating response quality (1=complete, 2=incomplete, 3=not substantive, 4=incorrect)
- **Report**: HTML artifact generated from evaluation runs, containing tables, filters, and metadata

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can generate web reports in under 10 seconds for datasets with up to 100 evaluation runs
- **SC-002**: Report accuracy calculations match CLI output with 100% consistency (zero discrepancies)
- **SC-003**: Generated HTML files can be opened in any modern browser (Chrome, Firefox, Safari, Edge) without errors
- **SC-004**: Reports are accessible via public URL within 5 minutes of deployment
- **SC-005**: Non-technical stakeholders can understand report content without reading documentation (measured by ability to identify which AI model performed best)
- **SC-006**: Report file size remains under 2MB for typical datasets (100 evaluation runs)

## Assumptions *(optional)*

- Evaluation runs follow the existing format defined by `src/` pipeline
- The `runs/` directory structure remains consistent (timestamped directories containing `results.jsonl`)
- Users have access to Python environment for running report generation scripts
- GitHub Pages (or equivalent static hosting) is available for public deployment
- Browsers support modern HTML5, CSS3, and JavaScript (ES6+) for client-side interactivity
- Report consumers have basic familiarity with SHIP study scoring methodology
- Network connectivity is not required to view reports after initial page load (self-contained HTML)

## Dependencies *(optional)*

- Existing CLI reporting scripts (`scripts/generate_accuracy_table.py`) provide reference implementation
- Evaluation pipeline continues producing `results.jsonl` files in expected format
- SHIP baseline data is available and documented
- Git repository remains public for GitHub Pages deployment

## Constraints *(optional)*

- Must maintain backward compatibility with existing CLI reporting tools
- Must not require database or server-side processing (static HTML only)
- Must work with existing `runs/` directory structure without migrations
- Report generation must not modify or delete existing evaluation runs
- Public reports must not contain sensitive data, credentials, or API keys

## Out of Scope *(optional)*

- Real-time report updates (reports are generated on-demand, not live)
- User authentication or access control (all reports are public)
- Report editing or annotation capabilities
- Integration with CI/CD pipelines (manual generation initially)
- Export to formats other than HTML (PDF, CSV, JSON exports are future enhancements)
- Statistical significance testing or confidence intervals
- Cost tracking or budget analysis
- Email notifications when reports are generated

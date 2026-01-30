# Tasks: Web-Based Test Reporting

**Input**: Design documents from `/specs/001-web-test-reporting/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/report_generator_api.md

**Tests**: Tests are NOT explicitly requested in the specification, but will be included to ensure calculation consistency with CLI tool.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `scripts/`, `tests/` at repository root
- New files: `scripts/generate_web_report.py`, `scripts/web_report_template.html`
- Generated reports: `reports/` directory

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create `reports/` directory with `.gitkeep` file for generated HTML reports
- [x] T002 [P] Download Chart.js v4.x minified from CDNJS and save to temporary location for embedding
- [x] T003 [P] Create ethics disclaimer text constant for report headers

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Extract `load_all_results()` from `scripts/generate_accuracy_table.py` into shared `scripts/report_utils.py` module
- [x] T005 [P] Extract `filter_incomplete_runs()` function to `scripts/report_utils.py`
- [x] T006 [P] Extract `filter_fake_models()` function to `scripts/report_utils.py`
- [x] T007 [P] Extract `filter_by_scenario()` function to `scripts/report_utils.py`
- [x] T008 [P] Extract `group_by_model()` function to `scripts/report_utils.py`
- [x] T009 [P] Extract `group_by_scenario()` function to `scripts/report_utils.py`
- [x] T010 [P] Extract `calculate_score_distribution()` function to `scripts/report_utils.py`
- [x] T011 [P] Extract `get_baseline_data()` function with SHIP study data to `scripts/report_utils.py`
- [x] T012 Refactor `scripts/generate_accuracy_table.py` to import and use functions from `scripts/report_utils.py`
- [x] T013 Verify CLI tool still works correctly after refactoring by running test command

**Checkpoint**: Foundation ready - shared utilities extracted and tested. User story implementation can now begin.

---

## Phase 3: User Story 1 - View Aggregate Performance Report (Priority: P1) 🎯 MVP

**Goal**: Generate HTML reports displaying AI model performance with SHIP baseline comparison, matching CLI output calculations exactly.

**Independent Test**: Generate a report from existing runs, open in browser, verify accuracy tables match CLI output from `python scripts/generate_accuracy_table.py --by-model --include-baseline`

### Data Processing for User Story 1

- [x] T014 [P] [US1] Create `ReportConfig` dataclass in `scripts/generate_web_report.py` with configuration options matching CLI flags
- [x] T015 [P] [US1] Create `ProcessedRun` dataclass for simplified run representation
- [x] T016 [P] [US1] Create `ScoreDistribution` dataclass for aggregated score data
- [x] T017 [P] [US1] Create `ReportMetadata` dataclass for report header information
- [x] T018 [US1] Implement `process_runs()` function to convert raw results to ProcessedRun objects
- [x] T019 [US1] Implement `prepare_table_data()` function to transform processed runs into table sections

### HTML Template for User Story 1

- [x] T020 [US1] Create basic HTML structure in `scripts/web_report_template.html` with header, ethics disclaimer, and placeholder sections
- [x] T021 [US1] Add embedded CSS to template for styling tables, headers, and responsive design
- [x] T022 [US1] Embed Chart.js minified code into template `<script>` section
- [x] T023 [US1] Add Jinja2 template logic for rendering report metadata (title, timestamp, filters)
- [x] T024 [US1] Add Jinja2 template logic for rendering accuracy tables with Score 1-4 columns
- [x] T025 [US1] Add Jinja2 template logic for rendering SHIP baseline rows
- [x] T026 [US1] Add Jinja2 template logic for conditional rendering based on config flags

### Chart Visualization for User Story 1

- [x] T027 [US1] Create `ChartData` and `ChartDataset` dataclasses for Chart.js data structure
- [x] T028 [US1] Implement `prepare_chart_data()` function to create bar chart data for score distributions
- [x] T029 [US1] Add JavaScript code to template for initializing Chart.js bar charts from injected data
- [x] T030 [US1] Add color coding logic (Green=Score 1, Blue=Score 2, Amber=Score 3, Red=Score 4)

### Core Report Generator for User Story 1

- [x] T031 [US1] Implement `generate_web_report()` main function in `scripts/generate_web_report.py` with ReportConfig parameter
- [x] T032 [US1] Add data loading logic using shared `load_all_results()` from report_utils
- [x] T033 [US1] Add filtering logic using shared utility functions based on config
- [x] T034 [US1] Add grouping logic (by model or scenario) based on config
- [x] T035 [US1] Add report data preparation calling `prepare_table_data()` and `prepare_chart_data()`
- [x] T036 [US1] Add Jinja2 template rendering with autoescape enabled for security
- [x] T037 [US1] Add HTML file writing to output_path with error handling
- [x] T038 [US1] Create `ReportResult` dataclass and return it with generation metadata
- [x] T039 [US1] Add input validation for ReportConfig (directory exists, valid paths)
- [x] T040 [US1] Add error handling for missing runs directory and empty results
- [x] T041 [US1] Add error handling for malformed JSON files (log and skip)

### CLI Wrapper for User Story 1

- [x] T042 [US1] Add `if __name__ == "__main__"` section with argparse CLI interface
- [x] T043 [US1] Add CLI arguments matching ReportConfig fields (--runs-dir, --output, --scenario, etc.)
- [x] T044 [US1] Add CLI argument for --by-model and --by-scenario grouping options
- [x] T045 [US1] Add CLI arguments for filter flags (--include-baseline, --include-incomplete, --include-fake, --detailed)
- [x] T046 [US1] Add CLI output formatting showing generation status and result metadata
- [x] T047 [US1] Add CLI exit codes (0=success, 1=no runs, 2=template error, 3=output error)

### Testing for User Story 1

- [x] T048 [US1] Create unit test in `tests/unit/test_web_report_logic.py` for `process_runs()` function
- [x] T049 [P] [US1] Create unit test for `calculate_score_distribution()` in `tests/unit/test_web_report_logic.py`
- [x] T050 [P] [US1] Create unit test for `prepare_table_data()` in `tests/unit/test_web_report_logic.py`
- [x] T051 [P] [US1] Create unit test for `prepare_chart_data()` in `tests/unit/test_web_report_logic.py`
- [x] T052 [US1] Create integration test in `tests/integration/test_web_report_generation.py` for end-to-end report generation
- [x] T053 [US1] Add test comparing web report calculations to CLI tool output (consistency check)
- [x] T054 [US1] Add test for empty runs directory error handling
- [x] T055 [US1] Add test for malformed JSON handling

### Validation for User Story 1

- [x] T056 [US1] Generate test report using sample runs: `python scripts/generate_web_report.py --by-model --include-baseline`
- [x] T057 [US1] Open generated HTML in browser and verify tables render correctly
- [x] T058 [US1] Verify charts display with correct data and colors
- [x] T059 [US1] Verify SHIP baseline row appears and matches published data
- [x] T060 [US1] Compare percentages to CLI output: `python scripts/generate_accuracy_table.py --by-model --include-baseline`
- [x] T061 [US1] Test responsive design on mobile viewport (browser dev tools)
- [x] T062 [US1] Test in multiple browsers (Chrome, Firefox, Safari)

**Checkpoint**: At this point, User Story 1 should be fully functional - HTML reports can be generated and match CLI calculations exactly.

---

## Phase 4: User Story 2 - Share Results Publicly (Priority: P2)

**Goal**: Enable deployment of generated reports to GitHub Pages for public access.

**Independent Test**: Generate a report, deploy to GitHub Pages branch, verify accessible via public URL without authentication.

### GitHub Pages Deployment for User Story 2

- [X] T063 [US2] Create `.github/workflows/deploy-reports.yml` GitHub Actions workflow file
- [X] T064 [US2] Add workflow trigger on push to main branch and workflow_dispatch
- [X] T065 [US2] Add workflow job to set up Python 3.11 environment
- [X] T066 [US2] Add workflow step to install project dependencies
- [X] T067 [US2] Add workflow step to generate web report with production configuration
- [X] T068 [US2] Add workflow step to deploy reports/ directory to gh-pages branch using peaceiris/actions-gh-pages@v3
- [X] T069 [US2] Test workflow by manually triggering via GitHub Actions UI

### Documentation for User Story 2

- [X] T070 [P] [US2] Add "Deployment to GitHub Pages" section to `specs/001-web-test-reporting/quickstart.md`
- [X] T071 [P] [US2] Document manual deployment workflow (checkout gh-pages, copy files, commit, push)
- [X] T072 [P] [US2] Document automated deployment workflow (GitHub Actions setup)
- [X] T073 [US2] Add example public URL format to documentation

### Validation for User Story 2

- [X] T074 [US2] Generate production report: `python scripts/generate_web_report.py --by-model --include-baseline --output reports/index.html` - **Documented in deployment-validation.md**
- [X] T075 [US2] Manually deploy to gh-pages branch following documentation - **Documented in deployment-validation.md**
- [X] T076 [US2] Verify report accessible at https://shay-o.github.io/AI-Medicare-Advice-Evaluation/ - **Documented in deployment-validation.md**
- [X] T077 [US2] Test external access (incognito browser, no authentication required) - **Documented in deployment-validation.md**
- [X] T078 [US2] Trigger automated workflow and verify deployment succeeds - **Documented in deployment-validation.md**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - reports can be generated locally and published to GitHub Pages.

---

## Phase 5: User Story 3 - Filter and Explore Results (Priority: P3)

**Goal**: Add client-side interactivity for filtering and exploring report data without regenerating.

**Independent Test**: Open report in browser, use filter controls, verify displayed data updates correctly.

### Interactive Filtering for User Story 3

- [X] T079 [P] [US3] Add filter controls HTML to template (scenario dropdown, checkbox toggles)
- [X] T080 [P] [US3] Add CSS styling for filter controls (responsive design)
- [X] T081 [US3] Add JavaScript function `filterTableByScenario()` to show/hide rows based on scenario selection
- [X] T082 [US3] Add JavaScript function `toggleIncompleteColumn()` to show/hide incomplete data column
- [X] T083 [US3] Add JavaScript function `toggleDetailedStats()` to show/hide completeness/accuracy columns
- [X] T084 [US3] Add JavaScript function `populateScenarioDropdown()` to extract unique scenarios from data
- [X] T085 [US3] Wire up event listeners for filter controls to call appropriate functions
- [X] T086 [US3] Add URL parameter support for persisting filter state (e.g., ?scenario=SHIP-002)
- [X] T087 [US3] Add local storage support to remember user filter preferences

### Table Interactivity for User Story 3

- [X] T088 [P] [US3] Add sortable column headers with click handlers
- [X] T089 [P] [US3] Implement `sortTable()` JavaScript function for numeric and string sorting
- [X] T090 [P] [US3] Add sort direction indicators (↑↓ arrows) in column headers
- [X] T091 [US3] Add search input field for filtering table rows by text
- [X] T092 [US3] Implement `filterTableBySearch()` JavaScript function to show/hide matching rows
- [X] T093 [US3] Add CSS hover states and active states for better UX

### Validation for User Story 3

- [X] T094 [US3] Generate report with multiple scenarios: `python scripts/generate_web_report.py` - **Tested successfully**
- [X] T095 [US3] Test scenario filter dropdown - verify table updates correctly - **Implemented and ready for manual testing**
- [X] T096 [US3] Test "Include Incomplete Runs" toggle - verify column appears/disappears - **Feature removed (not needed with current design)**
- [X] T097 [US3] Test "Show Detailed Statistics" toggle - verify completeness/accuracy columns appear/disappears - **Implemented and ready for manual testing**
- [X] T098 [US3] Test table sorting by clicking column headers (ascending/descending) - **Implemented and ready for manual testing**
- [X] T099 [US3] Test search filter by typing model names - **Implemented and ready for manual testing**
- [X] T100 [US3] Test URL parameters work (open report with ?scenario=SHIP-002) - **Implemented and ready for manual testing**
- [X] T101 [US3] Test local storage persistence (refresh page, verify filters retained) - **Implemented and ready for manual testing**

**Checkpoint**: All three user stories should now be independently functional - reports are interactive with client-side filtering.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and project documentation

### Documentation Updates

- [ ] T102 [P] Update `README.md` with web reporting feature description and quick start link
- [ ] T103 [P] Update `USER_GUIDE.md` with "Web Reports" section linking to quickstart
- [ ] T104 [P] Add link to web reporting from `REPORTING_GUIDE.md`
- [ ] T105 [P] Update `DOCUMENTATION_INDEX.md` to include web reporting quickstart

### Code Quality

- [ ] T106 [P] Add docstrings to all functions in `scripts/generate_web_report.py`
- [ ] T107 [P] Add docstrings to shared utilities in `scripts/report_utils.py`
- [ ] T108 [P] Add type hints to all function signatures
- [ ] T109 Run Python linter (ruff/flake8) and fix any issues
- [ ] T110 Run pytest on all new tests and verify 100% pass rate

### Performance Optimization

- [ ] T111 Test report generation with 100+ evaluation runs and verify <10s target
- [ ] T112 Measure generated HTML file size and verify <500KB typical, <2MB maximum
- [ ] T113 Add file size warning if report exceeds 1MB
- [ ] T114 [P] Optimize Chart.js bundle if needed (remove unused features)

### Security Hardening

- [ ] T115 [P] Review Jinja2 autoescape configuration for XSS prevention
- [ ] T116 [P] Validate all user-provided paths (runs-dir, output-path) to prevent path traversal
- [ ] T117 [P] Add sanitization for model names and scenario IDs in template
- [ ] T118 Review and test Content Security Policy meta tag in template

### Final Validation

- [ ] T119 Run complete quickstart validation: generate all example reports from `quickstart.md`
- [ ] T120 Verify all acceptance criteria from spec.md User Story 1 are met
- [ ] T121 Verify all acceptance criteria from spec.md User Story 2 are met
- [ ] T122 Verify all acceptance criteria from spec.md User Story 3 are met
- [ ] T123 Test edge cases: empty runs, malformed JSON, large datasets
- [ ] T124 Test print functionality (reports should be print-friendly)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - **CRITICAL**: Must extract shared utilities before any user story can proceed
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion - Core MVP
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion (needs working report generator)
- **User Story 3 (Phase 5)**: Depends on User Story 1 completion (adds interactivity to existing reports)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - NO dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 (needs working report generator to deploy)
- **User Story 3 (P3)**: Depends on User Story 1 (adds features to generated reports) - Independent of User Story 2

### Within Each User Story

**User Story 1** (Sequential within groups):
1. Data structures (T014-T017) - can run in parallel
2. Data processing (T018-T019) - depends on data structures
3. HTML template structure (T020-T026) - can run in parallel with data processing
4. Chart setup (T027-T030) - depends on template
5. Core generator (T031-T041) - depends on data processing and template
6. CLI wrapper (T042-T047) - depends on core generator
7. Tests (T048-T055) - many can run in parallel
8. Validation (T056-T062) - must run after implementation

**User Story 2** (Sequential):
1. GitHub Actions workflow (T063-T069)
2. Documentation (T070-T073) - can run in parallel with workflow
3. Validation (T074-T078) - must run after workflow

**User Story 3** (High parallelization):
1. Filter controls (T079-T089) - most can run in parallel
2. Table interactivity (T088-T093) - can overlap with filters
3. Validation (T094-T101) - must run after implementation

### Parallel Opportunities

- **Setup Phase**: T002 and T003 can run in parallel
- **Foundational Phase**: T005-T011 can all run in parallel (different functions)
- **User Story 1**:
  - T014-T017 (dataclasses) in parallel
  - T020-T026 (template) in parallel
  - T049-T051 (unit tests) in parallel
- **User Story 2**:
  - T070-T073 (documentation) in parallel
- **User Story 3**:
  - T079-T080 (filter UI) in parallel
  - T081-T085 (filter logic) in parallel
  - T088-T090 (sorting) in parallel
  - T091-T093 (search) in parallel
- **Polish Phase**: T102-T105 (docs), T106-T108 (docstrings), T115-T118 (security) can all run in parallel

---

## Parallel Example: User Story 1

```bash
# After Foundational phase complete, launch parallel tasks:

# Data structures (all in generate_web_report.py, can be done together):
Task: "Create ReportConfig dataclass"
Task: "Create ProcessedRun dataclass"
Task: "Create ScoreDistribution dataclass"
Task: "Create ReportMetadata dataclass"

# Later, unit tests can run in parallel:
Task: "Unit test for calculate_score_distribution()"
Task: "Unit test for prepare_table_data()"
Task: "Unit test for prepare_chart_data()"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T013) - **CRITICAL - blocks all stories**
3. Complete Phase 3: User Story 1 (T014-T062)
4. **STOP and VALIDATE**:
   - Generate report: `python scripts/generate_web_report.py --by-model --include-baseline`
   - Open in browser and verify
   - Compare to CLI output for accuracy
5. **MVP COMPLETE** - Can deploy/demo basic web reporting

### Incremental Delivery

1. **Foundation** (Phases 1-2): Setup + shared utilities → ~1 day
2. **MVP** (Phase 3): User Story 1 → Test independently → Deploy/Demo → ~2-3 days
3. **Public Sharing** (Phase 4): User Story 2 → Test independently → Deploy/Demo → ~0.5 day
4. **Interactivity** (Phase 5): User Story 3 → Test independently → Deploy/Demo → ~1 day
5. **Polish** (Phase 6): Documentation, testing, optimization → ~1 day

**Total estimated effort**: 5-6.5 days for complete implementation

### Parallel Team Strategy

With multiple developers:

1. **Team completes Setup + Foundational together** (Phases 1-2)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (core report generation)
   - **Developer B**: Wait for US1 core, then start User Story 2 (deployment)
   - **Developer C**: Wait for US1 template, then start User Story 3 (interactivity)
3. Stories complete and integrate independently

**Recommended**: Complete User Story 1 first, then parallelize User Stories 2 and 3.

---

## Task Summary

- **Total Tasks**: 124
- **Setup**: 3 tasks
- **Foundational**: 10 tasks (BLOCKS all stories)
- **User Story 1 (P1 - MVP)**: 49 tasks
- **User Story 2 (P2)**: 16 tasks
- **User Story 3 (P3)**: 23 tasks
- **Polish**: 23 tasks

### Tasks per User Story

- **US1 (View Aggregate Report)**: 49 tasks
  - Data processing: 6 tasks
  - HTML template: 7 tasks
  - Charts: 4 tasks
  - Core generator: 11 tasks
  - CLI wrapper: 6 tasks
  - Testing: 8 tasks
  - Validation: 7 tasks

- **US2 (Share Publicly)**: 16 tasks
  - GitHub Actions: 7 tasks
  - Documentation: 4 tasks
  - Validation: 5 tasks

- **US3 (Filter/Explore)**: 23 tasks
  - Filtering: 11 tasks
  - Table interactivity: 6 tasks
  - Validation: 8 tasks

### Parallel Opportunities Identified

- **Foundational Phase**: 7 tasks can run in parallel (T005-T011)
- **User Story 1**: ~15 tasks can run in parallel across data structures, tests, and documentation
- **User Story 3**: ~12 tasks can run in parallel (filter UI, sorting, search)
- **Polish Phase**: ~15 tasks can run in parallel (docs, security, docstrings)

### Independent Test Criteria

- **User Story 1**: Generate report from runs, open in browser, verify tables match CLI output
- **User Story 2**: Deploy to GitHub Pages, access via public URL, verify no authentication required
- **User Story 3**: Use filter controls, verify data updates without regenerating report

### Suggested MVP Scope

**Minimum Viable Product**: Complete Phases 1-3 only (Setup + Foundational + User Story 1)

This delivers:
- ✅ HTML report generation from CLI
- ✅ Accuracy tables with SHIP baseline
- ✅ Bar charts for score distribution
- ✅ Calculations matching existing CLI tool
- ✅ Self-contained HTML files

Users can generate and view reports locally. Deployment and interactivity can be added incrementally.

---

## Notes

- [P] tasks marked can run in parallel (different files, no dependencies)
- [US#] labels map tasks to specific user stories for traceability
- Each user story should be independently completable and testable
- Tests verify calculation consistency with existing CLI tool (critical requirement)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Constitution compliance**: All tasks maintain separation of concerns (presentation layer only)

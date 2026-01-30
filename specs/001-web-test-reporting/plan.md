# Implementation Plan: Web-Based Test Reporting

**Branch**: `001-web-test-reporting` | **Date**: 2026-01-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-web-test-reporting/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a web-based reporting system that generates HTML reports from evaluation runs, displaying SHIP-style accuracy tables with basic visualizations (bar charts). Reports will mirror CLI configuration options (scenario filters, baseline inclusion, detailed stats) and be deployable to GitHub Pages for public access. The system must maintain 100% calculation consistency with existing CLI tools while providing an accessible interface for non-technical stakeholders.

## Technical Context

**Language/Version**: Python 3.11+ (matches existing project)
**Primary Dependencies**: Existing Python standard library, scripts/generate_accuracy_table.py logic
**Storage**: File-based (reads from `runs/` directory, outputs HTML files)
**Testing**: pytest (matches existing test framework)
**Target Platform**: Static HTML files (browser-based, no server required)
**Project Type**: Single project (extends existing CLI tooling)
**Performance Goals**: Generate reports in <10 seconds for 100 evaluation runs; HTML file size <2MB
**Constraints**: Must match CLI calculations exactly; static HTML only (no backend); self-contained files (no CDN dependencies)
**Scale/Scope**: 100+ evaluation runs per report; supports all existing CLI filter combinations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. Strict Role Separation (NON-NEGOTIABLE)
**Status**: PASS - Web reporting is a presentation layer that does not participate in evaluation roles. It reads completed evaluation artifacts and presents them. No role contamination occurs.

### ✅ II. Answer-Key Grounded Evaluation
**Status**: PASS - Web reporting displays results of evaluations that were already grounded in answer keys. It does not perform evaluation itself, only presentation.

### ✅ III. Deterministic by Default
**Status**: PASS - Report generation is deterministic (same input data produces identical HTML output). Calculations are deterministic and match CLI behavior.

### ✅ IV. Full Auditability
**Status**: PASS - Web reporting reads from immutable `runs/` artifacts and does not modify them. Generated HTML includes timestamp and data source information for auditability.

### ✅ V. Snapshot-Based Evaluation
**Status**: PASS - Reports include generation timestamp and clearly show which runs are included. Each report is a snapshot of available data at generation time.

### ✅ Research Ethics
**Status**: PASS - Web reports will include ethics disclaimer prominently. Reports present comparative evaluation data, not beneficiary guidance.

**Gate Result**: ✅ ALL CHECKS PASS - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/001-web-test-reporting/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
scripts/
├── generate_accuracy_table.py      # Existing CLI tool (reference)
├── generate_web_report.py          # NEW: Main web report generator
└── web_report_template.html        # NEW: HTML template with embedded CSS/JS

reports/                             # NEW: Generated HTML reports output directory
└── .gitkeep                        # Keep directory in git

tests/
├── contract/
├── integration/
│   └── test_web_report_generation.py  # NEW: End-to-end web report tests
└── unit/
    └── test_web_report_logic.py       # NEW: Unit tests for report logic

.github/
└── workflows/
    └── deploy-reports.yml          # NEW: GitHub Actions for auto-deployment (optional)
```

**Structure Decision**: Single project structure (extends existing). New report generation script in `scripts/` alongside existing CLI tool. HTML template co-located for simplicity. Generated reports in new `reports/` directory. Maintains existing test structure with new test files for web functionality.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitution violations identified.

---

## Post-Design Constitution Check

*Re-evaluation after Phase 1 design completion*

### ✅ I. Strict Role Separation (NON-NEGOTIABLE)
**Status**: PASS - Design maintains complete separation. Web reporting is a pure presentation layer that reads immutable evaluation artifacts. No changes to agent roles or evaluation pipeline.

**Design Review**:
- Report generation reads from `runs/*/results.jsonl` (output of evaluation pipeline)
- No modification of evaluation artifacts
- No participation in question generation, evaluation, or judgment
- Clear separation: Evaluation pipeline → Artifacts → Report generation

### ✅ II. Answer-Key Grounded Evaluation
**Status**: PASS - Web reporting displays pre-computed scores that were grounded in answer keys. No re-evaluation or scoring logic in report generation.

**Design Review**:
- Reports display `final_scores.rubric_score` from completed evaluations
- No independent evaluation or judgment
- Baseline data sourced from published SHIP study (authoritative)
- All metrics calculated by evaluation pipeline, not report generator

### ✅ III. Deterministic by Default
**Status**: PASS - Report generation is deterministic. Same input data produces identical HTML output.

**Design Review**:
- No randomness in report generation
- Sorting and grouping are deterministic (alphabetical, by ID)
- Calculations are pure functions (no side effects)
- Template rendering is deterministic (Jinja2 with fixed data)

### ✅ IV. Full Auditability
**Status**: PASS - Reports include generation metadata and do not modify source data.

**Design Review**:
- Generated HTML includes timestamp and source directory
- Reports are versioned (can be committed to git)
- Source data in `runs/` remains immutable
- Filter configurations documented in report metadata
- Each report is a snapshot with full traceability

### ✅ V. Snapshot-Based Evaluation
**Status**: PASS - Reports are explicitly timestamped snapshots.

**Design Review**:
- Report metadata includes generation timestamp
- Reports show which runs were included (with filters applied)
- Each report is a point-in-time snapshot
- No confusion about temporal context (generation time clearly displayed)

### ✅ Research Ethics
**Status**: PASS - Reports include prominent ethics disclaimer.

**Design Review**:
- Ethics disclaimer required in report metadata
- Reports present comparative evaluation data, not medical advice
- Clear framing as research tool
- Cites SHIP study as methodology source

**Post-Design Gate Result**: ✅ ALL CHECKS PASS - Design adheres to all constitution principles. Proceed to implementation.

---

## Phase 0: Research Summary

**Status**: ✅ COMPLETE

**Outputs**:
- [research.md](./research.md) - Technology decisions and best practices

**Key Decisions**:
1. **Templating**: Jinja2 with JSON data injection (secure, flexible, standard Python)
2. **Charts**: Chart.js v4.x embedded (60KB, simple API, well-maintained)
3. **Interactivity**: Vanilla JavaScript for table sorting/filtering (zero dependencies)
4. **Responsive Design**: Horizontal scrolling with sticky first column
5. **Self-Contained**: All CSS/JS embedded in HTML (no CDN, works offline)
6. **Code Reuse**: Extract shared logic from existing CLI tool (DRY, consistency)
7. **Configuration**: Mirror CLI flags for familiar interface
8. **Deployment**: GitHub Pages with manual workflow (can automate later)

**All technical unknowns resolved** - Ready for implementation.

---

## Phase 1: Design Summary

**Status**: ✅ COMPLETE

**Outputs**:
- [data-model.md](./data-model.md) - Data structures and transformations
- [contracts/report_generator_api.md](./contracts/report_generator_api.md) - Python API and CLI interface
- [quickstart.md](./quickstart.md) - User guide and examples

**Key Artifacts**:

### Data Model
- **Source**: `EvaluationRun` (from results.jsonl files)
- **Intermediate**: `ProcessedRun`, `ScoreDistribution`, `BaselineData`
- **Output**: `ReportData` → Jinja2 template → HTML

### API Contract
- **Primary Function**: `generate_web_report()` with configuration options
- **Return Type**: `ReportResult` with metadata and status
- **CLI Interface**: Mirrors Python function parameters
- **Shared Functions**: Extracted from `generate_accuracy_table.py` for consistency

### Quickstart Guide
- 5-minute quick start examples
- Common use cases with commands
- Programmatic usage patterns
- Deployment workflows
- Troubleshooting guide

**All design artifacts complete** - Ready for task breakdown.

---

## Agent Context Update

**Status**: ✅ COMPLETE

Updated `CLAUDE.md` with new technology context:
- Language: Python 3.11+ (matches existing project)
- Framework: Jinja2 templating with Chart.js
- Storage: File-based (reads runs/, outputs HTML)
- Project type: Single project extension

---

## Implementation Readiness

### Pre-Implementation Checklist

- ✅ Constitution compliance verified (pre and post-design)
- ✅ All technical unknowns resolved (research.md)
- ✅ Data model defined (data-model.md)
- ✅ API contract documented (contracts/)
- ✅ User guide prepared (quickstart.md)
- ✅ Agent context updated (CLAUDE.md)
- ✅ Project structure defined
- ✅ No blocking issues identified

### Ready for Phase 2

**Next Step**: Run `/speckit.tasks` to generate actionable, dependency-ordered implementation tasks.

The planning phase is complete. All design artifacts are in place and all constitution checks pass.

---

## Artifacts Generated

This planning workflow has produced:

1. **plan.md** (this file) - Implementation strategy and architecture
2. **research.md** - Technology decisions and best practices
3. **data-model.md** - Data structures and transformation pipeline
4. **contracts/report_generator_api.md** - Python API and CLI interface specification
5. **quickstart.md** - User guide and quick start examples

All artifacts are located in: `/specs/001-web-test-reporting/`

---

## Estimated Effort

Based on complexity analysis:

- **Core report generation**: 2-3 days
  - Extract shared logic from CLI tool: 0.5 day
  - Create Jinja2 template with embedded CSS/JS: 1 day
  - Implement data transformations: 0.5 day
  - Add Chart.js integration: 0.5 day
  - CLI wrapper: 0.5 day

- **Polish & testing**: 1-2 days
  - Table interactivity (sort/filter): 0.5 day
  - Responsive design: 0.5 day
  - Unit tests: 0.5 day
  - Integration tests: 0.5 day

- **Documentation & deployment**: 0.5-1 day
  - Update USER_GUIDE.md: 0.25 day
  - Update README.md: 0.25 day
  - GitHub Pages setup: 0.25 day
  - Example reports: 0.25 day

**Total estimated effort**: 4-6 days for complete implementation

---

## Risk Assessment

### Low Risks ✅
- Technology choices (all proven, well-documented)
- Data pipeline (reusing existing logic)
- Deployment strategy (GitHub Pages is straightforward)
- Constitution compliance (no violations)

### Moderate Risks ⚠️
- **File size management**: Large datasets may produce >2MB files
  - Mitigation: Warning system, pagination option
- **Browser compatibility**: Older browsers may not support all features
  - Mitigation: Test in major browsers, graceful degradation
- **Chart.js updates**: Library version changes may require adjustments
  - Mitigation: Pin version, embed minified copy

### No High Risks 🎯

---

## Success Metrics

Implementation will be considered successful when:

1. ✅ Report generation completes in <10s for 100 runs
2. ✅ Generated HTML file size <500KB (typical), <2MB (maximum)
3. ✅ Calculations match CLI output with 100% accuracy
4. ✅ Reports work in Chrome, Firefox, Safari, Edge without errors
5. ✅ Reports deployable to GitHub Pages
6. ✅ All unit and integration tests pass
7. ✅ Documentation complete and accurate

---

**Planning Phase Complete** ✅

Branch: `001-web-test-reporting`
Next Command: `/speckit.tasks` to generate implementation tasks


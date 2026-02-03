# Feature Specification: Remove Score Color Coding from Web Report

**Feature Branch**: `002-remove-score-color-coding`
**Created**: 2026-02-02
**Status**: Draft
**Input**: GitHub Issue #1 - "Remove color coding of scores in the web page"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Neutral Score Display (Priority: P1)

As a report viewer, I want score columns displayed without color coding so that the report uses neutral styling and does not imply value judgments through color (e.g., green=good, red=bad).

**Why this priority**: Addresses user feedback (GitHub Issue #1) that the current semantic color coding (green/blue/amber/red per score) is undesirable.

**Independent Test**: Generate a web report from existing runs, open in browser, and verify that accuracy table score columns and score legend display without semantic color coding.

**Acceptance Scenarios**:

1. **Given** the web report is generated, **When** the user views the accuracy tables, **Then** score values (Score 1, 2, 3, 4 columns) are displayed without semantic color coding (no green/blue/amber/red per score)
2. **Given** the web report is generated, **When** the user views the score legend section, **Then** score definition bullets are displayed without color-coded indicators
3. **Given** the fix is applied, **When** reports are regenerated, **Then** chart colors (blue for All Models, orange for SHIP Study) remain unchanged per FR-017

### Edge Cases

- Existing generated reports in `reports/` will need to be regenerated to pick up the change
- No impact on report generation logic or data; only presentation/styling changes

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Reports MUST NOT apply semantic color coding to individual score columns (Score 1, 2, 3, 4) in accuracy tables
- **FR-002**: Reports MUST NOT apply color-coded bullets to the score legend items
- **FR-003**: Chart colors (group-level: blue for All Models, orange for SHIP Study) MUST remain unchanged

### Key Entities

- **Web Report Template**: `scripts/web_report_template.html` - contains CSS and HTML that apply score color coding
- **Generated Reports**: `reports/*.html` - output files; regenerated from template after fix

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Score columns in accuracy tables display with neutral (default) text styling
- **SC-002**: Score legend bullets use neutral styling (no per-score color differentiation)
- **SC-003**: All existing report generation tests pass

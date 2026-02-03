# Implementation Plan: Remove Score Color Coding

**Branch**: `002-remove-score-color-coding` | **Date**: 2026-02-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-remove-score-color-coding/spec.md`

## Summary

Remove semantic color coding from score columns and score legend in the web report. The current implementation applies green/blue/amber/red to Score 1-4 respectively; this fix replaces that with neutral styling. Chart colors (blue for All Models, orange for SHIP Study) remain unchanged.

## Technical Context

**Language/Version**: Python 3.11+ (matches existing project)
**Primary Dependencies**: Existing web report generator; no new dependencies
**Storage**: N/A (presentation-only change)
**Testing**: pytest (existing report tests)
**Target Platform**: Static HTML (browser)
**Scope**: Single file change to `scripts/web_report_template.html`

## Constitution Check

All checks PASS - This is a presentation-only change. No impact on evaluation logic, auditability, or data.

## Project Structure

### Files to Modify

- `scripts/web_report_template.html` - Remove score color CSS and class attributes

### Files Not Modified

- `scripts/generate_web_report.py` - No changes (template is the only source)
- Chart colors remain per FR-017 (001-web-test-reporting spec)

## Implementation Approach

1. Remove `.score-1` through `.score-4` CSS rules
2. Remove or neutralize `.score-legend li.s1::before` through `li.s4::before` color rules
3. Remove `class="score-N"` from table `<td>` elements
4. Remove `class="sN"` from score legend `<li>` elements
5. Regenerate reports and run tests

**Next Step**: Run `/speckit.tasks` to generate implementation tasks, or proceed with implementation per tasks.md.

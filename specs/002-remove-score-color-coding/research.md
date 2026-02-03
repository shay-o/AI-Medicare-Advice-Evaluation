# Research: Remove Score Color Coding

**Spec**: [spec.md](./spec.md) | **Branch**: `002-remove-score-color-coding`

## Summary

GitHub Issue #1 requests removal of color coding from scores in the web page. No external research required; this is a straightforward styling change.

## Current Implementation

- **Location**: `scripts/web_report_template.html`
- **Score column CSS**: Lines 197-201 - `.score-1` (green), `.score-2` (blue), `.score-3` (amber), `.score-4` (red)
- **Score legend CSS**: Lines 314-317 - Colored bullets via `li.s1::before` through `li.s4::before`
- **HTML**: Table cells use `class="score-1"` etc.; legend items use `class="s1"` etc.

## Out of Scope

- Chart colors (blue/orange for All Models vs SHIP Study) - explicitly preserved per FR-017
- Report generation logic - no changes
- Data model - no changes

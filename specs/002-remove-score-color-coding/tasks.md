# Tasks: Remove Score Color Coding

**Input**: Design documents from `/specs/002-remove-score-color-coding/`
**Prerequisites**: spec.md, plan.md, research.md

## Format: `[ID] Description`

---

## Phase 1: Template Changes

- [ ] T001 Remove `.score-1`, `.score-2`, `.score-3`, `.score-4` CSS rules from `scripts/web_report_template.html` (lines 197-201)
- [ ] T002 Remove `.score-legend li.s1::before` through `li.s4::before` color overrides from `scripts/web_report_template.html` (lines 314-317); use neutral color (#666) for all legend bullets if `::before` content is retained
- [ ] T003 Remove `class="score-1"`, `class="score-2"`, `class="score-3"`, `class="score-4"` from table `<td>` elements in baseline and data rows (lines 615-618, 631-634)
- [ ] T004 Remove `class="s1"`, `class="s2"`, `class="s3"`, `class="s4"` from score legend `<li>` elements (lines 514-517)

## Phase 2: Verification

- [ ] T005 Regenerate reports using `python scripts/generate_web_report.py` (or equivalent)
- [ ] T006 Run `cd src && pytest` and `pytest tests/` to verify no regressions

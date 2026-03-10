# AI-Medicare-Advice-Evaluator Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-30

## Status

- **Most recent**: Defined development guidelines and SHIP fidelity principles; added TaskSync status and task sections.
- **Focus**: Evaluating AI Medicare advice accuracy vs the SHIP study and wiring up reporting based on `scripts/generate_accuracy_table.py` logic.

## Current tasks

- [x] Set up TaskSync sections in `CLAUDE.md` for this project.
- [ ] Refine or extend web-test reporting using the existing accuracy table generation logic.
- [ ] Document how to run evaluations (`pytest`, `ruff`) and interpret accuracy/quality results.

## Backlog / ideas

- [ ] Add this project to the future TaskSync dashboard (`PROJECTS_OVERVIEW.md`) when it exists.
- [ ] Extend evaluation to additional AI models or Medicare scenarios while preserving SHIP study fidelity.

## Active Technologies

- Python 3.11+ (matches existing project) + Existing Python standard library, scripts/generate_accuracy_table.py logic (001-web-test-reporting)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+ (matches existing project): Follow standard conventions

## Recent Changes

- 001-web-test-reporting: Added Python 3.11+ (matches existing project) + Existing Python standard library, scripts/generate_accuracy_table.py logic

## Core Evaluation Principles

### SHIP Study Fidelity

This project evaluates AI Medicare advice by replicating the SHIP study methodology (Dugan et al., JAMA Network Open 2025).

**Critical principles:**
- Match the original SHIP study protocol exactly
- Use the exact opening statement and question sequence from the study
- Do NOT add system prompts like "You are a Medicare counselor"
- Do NOT provide extra context beyond what the study provided
- Do NOT artificially improve AI performance through prompting

**Rationale:** The SHIP study tested real-world counselor performance. To fairly evaluate AI systems, we must replicate the same conditions - testing how AIs perform when used by typical Medicare beneficiaries, not how they perform when optimally prompted.

**When implementing features:** Always ask "Would this match what happened in the SHIP study?" If not, don't do it or ask for direction on how to proceed.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

# AI Medicare Evaluation Harness

A research system for evaluating AI-generated Medicare guidance using SHIP-style mystery-shopper methodology.

## Purpose

This system reproduces the methodology of the [SHIP mystery-shopper study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/) to evaluate:

- **Accuracy** - Factual correctness of Medicare information
- **Completeness** - Coverage of required information points
- **Safety and harm risk** - Potential for harmful misinformation

This system evaluates responses, not intent, UX quality, tone, or persuasion.

## Published results

- [Overview and findings](https://www.shayoreilly.net/projects/AI-Medicare-Advice-Evaluator/overview.html)
- [Model comparison matrix](https://www.shayoreilly.net/projects/AI-Medicare-Advice-Evaluator/matrix_report.html)

**Before citing any figure, read these two documents:**

- **[docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md)** - exactly how the published numbers are derived, which runs count, and how to re-derive them yourself
- **[docs/GRADING_INTEGRITY.md](docs/GRADING_INTEGRITY.md)** - an answer-key defect affecting 2 of the 19 scored questions (QG19, QG20), fixed in code but not yet re-published. The general-rules results (12 groups) are unaffected; the plan-specific results are not currently citable.
- **[docs/LEARNINGS.md](docs/LEARNINGS.md)** - what building and auditing this harness actually taught, including the misdiagnoses

## Architecture

The system uses strict role separation with five specialized agents:

1. **Questioner** - Generates beneficiary questions from scenarios
2. **Extractor** - Converts AI responses into atomic, verifiable claims
3. **Verifier** - Judges claims against answer keys (multiple independent instances)
4. **Scorer** - Computes accuracy and completeness metrics
5. **Adjudicator** - Resolves disagreements between verifiers

## Quick Start

### 1. Install

```bash
pip install -e ".[openrouter]"
```

Other provider extras: `.[openai]`, `.[anthropic]`, `.[google]`, or `.[all]`.

### 2. Verify the install (no API key needed)

Both the target model and the grading model can be faked, so this runs entirely offline:

```bash
python -m src run --scenario scenarios/v1/scenario_001.json --target-model fake:perfect --grade-model fake:perfect
```

SHIP rubric grading runs on **every** evaluation and defaults to `anthropic:claude-3-5-sonnet-20241022`. If you omit `--grade-model`, this command fails without an Anthropic key even though the target model is fake.

### 3. Set up API keys

```bash
cp .env.example .env
echo "OPENROUTER_API_KEY=sk-or-your_key_here" >> .env
```

Get an OpenRouter API key at [openrouter.ai/keys](https://openrouter.ai/keys). Direct provider keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) also work.

### 4. Run a real evaluation

```bash
python -m src run --scenario scenarios/medicare_only/all_questions.json --target-model openrouter:openai/gpt-5.2 --grade-model openrouter:anthropic/claude-3.5-sonnet
```

### 5. View results

```bash
python -m src.view_run --run-dir runs/$(ls -t runs/ | head -1)
```

Rebuild the comparison report:

```bash
python scripts/generate_matrix_report.py --runs-dir runs --output reports/matrix_report.html
```

Re-derive the published headline figures independently:

```bash
python scripts/verify_headline_numbers.py
```

## Command reference

`python -m src run` accepts:

| Flag | Purpose | Default |
| --- | --- | --- |
| `--scenario` | `medicare_only`, `dual_eligible`, or a path to a scenario JSON | required |
| `--target-model` | The model being evaluated | required |
| `--grade-model` | Model used for SHIP rubric grading | `anthropic:claude-3-5-sonnet-20241022` |
| `--agent-model` | Model used for claim extraction and verification | `fake:perfect` |
| `--verify-claims` | Also extract and verify atomic claims against the answer key | off |
| `--judges` | Number of independent verifiers (only meaningful with `--verify-claims`) | 2 |
| `--seed` | Random seed | 42 |
| `--output-dir` | Where runs are written | `runs/` |
| `--run-id` | Custom run ID | timestamp |

Model specs are `provider:model`, for example `openrouter:openai/gpt-5.2`, `anthropic:claude-3-5-sonnet-20241022`, or `fake:perfect`.

Supported providers: OpenRouter (recommended, one key for many models), OpenAI, Anthropic, Google, xAI, and a `fake:` adapter for testing. See [docs/OPENROUTER_GUIDE.md](docs/OPENROUTER_GUIDE.md).

## Eval Dataset

The `eval_dataset/` directory contains a standalone, structured version of the SHIP question bank that can be used independently of the evaluation harness, for example to build your own grader, run manual evaluations, or compare AI outputs against the human baseline.

```
eval_dataset/
├── index.json                        # Manifest linking all files
├── scenarios/                        # Persona definitions and question sequences
│   ├── medicare_only_v1.json         # Turning-65, employer coverage persona
│   └── dual_eligible_v1.json         # Medicare + full Medicaid persona
├── question_groups/                  # One file per scored SHIP question (19 total)
│   ├── QG01_enrollment_timing.json
│   ├── QG09–QG20_*.json              # Medicare-Only questions
│   └── QG21–QG26_*.json              # Dual-Eligible questions
└── baselines/
    └── ship_2025_human_baseline.json # SHIP counselor accuracy rates (eTable 3)
```

Each question group file contains the exact question text from the SHIP study script, a four-tier scoring rubric (`accurate_complete`, `substantive_incomplete`, `not_substantive`, `incorrect`) derived from eAppendix 4, and the SHIP human baseline percentages for that question. Questions that require real-time plan lookup (network status, premiums, formulary) are flagged `external_validation_required: true`.

Start with `eval_dataset/index.json` for a full listing of files and per-question baseline rates.

## Project Structure

```
ai-medicare-eval/
├── eval_dataset/       # Standalone SHIP question bank (scenarios, rubrics, baselines)
├── scenarios/          # Test scenarios with answer keys
├── prompts/            # System prompts for each agent
├── src/
│   ├── adapters/       # LLM provider integrations
│   └── agents/         # Evaluation agents
├── scripts/            # Report generation and verification
├── reports/            # Generated HTML reports
├── docs/               # Documentation
├── reported_runs.json  # The exact run set behind published figures
└── runs/               # Evaluation results
```

## Key Design Principles

1. **Strict role separation** - Questioner is not Responder is not Judge
2. **Answer-key grounded** - Judges rely only on provided answer keys
3. **Deterministic by default** - Fixed seeds, prompts, and parameters
4. **Full auditability** - Raw transcripts and judge outputs stored verbatim
5. **Snapshot-based evaluation** - Results are time-, model-, and prompt-specific
6. **Append-only evidence** - A re-grade writes a new run and never edits an existing one

## SHIP Study Fidelity

Results are only comparable to the published human baseline if the study conditions are replicated exactly:

- Use the exact opening statement and question wording from the scenario files, do not paraphrase
- Do **not** add system prompts instructing the AI to act as a counselor
- Do **not** give the AI extra context beyond what the scenario provides
- Ask questions in the sequence the scenario specifies

The study measured how counselors performed for ordinary beneficiaries. Optimally prompting the AI would measure something else.

## Ethics and Framing

**This system is for research purposes only.**

This tool evaluates AI-generated information quality. It does not provide medical, legal, or insurance advice. Results should not be used to make healthcare decisions. The SHIP program provides free, expert Medicare counseling: find a local counselor at [shiphelp.org](https://www.shiphelp.org).

## Development

```bash
pip install -e ".[dev]"
pytest tests/
ruff check .
```

## Documentation

| Document | Purpose |
| --- | --- |
| [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) | How published numbers are derived and verified |
| [docs/LEARNINGS.md](docs/LEARNINGS.md) | High-level learnings from building and auditing this harness |
| [docs/GRADING_INTEGRITY.md](docs/GRADING_INTEGRITY.md) | Known answer-key defect and its blast radius |
| [docs/GRADER_SELECTION.md](docs/GRADER_SELECTION.md) | Grader model vs harness experiment: how often the grader fails |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | Step-by-step usage guide |
| [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) | Command reference card |
| [docs/SCENARIOS.md](docs/SCENARIOS.md) | What each test scenario evaluates |
| [docs/INTEGRATED_GRADING_GUIDE.md](docs/INTEGRATED_GRADING_GUIDE.md) | How grading works end to end |
| [docs/GRADING_SYSTEM_README.md](docs/GRADING_SYSTEM_README.md) | Rubric mapping internals |
| [docs/REPORTING_GUIDE.md](docs/REPORTING_GUIDE.md) | Generating SHIP-style accuracy tables |
| [docs/OPENROUTER_GUIDE.md](docs/OPENROUTER_GUIDE.md) | Accessing many models with one API key |
| [docs/METHODOLOGY_COMPARISON.md](docs/METHODOLOGY_COMPARISON.md) | This system versus the SHIP study |
| [docs/PLAN_INFORMATION_GUIDE.md](docs/PLAN_INFORMATION_GUIDE.md) | Plan-specific question handling |
| [docs/VIEW_RUNS_GUIDE.md](docs/VIEW_RUNS_GUIDE.md) | Inspecting stored run artifacts |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Publishing the reports |

## License

MIT

## References

Based on methodology from:

**Dugan K, et al.** "Accuracy of Medicare Information Provided by State Health Insurance Assistance Programs." *JAMA Network Open*. 2025;8(4):e252834.

- PubMed Central: [PMC11962663](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/)
- DOI: [10.1001/jamanetworkopen.2025.2834](https://doi.org/10.1001/jamanetworkopen.2025.2834)

This project re-implements the original study's methodology. The substantive research contribution is the original authors'.

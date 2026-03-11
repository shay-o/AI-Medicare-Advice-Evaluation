# AGENTS.md

## Cursor Cloud specific instructions

This is a Python 3.11+ CLI application (no web server, no Docker, no database). All state is stored as JSONL files in `runs/`.

### Running the application

The CLI entry point is `python3 -m src run`. Use `--help` for all flags. A full evaluation requires `--scenario`, `--target-model`, and optionally `--grade-model` and `--judges`.

**Without API keys** (always works): override both target and grading models with the fake adapter:
```
python3 -m src run --scenario scenarios/v1/scenario_001.json --target-model fake:perfect --grade-model fake:perfect --judges 2
```

The default `--grade-model` is `anthropic:claude-3-5-sonnet-20241022`, which requires `ANTHROPIC_API_KEY`. If no LLM API key is available, you **must** pass `--grade-model fake:perfect` to avoid a startup error.

### Lint / Test / Type-check

- **Lint:** `python3 -m ruff check .` (ruff is installed but not on PATH; invoke via `python3 -m ruff`)
- **Format:** `python3 -m black .`
- **Type-check:** `python3 -m mypy src/`
- **Tests:** `python3 -m pytest tests/` (8 pass; 3 pre-existing failures unrelated to environment)

### Reporting scripts

Generate accuracy tables from completed runs:
```
python3 scripts/generate_accuracy_table.py --include-fake --include-incomplete
```
See `REPORTING_GUIDE.md` for full options.

### Known caveats

- `test_basic.py` at the repo root has a pre-existing `ImportError` (`SHIPClassification` not in `src/schemas.py`). Use `pytest tests/` instead.
- The `ruff` and `black` binaries are installed under the user pip bin directory; always invoke as `python3 -m ruff` / `python3 -m black` to ensure they are found.

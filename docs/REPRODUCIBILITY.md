# Reproducibility: how the published numbers are derived

The published figures are **65.0% accurate & complete / 25.0% accurate but incomplete / 7.8% not substantive / 2.2% incorrect**, over n=180 graded answers: 9 models × 20 question instances, across 19 scored question groups and 2 scenarios.

Anyone can re-derive them from this repo:

```bash
python scripts/verify_headline_numbers.py
```

That script recomputes the aggregates straight from `runs/*/results.jsonl`, independently of the report generator, and exits non-zero if they drift from the published values.

To rebuild the report itself:

```bash
python scripts/generate_matrix_report.py --runs-dir runs --output reports/matrix_report.html
```

Requires Python 3.10+ (the codebase uses PEP 604 `X | None` annotations; the macOS system Python 3.9 will fail on import).

## Which runs count

**The reported set is defined by [`reported_runs.json`](../reported_runs.json), not by scanning `runs/`.**

The manifest names each of the 18 runs behind the published figures and records a SHA-256 of its `results.jsonl`. Both the report generator and the verification script read it, and both fail loudly if a listed run is missing or its contents have changed. This makes the published set an explicit, reviewable artifact: adding or dropping a run from the headline is a visible diff, not a side effect of a file appearing in a directory.

```bash
python scripts/run_manifest.py verify   # check runs/ still matches the manifest
python scripts/run_manifest.py build    # regenerate after adding a run (review the diff)
```

`generate_matrix_report.py --no-manifest` falls back to directory scanning for exploratory work. Its output is not the published set and must not be republished as such.

### Runs are append-only

Evaluation results are evidence. A re-grade writes a **new** run; it never edits an existing one. Old and new sit side by side and the manifest decides which is published, so a changed verdict is always traceable.

`scripts/check_runs_append_only.py` enforces this and is installed as a git pre-commit hook:

```bash
ln -sf ../../scripts/check_runs_append_only.py .git/hooks/pre-commit
```

It fails the commit if a tracked file under `runs/` is modified or deleted, and — because `runs/*/` is currently gitignored, so git cannot police it — also if any manifest hash no longer matches. Bypass with `git commit --no-verify` only when deliberately rewriting evidence.

### Selection rules behind the manifest

`runs/` holds more than the reported evaluation: partial runs, ad-hoc probes, and superseded attempts. Aggregating all of it produces materially different (and wrong) numbers — a naive pass over every `results.jsonl` yields ~47% accurate & complete rather than 65%. `run_manifest.py build` applies these rules when proposing the set:

1. **Top-level runs only.** Results are read from `runs/<run>/results.jsonl`. Archived runs under `runs/Back/<run>/` are not traversed. Pass `--include-back` to opt them in; this adds 37 archived runs and a 10th model, and is not what the published report uses.
2. **Complete-scenario runs only.** `scenario_id` must be `SHIP-MO-ALL` or `SHIP-DE-ALL`. This is what excludes the partial and single-question runs.
3. **Graded results only.** The result must carry `grading.question_scores`.
4. **No test doubles.** Models named `fake:*` are dropped.
5. **QG2 excluded.** The Spanish-translation question is not scored on the 4-point rubric in the SHIP study (it was recorded yes/no, and every counsellor answered yes), so it is excluded from rubric aggregates. This is declared in `reference_material/etable3_question_mapping.json` under `excluded_questions`. It is the difference between the 20 question groups present in the data and the 19 reported.
6. **Rubric labels only.** Rows scored `missing`, and rows whose question group is `Error`, represent ungraded or failed items and are excluded. Only `accurate_complete`, `substantive_incomplete`, `not_substantive`, and `incorrect` are counted.

Applying rules 1–4 gives 198 graded rows at 61.1% accurate & complete; rule 5 removes the 18 Spanish-translation rows and yields the published n=180 at 65.0%. Per-question figures match the published matrix exactly.

## Open gap: the run data is not in the repo

`.gitignore` excludes `runs/*/`, so the 18 runs behind the published figures are **not** in version control. Anyone cloning this repository cannot currently reproduce the numbers — `verify_headline_numbers.py` will fail for them, because the evidence it checks is only on the author's machine. The manifest records what *should* be there and would detect substitution, but it cannot supply the missing data.

The canonical `results.jsonl` files total **2.4 MB** across all 18 runs (4.9 MB including `transcripts/` and `intermediate/`), which is well within what a git repository can carry. Committing at least the `results.jsonl` files would make the reproducibility claim real rather than aspirational. Note the verbatim model responses they contain are already published in `reports/matrix_report.html`, so this discloses nothing new.

## Verified 2026-07-25

- `scripts/generate_matrix_report.py` regenerates `reports/matrix_report.html` byte-identically to the published version (ignoring the generation timestamp), from the current contents of `runs/`. There is no run-set drift between what is published and what is in the repo.
- `scripts/verify_headline_numbers.py` independently reproduces 65.0 / 25.0 / 7.8 / 2.2 at n=180, 19 question groups, 9 models.

## Known issue affecting a subset

Two of the nineteen question groups (QG19 drug coverage, QG20 Lipitor) were graded against an answer key hardcoded in the rubric that contradicts the real plan the question names. Correct answers were marked `incorrect` and at least one wrong answer was marked `accurate_complete`. The general-rules questions (12 groups, n=117) are unaffected.

This was fixed in code on 2026-08-17 and the stored responses are being re-graded. **The published figures on this page were produced by the old grading and still contain the defect.** See [GRADING_INTEGRITY.md](GRADING_INTEGRITY.md) before citing the plan-specific figures.

Note that an earlier version of that document attributed the defect to `plan_information` in the scenario file. That was wrong: the grader never receives `plan_information`. The corrected diagnosis is recorded there.

`verify_headline_numbers.py` reports the general-rules and plan-specific slices separately for this reason.

"""Explicit, hash-verified definition of which runs back the published figures.

Reporting used to be defined implicitly: "whatever is in runs/ that matches a
filter". That made the reported set an accident of directory contents -- a
stray test run could silently move the headline number, and a re-grade in place
could change a published result with no trace.

This module makes the reported set an explicit, reviewable artifact. The
manifest (reported_runs.json) names each run, records a SHA-256 of its
results.jsonl, and is checked in. Adding or removing a run from the published
figures is therefore a visible diff, and a modified run is detected rather than
silently absorbed.

Usage:
    python scripts/run_manifest.py build     # regenerate from runs/ (review the diff!)
    python scripts/run_manifest.py verify    # check runs/ still matches the manifest
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO_ROOT / "reported_runs.json"
DEFAULT_RUNS_DIR = REPO_ROOT / "runs"

ALLOWED_SCENARIOS = {"SHIP-MO-ALL", "SHIP-DE-ALL"}
EXCLUDED_GROUP_IDS = {"QG2"}
RUBRIC_LABELS = [
    "accurate_complete",
    "substantive_incomplete",
    "not_substantive",
    "incorrect",
]


class ManifestError(RuntimeError):
    """Raised when the manifest and the runs directory disagree."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_trials(results_path: Path):
    with open(results_path) as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def discover_canonical_runs(runs_dir: Path) -> list[dict[str, Any]]:
    """Find runs that qualify for the reported set, by the documented rules.

    Only used by `build`. Reporting itself reads the manifest, never this.
    """
    entries: list[dict[str, Any]] = []
    for results_path in sorted(runs_dir.glob("*/results.jsonl")):
        trials = []
        for trial in _iter_trials(results_path):
            model = (trial.get("target") or {}).get("model_name", "")
            grading = trial.get("grading") or {}
            if trial.get("scenario_id") not in ALLOWED_SCENARIOS:
                continue
            if not grading.get("question_scores"):
                continue
            if not model or model.startswith("fake:"):
                continue
            trials.append(
                {
                    "trial_id": trial.get("trial_id"),
                    "scenario_id": trial.get("scenario_id"),
                    "model": model,
                    "graded_questions": len(grading["question_scores"]),
                }
            )
        if trials:
            entries.append(
                {
                    "run_dir": results_path.parent.name,
                    "results_sha256": sha256_file(results_path),
                    "trials": trials,
                }
            )
    return entries


def load_manifest(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    if not manifest_path.exists():
        raise ManifestError(
            f"Manifest not found: {manifest_path}\n"
            "The reported run set is defined by this file. Regenerate it with:\n"
            "    python scripts/run_manifest.py build"
        )
    with open(manifest_path) as handle:
        return json.load(handle)


def verify_manifest(
    manifest: dict[str, Any],
    runs_dir: Path = DEFAULT_RUNS_DIR,
) -> list[str]:
    """Return a list of problems; empty means runs/ matches the manifest."""
    problems: list[str] = []
    for entry in manifest.get("runs", []):
        run_dir = entry["run_dir"]
        results_path = runs_dir / run_dir / "results.jsonl"
        if not results_path.exists():
            problems.append(f"MISSING: {run_dir}/results.jsonl is listed in the manifest but absent")
            continue
        actual = sha256_file(results_path)
        if actual != entry["results_sha256"]:
            problems.append(
                f"CHANGED: {run_dir}/results.jsonl content differs from the manifest\n"
                f"           manifest: {entry['results_sha256']}\n"
                f"           on disk:  {actual}\n"
                "           Runs are append-only. Re-grading writes a NEW run; it does not\n"
                "           edit an existing one. If this change is intended, add the new run\n"
                "           and rebuild the manifest."
            )
    return problems


def load_reported_trials(
    manifest_path: Path = DEFAULT_MANIFEST,
    runs_dir: Path = DEFAULT_RUNS_DIR,
    strict: bool = True,
) -> list[dict[str, Any]]:
    """Load exactly the trial records named by the manifest.

    With strict=True (the default) any hash mismatch or missing run is fatal.
    """
    manifest = load_manifest(manifest_path)
    problems = verify_manifest(manifest, runs_dir)
    if problems and strict:
        raise ManifestError(
            "Runs directory does not match the manifest:\n  "
            + "\n  ".join(problems)
        )

    wanted: dict[str, set[str]] = {}
    for entry in manifest.get("runs", []):
        wanted[entry["run_dir"]] = {t["trial_id"] for t in entry["trials"]}

    trials: list[dict[str, Any]] = []
    for run_dir, trial_ids in wanted.items():
        results_path = runs_dir / run_dir / "results.jsonl"
        if not results_path.exists():
            continue
        for trial in _iter_trials(results_path):
            if trial.get("trial_id") in trial_ids:
                trials.append(trial)
    return trials


def _expected_totals(trials: list[dict[str, Any]]) -> dict[str, Any]:
    from collections import Counter

    counts: Counter[str] = Counter()
    groups: set[str] = set()
    models: set[str] = set()
    for trial in trials:
        models.add((trial.get("target") or {}).get("model_name", ""))
        for question in (trial.get("grading") or {}).get("question_scores") or []:
            if question.get("group_id") in EXCLUDED_GROUP_IDS:
                continue
            if question.get("score") not in RUBRIC_LABELS:
                continue
            groups.add(question.get("group_id"))
            counts[question["score"]] += 1
    total = sum(counts.values())
    return {
        "graded_answers": total,
        "question_groups": len(groups),
        "models": len(models),
        "pct": {
            label: round(100 * counts[label] / total, 1) if total else 0.0
            for label in RUBRIC_LABELS
        },
    }


def build(manifest_path: Path, runs_dir: Path) -> int:
    entries = discover_canonical_runs(runs_dir)
    if not entries:
        print("No qualifying runs found.", file=sys.stderr)
        return 1

    trials = []
    for entry in entries:
        ids = {t["trial_id"] for t in entry["trials"]}
        for trial in _iter_trials(runs_dir / entry["run_dir"] / "results.jsonl"):
            if trial.get("trial_id") in ids:
                trials.append(trial)

    manifest = {
        "version": 1,
        "description": (
            "The exact set of evaluation runs behind the published figures. "
            "Reporting reads this file rather than globbing runs/, so the reported "
            "set is explicit and reviewable. Hashes make edits to existing runs "
            "detectable. See docs/REPRODUCIBILITY.md."
        ),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "selection_rules": {
            "allowed_scenario_ids": sorted(ALLOWED_SCENARIOS),
            "excluded_group_ids": sorted(EXCLUDED_GROUP_IDS),
            "rubric_labels": RUBRIC_LABELS,
            "notes": "QG2 (Spanish translation) is excluded: scored yes/no in the SHIP study, not on the 4-point rubric.",
        },
        "expected_totals": _expected_totals(trials),
        "runs": entries,
    }

    with open(manifest_path, "w") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    totals = manifest["expected_totals"]
    print(f"Wrote {manifest_path.relative_to(REPO_ROOT)}")
    print(f"  runs: {len(entries)}   models: {totals['models']}   question groups: {totals['question_groups']}")
    print(f"  graded answers: {totals['graded_answers']}")
    print(f"  distribution: {totals['pct']}")
    print("\n  Review the diff before committing -- this file defines your published numbers.")
    return 0


def verify(manifest_path: Path, runs_dir: Path) -> int:
    manifest = load_manifest(manifest_path)
    problems = verify_manifest(manifest, runs_dir)
    if problems:
        print("Manifest verification FAILED:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    totals = manifest.get("expected_totals", {})
    print(f"Manifest OK: {len(manifest.get('runs', []))} runs, all hashes match.")
    if totals:
        print(f"  expected: n={totals.get('graded_answers')} "
              f"groups={totals.get('question_groups')} models={totals.get('models')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["build", "verify"])
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    args = parser.parse_args()

    if args.command == "build":
        return build(args.manifest, args.runs_dir)
    return verify(args.manifest, args.runs_dir)


if __name__ == "__main__":
    raise SystemExit(main())

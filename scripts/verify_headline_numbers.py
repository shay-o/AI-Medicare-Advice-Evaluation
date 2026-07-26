#!/usr/bin/env python3
"""Recompute the published headline numbers directly from runs/.

This is an independent check on generate_matrix_report.py: it re-derives the
aggregate figures from the raw results.jsonl files using the same inclusion
rules, so a third party can confirm the reported numbers without reading the
report generator.

Usage:
    python scripts/verify_headline_numbers.py
    python scripts/verify_headline_numbers.py --runs-dir runs --json

Which runs count is defined by reported_runs.json, not by scanning runs/. The
manifest is hash-verified, so an edited or missing run is a hard failure rather
than a silent change in the numbers. See docs/REPRODUCIBILITY.md.

Within those runs, two exclusions apply:
  - Question group QG2 (Spanish translation): scored yes/no in the SHIP study,
    not on the 4-point rubric. See reference_material/etable3_question_mapping.json.
  - Rows scored "missing" or belonging to an "Error" group: ungraded.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_manifest import (  # noqa: E402
    DEFAULT_MANIFEST,
    DEFAULT_RUNS_DIR,
    EXCLUDED_GROUP_IDS,
    RUBRIC_LABELS,
    ManifestError,
    load_reported_trials,
)

# Question groups whose answer key depends on attributes of a specific named
# plan (scenarios/*/all_questions.json -> plan_information) rather than on
# general Medicare rules. Reported separately: see docs/GRADING_INTEGRITY.md.
PLAN_SPECIFIC_MARKERS = (
    "in Network for Spe",
    "Premium for Specific Plan",
    "Allows Out-of-Networ",
    "in-network PCP copay",
    "maximum out-of-pocket",
    "includes coverage fo",
    "covers specific drug",
)

# Published figures, for regression checking.
EXPECTED = {
    "n": 180,
    "questions": 19,
    "models": 9,
    "accurate_complete": 65.0,
    "substantive_incomplete": 25.0,
    "not_substantive": 7.8,
    "incorrect": 2.2,
}


def is_plan_specific(group_name: str) -> bool:
    return any(marker in group_name for marker in PLAN_SPECIFIC_MARKERS)


def collect(manifest_path: Path, runs_dir: Path) -> list[dict]:
    """Load the manifest-defined runs and flatten them to graded rows."""
    trials = load_reported_trials(manifest_path=manifest_path, runs_dir=runs_dir, strict=True)

    rows: list[dict] = []
    for trial in trials:
        model = (trial.get("target") or {}).get("model_name", "")
        for question in (trial.get("grading") or {}).get("question_scores") or []:
            score = question.get("score")
            group_id = question.get("group_id")
            if score not in RUBRIC_LABELS:
                continue
            if group_id in EXCLUDED_GROUP_IDS:
                continue
            group_name = question.get("group_name") or ""
            rows.append(
                {
                    "model": model,
                    "group_id": group_id,
                    "group_name": group_name,
                    "score": score,
                    "plan_specific": is_plan_specific(group_name),
                }
            )
    return rows


def summarize(rows: list[dict]) -> dict:
    counts = Counter(r["score"] for r in rows)
    total = len(rows)
    return {
        "n": total,
        "counts": {label: counts[label] for label in RUBRIC_LABELS},
        "pct": {
            label: round(100 * counts[label] / total, 1) if total else 0.0
            for label in RUBRIC_LABELS
        },
    }


def print_block(title: str, summary: dict) -> None:
    print(f"  {title:34s} n={summary['n']:<4}", end="")
    for label in RUBRIC_LABELS:
        print(f"  {label.split('_')[0][:4].upper()}={summary['pct'][label]:5.1f}%", end="")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    if not args.runs_dir.is_dir():
        print(f"Error: runs dir not found: {args.runs_dir}", file=sys.stderr)
        return 1

    try:
        rows = collect(args.manifest, args.runs_dir)
    except ManifestError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not rows:
        print("Error: no graded rows found", file=sys.stderr)
        return 1

    overall = summarize(rows)
    general = summarize([r for r in rows if not r["plan_specific"]])
    plan = summarize([r for r in rows if r["plan_specific"]])

    models = sorted({r["model"] for r in rows})
    groups = sorted({r["group_id"] for r in rows if r["group_id"]})

    if args.json:
        print(json.dumps({
            "overall": overall,
            "general_rules": general,
            "plan_specific": plan,
            "models": models,
            "question_groups": len(groups),
        }, indent=2))
        return 0

    print("AI Medicare Advice Evaluator — headline verification")
    print(f"  runs dir: {args.runs_dir}   models: {len(models)}   question groups: {len(groups)}")
    print()
    print_block("ALL questions (published)", overall)
    print_block("General-rules questions", general)
    print_block("Plan-specific questions", plan)
    print()

    # Regression check against the published figures.
    problems = []
    if overall["n"] != EXPECTED["n"]:
        problems.append(f"n={overall['n']} expected {EXPECTED['n']}")
    if len(groups) != EXPECTED["questions"]:
        problems.append(f"questions={len(groups)} expected {EXPECTED['questions']}")
    if len(models) != EXPECTED["models"]:
        problems.append(f"models={len(models)} expected {EXPECTED['models']}")
    for label in RUBRIC_LABELS:
        if abs(overall["pct"][label] - EXPECTED[label]) > 0.05:
            problems.append(f"{label}={overall['pct'][label]} expected {EXPECTED[label]}")

    if problems:
        print("  MISMATCH vs published figures:")
        for problem in problems:
            print(f"    - {problem}")
        return 1

    print("  OK — matches the published figures (65.0 / 25.0 / 7.8 / 2.2, n=180, 19 questions, 9 models).")
    print()
    print("  NOTE: the plan-specific block above is affected by a known answer-key")
    print("  defect. See docs/GRADING_INTEGRITY.md before citing those figures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

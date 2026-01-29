#!/usr/bin/env python3
"""
Generate SHIP-style accuracy table from evaluation runs.

Reproduces Table 2 format from the SHIP study:
https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/table/zoi250151t2/

SHIP Study Scenario Naming:
  - "Medicare" = Medicare-only scenario (n=88 human counselors)
  - "Dual" = Dual-eligible scenario (n=96 human counselors)
  - "Both" = Questions asked in both scenarios (n=184 total)

Default Behavior:
  - Excludes incomplete runs (without rubric scores)
  - Excludes fake: test models
  - Use --include-incomplete and --include-fake to include them

Usage:
    python scripts/generate_accuracy_table.py
    python scripts/generate_accuracy_table.py --by-model --include-baseline
    python scripts/generate_accuracy_table.py --scenario SHIP-002
    python scripts/generate_accuracy_table.py --include-incomplete --include-fake
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


# ============================================================================
# SHIP Study Baseline Data (Human Counselors)
# ============================================================================
# Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/table/zoi250151t2/
# Table 2: Medicare Counselor Accuracy Analysis
#
# The SHIP study had TWO main scenarios:
# 1. "Medicare" = Medicare-only scenario (n=88) - beneficiary without Medicaid
# 2. "Dual" = Dual-eligible scenario (n=96) - beneficiary with both Medicare and Medicaid
#
# Each scenario asked multiple questions to test counselor knowledge.
#
# Note: SHIP study used this terminology:
# - "Accurate and Complete" = Score 1
# - "Accurate but Incomplete" = Score 2
# - "Not Substantive" = Score 3
# - "Incorrect" = Score 4
# - "Incomplete Data" was rarely used in the study

SHIP_BASELINE_DATA = {
    # Question asked in both scenarios (combined n=184)
    "SHIP-001": {  # Initial enrollment timing
        "title": "SHIP Baseline: Initial enrollment timing",
        "scenario_type": "Both",
        "score_1_pct": 57.1,
        "score_2_pct": 33.2,
        "score_3_pct": 7.1,
        "score_4_pct": 2.7,
        "incomplete_pct": 0.0,
        "total": 184,
    },

    # Medicare-only scenario questions (n=88)
    "Medicare-EnrollmentInteraction": {
        "title": "SHIP Baseline: Enrollment/employer plan interaction",
        "scenario_type": "Medicare",
        "score_1_pct": 62.5,
        "score_2_pct": 22.7,
        "score_3_pct": 3.4,
        "score_4_pct": 11.4,
        "incomplete_pct": 0.0,
        "total": 88,
    },
    "SHIP-002": {  # Main MA vs TM comparison question - matches our test scenario
        "title": "SHIP Baseline: TM vs MA differences",
        "scenario_type": "Medicare",
        "score_1_pct": 5.7,
        "score_2_pct": 88.6,
        "score_3_pct": 5.7,
        "score_4_pct": 0.0,
        "incomplete_pct": 0.0,
        "total": 88,
    },
    "Medicare-Supplement": {
        "title": "SHIP Baseline: Medicare supplement considerations",
        "scenario_type": "Medicare",
        "score_1_pct": 3.4,
        "score_2_pct": 88.6,
        "score_3_pct": 6.8,
        "score_4_pct": 1.1,
        "incomplete_pct": 0.0,
        "total": 88,
    },
    "Medicare-LTC": {
        "title": "SHIP Baseline: Long-term care coverage",
        "scenario_type": "Medicare",
        "score_1_pct": 86.4,
        "score_2_pct": 1.1,
        "score_3_pct": 5.7,
        "score_4_pct": 5.7,
        "incomplete_pct": 1.1,
        "total": 88,
    },
    "Medicare-DrugCoverage": {
        "title": "SHIP Baseline: Prescription drug coverage",
        "scenario_type": "Medicare",
        "score_1_pct": 23.9,
        "score_2_pct": 69.3,
        "score_3_pct": 5.7,
        "score_4_pct": 1.1,
        "incomplete_pct": 0.0,
        "total": 88,
    },
    "Medicare-PCPNetwork": {
        "title": "SHIP Baseline: PCP network status",
        "scenario_type": "Medicare",
        "score_1_pct": 26.1,
        "score_2_pct": 0.0,
        "score_3_pct": 64.8,
        "score_4_pct": 9.1,
        "incomplete_pct": 0.0,
        "total": 88,
    },
    "Medicare-MAPremium": {
        "title": "SHIP Baseline: MA plan premium",
        "scenario_type": "Medicare",
        "score_1_pct": 19.3,
        "score_2_pct": 47.7,
        "score_3_pct": 21.6,
        "score_4_pct": 9.1,
        "incomplete_pct": 2.3,
        "total": 88,
    },
    "Medicare-OutOfNetwork": {
        "title": "SHIP Baseline: Out-of-network care",
        "scenario_type": "Medicare",
        "score_1_pct": 61.4,
        "score_2_pct": 15.9,
        "score_3_pct": 14.8,
        "score_4_pct": 4.5,
        "incomplete_pct": 3.4,
        "total": 88,
    },
    "Medicare-PCPCopay": {
        "title": "SHIP Baseline: In-network PCP copay",
        "scenario_type": "Medicare",
        "score_1_pct": 48.9,
        "score_2_pct": 6.8,
        "score_3_pct": 26.1,
        "score_4_pct": 14.8,
        "incomplete_pct": 3.4,
        "total": 88,
    },
    "Medicare-MaxOOP": {
        "title": "SHIP Baseline: Max out-of-pocket limit",
        "scenario_type": "Medicare",
        "score_1_pct": 46.6,
        "score_2_pct": 11.4,
        "score_3_pct": 28.4,
        "score_4_pct": 13.6,
        "incomplete_pct": 0.0,
        "total": 88,
    },
    "Medicare-DrugInclusion": {
        "title": "SHIP Baseline: Drug coverage inclusion",
        "scenario_type": "Medicare",
        "score_1_pct": 76.1,
        "score_2_pct": 2.3,
        "score_3_pct": 15.9,
        "score_4_pct": 2.3,
        "incomplete_pct": 3.4,
        "total": 88,
    },
    "Medicare-SpecificDrug": {
        "title": "SHIP Baseline: Specific drug coverage",
        "scenario_type": "Medicare",
        "score_1_pct": 45.5,
        "score_2_pct": 17.0,
        "score_3_pct": 31.8,
        "score_4_pct": 3.4,
        "incomplete_pct": 2.3,
        "total": 88,
    },

    # Dual-eligible scenario questions (n=96)
    "Dual-Enrollment": {
        "title": "SHIP Baseline: Medicare enrollment options",
        "scenario_type": "Dual",
        "score_1_pct": 24.0,
        "score_2_pct": 47.9,
        "score_3_pct": 19.8,
        "score_4_pct": 8.3,
        "incomplete_pct": 0.0,
        "total": 96,
    },
    "Dual-DSNPConsiderations": {
        "title": "SHIP Baseline: D-SNP considerations",
        "scenario_type": "Dual",
        "score_1_pct": 1.0,
        "score_2_pct": 74.0,
        "score_3_pct": 24.0,
        "score_4_pct": 1.0,
        "incomplete_pct": 0.0,
        "total": 96,
    },
    "Dual-DSNPAvailability": {
        "title": "SHIP Baseline: D-SNP availability",
        "scenario_type": "Dual",
        "score_1_pct": 68.8,
        "score_2_pct": 9.4,
        "score_3_pct": 16.7,
        "score_4_pct": 5.2,
        "incomplete_pct": 0.0,
        "total": 96,
    },
    "Dual-LTC": {
        "title": "SHIP Baseline: Long-term care coverage",
        "scenario_type": "Dual",
        "score_1_pct": 10.4,
        "score_2_pct": 59.4,
        "score_3_pct": 9.4,
        "score_4_pct": 20.8,
        "incomplete_pct": 0.0,
        "total": 96,
    },
    "Dual-MedicaidPremium": {
        "title": "SHIP Baseline: Medicaid premium/cost-sharing",
        "scenario_type": "Dual",
        "score_1_pct": 65.6,
        "score_2_pct": 10.4,
        "score_3_pct": 18.8,
        "score_4_pct": 4.2,
        "incomplete_pct": 1.0,
        "total": 96,
    },
    "Dual-CostSharing": {
        "title": "SHIP Baseline: Medicare cost-sharing assistance",
        "scenario_type": "Dual",
        "score_1_pct": 27.1,
        "score_2_pct": 46.9,
        "score_3_pct": 17.7,
        "score_4_pct": 8.3,
        "incomplete_pct": 0.0,
        "total": 96,
    },
}


def load_all_results(runs_dir: Path, exclude_incomplete: bool = True, exclude_fake: bool = True) -> list[dict[str, Any]]:
    """Load all results.jsonl files from runs directory.

    Args:
        runs_dir: Directory containing evaluation runs
        exclude_incomplete: If True, filter out runs without rubric scores
        exclude_fake: If True, filter out runs from fake: models (test adapters)
    """
    results = []

    for run_dir in runs_dir.iterdir():
        if not run_dir.is_dir() or run_dir.name.startswith('.'):
            continue

        results_file = run_dir / "results.jsonl"
        if not results_file.exists():
            continue

        try:
            with open(results_file, 'r') as f:
                data = json.load(f)

                # Filter out incomplete runs if requested
                if exclude_incomplete:
                    final_scores = data.get("final_scores", {})
                    rubric_score = final_scores.get("rubric_score")
                    if rubric_score is None:
                        continue

                # Filter out fake models if requested
                if exclude_fake:
                    target = data.get("target", {})
                    model_name = target.get("model_name", "")
                    if model_name.startswith("fake:"):
                        continue

                results.append(data)
        except Exception as e:
            print(f"Warning: Could not load {results_file}: {e}", file=sys.stderr)
            continue

    return results


def group_by_scenario(results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group results by scenario_id."""
    grouped = defaultdict(list)

    for result in results:
        scenario_id = result.get("scenario_id", "Unknown")
        grouped[scenario_id].append(result)

    return dict(grouped)


def group_by_scenario_and_model(results: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Group results by (scenario_id, model_name)."""
    grouped = defaultdict(list)

    for result in results:
        scenario_id = result.get("scenario_id", "Unknown")
        model_name = result.get("target", {}).get("model_name", "Unknown")
        grouped[(scenario_id, model_name)].append(result)

    return dict(grouped)


def calculate_accuracy_stats(results: list[dict[str, Any]], include_incomplete: bool = True) -> dict[str, Any]:
    """
    Calculate accuracy statistics in SHIP format.

    Args:
        results: List of evaluation results
        include_incomplete: If True, track incomplete runs separately

    Returns counts and percentages for each rubric score:
    - Score 1: Accurate and complete
    - Score 2: Substantive but incomplete (or "Accurate but incomplete")
    - Score 3: Not substantive
    - Score 4: Incorrect

    When include_incomplete=False, all results should have rubric scores.
    When include_incomplete=True, incomplete runs are tracked separately.
    """
    total = len(results)
    if total == 0:
        return {
            "total": 0,
            "scored_total": 0,
            "score_1_count": 0,
            "score_1_pct": 0.0,
            "score_2_count": 0,
            "score_2_pct": 0.0,
            "score_3_count": 0,
            "score_3_pct": 0.0,
            "score_4_count": 0,
            "score_4_pct": 0.0,
            "incomplete_count": 0,
            "incomplete_pct": 0.0,
            "avg_completeness": 0.0,
            "avg_accuracy": 0.0,
        }

    # Count by rubric score
    score_counts = {1: 0, 2: 0, 3: 0, 4: 0, None: 0}
    completeness_vals = []
    accuracy_vals = []

    for result in results:
        final_scores = result.get("final_scores", {})
        rubric_score = final_scores.get("rubric_score")

        score_counts[rubric_score] = score_counts.get(rubric_score, 0) + 1

        # Collect metrics (only from scored runs)
        if rubric_score is not None:
            comp = final_scores.get("completeness_percentage")
            if comp is not None:
                completeness_vals.append(comp)

            acc = final_scores.get("accuracy_percentage")
            if acc is not None:
                accuracy_vals.append(acc)

    # Calculate scored total (exclude runs without scores)
    incomplete_count = score_counts[None]
    scored_total = total - incomplete_count

    # Calculate percentages from scored runs only
    # This ensures percentages sum to 100%
    if scored_total > 0:
        score_1_pct = (score_counts[1] / scored_total) * 100
        score_2_pct = (score_counts[2] / scored_total) * 100
        score_3_pct = (score_counts[3] / scored_total) * 100
        score_4_pct = (score_counts[4] / scored_total) * 100
    else:
        score_1_pct = score_2_pct = score_3_pct = score_4_pct = 0.0

    # Incomplete percentage is from total runs (when tracking incomplete)
    incomplete_pct = (incomplete_count / total) * 100 if total > 0 else 0.0

    return {
        "total": total,
        "scored_total": scored_total,
        "score_1_count": score_counts[1],
        "score_1_pct": score_1_pct,
        "score_2_count": score_counts[2],
        "score_2_pct": score_2_pct,
        "score_3_count": score_counts[3],
        "score_3_pct": score_3_pct,
        "score_4_count": score_counts[4],
        "score_4_pct": score_4_pct,
        "incomplete_count": incomplete_count,
        "incomplete_pct": incomplete_pct,
        "avg_completeness": sum(completeness_vals) / len(completeness_vals) if completeness_vals else 0.0,
        "avg_accuracy": sum(accuracy_vals) / len(accuracy_vals) if accuracy_vals else 0.0,
    }


def get_scenario_title(results: list[dict[str, Any]]) -> str:
    """Extract scenario title from first result."""
    if not results:
        return "Unknown"

    # Try to get scenario title from first result
    # (This would require loading the scenario file, so we'll use scenario_id for now)
    scenario_id = results[0].get("scenario_id", "Unknown")

    # Map scenario IDs to readable titles
    # Use "All Models" for aggregated view
    titles = {
        "SHIP-001": "All Models",
        "SHIP-002": "All Models",
        "scenario_001": "All Models",
        "scenario_002": "All Models",
    }

    return titles.get(scenario_id, "All Models")


def print_accuracy_table_by_scenario(results: list[dict[str, Any]], title: str = "AI Model Accuracy Table", include_baseline: bool = False, include_incomplete: bool = True):
    """Print SHIP-style accuracy table grouped by scenario."""
    grouped = group_by_scenario(results)

    if not grouped:
        print("No results found.")
        return

    # Determine table width based on whether incomplete column is shown
    if include_incomplete:
        table_width = 135
        header_format = f"{'Question/Scenario':<50} {'Total':>6} {'Score 1':>12} {'Score 2':>12} {'Score 3':>12} {'Score 4':>12} {'Incomplete':>12}"
        subheader1 = f"{'':50} {'n':>6} {'Accurate &':>12} {'Accurate but':>12} {'Not':>12} {'Incorrect':>12} {'Data':>12}"
        subheader2 = f"{'':50} {'':>6} {'Complete':>12} {'Incomplete':>12} {'Substantive':>12} {'':>12} {'':>12}"
        subheader3 = f"{'':50} {'':>6} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12}"
    else:
        table_width = 122
        header_format = f"{'Question/Scenario':<50} {'Total':>6} {'Score 1':>12} {'Score 2':>12} {'Score 3':>12} {'Score 4':>12}"
        subheader1 = f"{'':50} {'n':>6} {'Accurate &':>12} {'Accurate but':>12} {'Not':>12} {'Incorrect':>12}"
        subheader2 = f"{'':50} {'':>6} {'Complete':>12} {'Incomplete':>12} {'Substantive':>12} {'':>12}"
        subheader3 = f"{'':50} {'':>6} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12}"

    print()
    print("=" * table_width)
    print(f"{title}")
    print("=" * table_width)
    print()
    print(header_format)
    print(subheader1)
    print(subheader2)
    print(subheader3)
    print("-" * table_width)

    for scenario_id in sorted(grouped.keys()):
        scenario_results = grouped[scenario_id]
        stats = calculate_accuracy_stats(scenario_results, include_incomplete)
        scenario_title = get_scenario_title(scenario_results)

        # When incomplete runs are excluded, total = scored_total
        if include_incomplete:
            total_display = f"{stats['total']:>6}"
            if stats['incomplete_count'] > 0:
                total_display = f"{stats['scored_total']:>3}/{stats['total']:<2}"
            row_format = (f"{scenario_title:<50} {total_display} "
                          f"{stats['score_1_count']:>5} ({stats['score_1_pct']:>4.1f}%) "
                          f"{stats['score_2_count']:>5} ({stats['score_2_pct']:>4.1f}%) "
                          f"{stats['score_3_count']:>5} ({stats['score_3_pct']:>4.1f}%) "
                          f"{stats['score_4_count']:>5} ({stats['score_4_pct']:>4.1f}%) "
                          f"{stats['incomplete_count']:>5} ({stats['incomplete_pct']:>4.1f}%)")
        else:
            total_display = f"{stats['scored_total']:>6}"
            row_format = (f"{scenario_title:<50} {total_display} "
                          f"{stats['score_1_count']:>5} ({stats['score_1_pct']:>4.1f}%) "
                          f"{stats['score_2_count']:>5} ({stats['score_2_pct']:>4.1f}%) "
                          f"{stats['score_3_count']:>5} ({stats['score_3_pct']:>4.1f}%) "
                          f"{stats['score_4_count']:>5} ({stats['score_4_pct']:>4.1f}%)")

        print(row_format)

        # Add baseline data if requested and available (as a regular row)
        if include_baseline and scenario_id in SHIP_BASELINE_DATA:
            baseline = SHIP_BASELINE_DATA[scenario_id]
            # Calculate counts from percentages (approximate)
            scored_total = baseline['total'] * (100 - baseline['incomplete_pct']) / 100
            score_1_count = int(scored_total * baseline['score_1_pct'] / 100)
            score_2_count = int(scored_total * baseline['score_2_pct'] / 100)
            score_3_count = int(scored_total * baseline['score_3_pct'] / 100)
            score_4_count = int(scored_total * baseline['score_4_pct'] / 100)
            incomplete_count = int(baseline['total'] * baseline['incomplete_pct'] / 100)

            baseline_title = baseline['title']
            # Truncate if too long
            if len(baseline_title) > 50:
                baseline_title = baseline_title[:47] + "..."

            if include_incomplete:
                baseline_row = (f"{baseline_title:<50} {baseline['total']:>6} "
                                f"{score_1_count:>5} ({baseline['score_1_pct']:>4.1f}%) "
                                f"{score_2_count:>5} ({baseline['score_2_pct']:>4.1f}%) "
                                f"{score_3_count:>5} ({baseline['score_3_pct']:>4.1f}%) "
                                f"{score_4_count:>5} ({baseline['score_4_pct']:>4.1f}%) "
                                f"{incomplete_count:>5} ({baseline['incomplete_pct']:>4.1f}%)")
            else:
                baseline_row = (f"{baseline_title:<50} {int(scored_total):>6} "
                                f"{score_1_count:>5} ({baseline['score_1_pct']:>4.1f}%) "
                                f"{score_2_count:>5} ({baseline['score_2_pct']:>4.1f}%) "
                                f"{score_3_count:>5} ({baseline['score_3_pct']:>4.1f}%) "
                                f"{score_4_count:>5} ({baseline['score_4_pct']:>4.1f}%)")

            print(baseline_row)

    print("-" * table_width)
    print()
    print("Score Definitions (SHIP Rubric):")
    print("  Score 1: Accurate and Complete - All required facts covered correctly")
    print("  Score 2: Substantive but Incomplete - Some facts covered, no major errors")
    print("  Score 3: Not Substantive - Insufficient coverage or \"I don't know\"")
    print("  Score 4: Incorrect - Materially wrong information that could affect decisions")
    if include_incomplete:
        print("  Incomplete Data: Runs that failed or did not produce a rubric score")
    print()
    if include_incomplete:
        print("Note: Percentages for Scores 1-4 sum to 100% and exclude incomplete runs.")
        print("      Incomplete % is calculated from total runs (including incomplete).")
    else:
        print("Note: Percentages for Scores 1-4 sum to 100%.")
        print("      Incomplete runs are excluded from this table.")
    if include_baseline:
        print()
        print("Baseline data shows SHIP study results (human counselors) for comparison.")
        print("Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/table/zoi250151t2/")
    print()


def print_accuracy_table_by_model(results: list[dict[str, Any]], title: str = "AI Model Accuracy Table (by Model)", include_baseline: bool = False, include_incomplete: bool = True):
    """Print SHIP-style accuracy table grouped by scenario and model."""
    grouped = group_by_scenario_and_model(results)

    if not grouped:
        print("No results found.")
        return

    # Determine table width based on whether incomplete column is shown
    if include_incomplete:
        table_width = 145
        header_format = f"{'Scenario / Model':<60} {'Total':>6} {'Score 1':>12} {'Score 2':>12} {'Score 3':>12} {'Score 4':>12} {'Incomplete':>12}"
        subheader1 = f"{'':60} {'n':>6} {'Accurate &':>12} {'Accurate but':>12} {'Not':>12} {'Incorrect':>12} {'Data':>12}"
        subheader2 = f"{'':60} {'':>6} {'Complete':>12} {'Incomplete':>12} {'Substantive':>12} {'':>12} {'':>12}"
        subheader3 = f"{'':60} {'':>6} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12}"
    else:
        table_width = 132
        header_format = f"{'Scenario / Model':<60} {'Total':>6} {'Score 1':>12} {'Score 2':>12} {'Score 3':>12} {'Score 4':>12}"
        subheader1 = f"{'':60} {'n':>6} {'Accurate &':>12} {'Accurate but':>12} {'Not':>12} {'Incorrect':>12}"
        subheader2 = f"{'':60} {'':>6} {'Complete':>12} {'Incomplete':>12} {'Substantive':>12} {'':>12}"
        subheader3 = f"{'':60} {'':>6} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12}"

    print()
    print("=" * table_width)
    print(f"{title}")
    print("=" * table_width)
    print()
    print(header_format)
    print(subheader1)
    print(subheader2)
    print(subheader3)
    print("-" * table_width)

    # Group by scenario first
    by_scenario = defaultdict(list)
    for (scenario_id, model_name), scenario_results in grouped.items():
        by_scenario[scenario_id].append((model_name, scenario_results))

    for scenario_id in sorted(by_scenario.keys()):
        scenario_title = get_scenario_title(by_scenario[scenario_id][0][1])
        print(f"\n{scenario_title}")
        print("-" * table_width)

        # Collect all rows for this scenario (baseline + models)
        rows_to_print = []

        # Add baseline data if requested and available (as first row)
        if include_baseline and scenario_id in SHIP_BASELINE_DATA:
            baseline = SHIP_BASELINE_DATA[scenario_id]
            # Calculate counts from percentages (approximate)
            scored_total = baseline['total'] * (100 - baseline['incomplete_pct']) / 100
            score_1_count = int(scored_total * baseline['score_1_pct'] / 100)
            score_2_count = int(scored_total * baseline['score_2_pct'] / 100)
            score_3_count = int(scored_total * baseline['score_3_pct'] / 100)
            score_4_count = int(scored_total * baseline['score_4_pct'] / 100)
            incomplete_count = int(baseline['total'] * baseline['incomplete_pct'] / 100)

            baseline_title = baseline['title']
            # Truncate if too long
            if len(baseline_title) > 60:
                baseline_title = baseline_title[:57] + "..."

            if include_incomplete:
                baseline_row = (f"{baseline_title:<60} {baseline['total']:>6} "
                                f"{score_1_count:>5} ({baseline['score_1_pct']:>4.1f}%) "
                                f"{score_2_count:>5} ({baseline['score_2_pct']:>4.1f}%) "
                                f"{score_3_count:>5} ({baseline['score_3_pct']:>4.1f}%) "
                                f"{score_4_count:>5} ({baseline['score_4_pct']:>4.1f}%) "
                                f"{incomplete_count:>5} ({baseline['incomplete_pct']:>4.1f}%)")
            else:
                baseline_row = (f"{baseline_title:<60} {int(scored_total):>6} "
                                f"{score_1_count:>5} ({baseline['score_1_pct']:>4.1f}%) "
                                f"{score_2_count:>5} ({baseline['score_2_pct']:>4.1f}%) "
                                f"{score_3_count:>5} ({baseline['score_3_pct']:>4.1f}%) "
                                f"{score_4_count:>5} ({baseline['score_4_pct']:>4.1f}%)")

            rows_to_print.append(baseline_row)

        # Add model rows
        for model_name, model_results in sorted(by_scenario[scenario_id], key=lambda x: x[0]):
            stats = calculate_accuracy_stats(model_results, include_incomplete)

            # Truncate long model names
            display_name = model_name
            if len(display_name) > 60:
                display_name = display_name[:57] + "..."

            # Format row based on whether incomplete is included
            if include_incomplete:
                total_display = f"{stats['total']:>6}"
                if stats['incomplete_count'] > 0:
                    total_display = f"{stats['scored_total']:>3}/{stats['total']:<2}"
                model_row = (f"{display_name:<60} {total_display} "
                             f"{stats['score_1_count']:>5} ({stats['score_1_pct']:>4.1f}%) "
                             f"{stats['score_2_count']:>5} ({stats['score_2_pct']:>4.1f}%) "
                             f"{stats['score_3_count']:>5} ({stats['score_3_pct']:>4.1f}%) "
                             f"{stats['score_4_count']:>5} ({stats['score_4_pct']:>4.1f}%) "
                             f"{stats['incomplete_count']:>5} ({stats['incomplete_pct']:>4.1f}%)")
            else:
                total_display = f"{stats['scored_total']:>6}"
                model_row = (f"{display_name:<60} {total_display} "
                             f"{stats['score_1_count']:>5} ({stats['score_1_pct']:>4.1f}%) "
                             f"{stats['score_2_count']:>5} ({stats['score_2_pct']:>4.1f}%) "
                             f"{stats['score_3_count']:>5} ({stats['score_3_pct']:>4.1f}%) "
                             f"{stats['score_4_count']:>5} ({stats['score_4_pct']:>4.1f}%)")

            rows_to_print.append(model_row)

        # Print all rows for this scenario
        for row in rows_to_print:
            print(row)

    print("-" * table_width)
    print()
    if include_incomplete:
        print("Note: Percentages for Scores 1-4 sum to 100% and exclude incomplete runs.")
        print("      Incomplete % is calculated from total runs (including incomplete).")
    else:
        print("Note: Percentages for Scores 1-4 sum to 100%.")
        print("      Incomplete runs are excluded from this table.")
    if include_baseline:
        print()
        print("Baseline data shows SHIP study results (human counselors) for comparison.")
        print("Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/table/zoi250151t2/")
    print()


def print_detailed_stats(results: list[dict[str, Any]]):
    """Print detailed statistics including completeness and accuracy."""
    grouped = group_by_scenario(results)

    print()
    print("=" * 100)
    print("Detailed Accuracy and Completeness Statistics")
    print("=" * 100)
    print()
    print(f"{'Scenario':<50} {'Total':>6} {'Avg Completeness':>18} {'Avg Accuracy':>18}")
    print(f"{'':50} {'n':>6} {'(%)':>18} {'(%)':>18}")
    print("-" * 100)

    for scenario_id in sorted(grouped.keys()):
        scenario_results = grouped[scenario_id]
        stats = calculate_accuracy_stats(scenario_results)
        title = get_scenario_title(scenario_results)

        print(f"{title:<50} {stats['total']:>6} "
              f"{stats['avg_completeness']*100:>17.1f}% "
              f"{stats['avg_accuracy']*100:>17.1f}%")

    print("-" * 100)
    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate SHIP-style accuracy table from evaluation runs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate table by scenario (incomplete runs and fake models excluded by default)
  python scripts/generate_accuracy_table.py

  # Generate table by model
  python scripts/generate_accuracy_table.py --by-model

  # Filter to specific scenario
  python scripts/generate_accuracy_table.py --scenario SHIP-002

  # Include SHIP study baseline for comparison
  python scripts/generate_accuracy_table.py --include-baseline

  # Compare AI models to human baseline (most useful command)
  python scripts/generate_accuracy_table.py --by-model --include-baseline --scenario SHIP-002

  # Include incomplete runs (runs without rubric scores)
  python scripts/generate_accuracy_table.py --include-incomplete

  # Include fake: test models
  python scripts/generate_accuracy_table.py --include-fake

  # Include both incomplete and fake models
  python scripts/generate_accuracy_table.py --include-incomplete --include-fake

  # Include detailed statistics
  python scripts/generate_accuracy_table.py --detailed
        """
    )

    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("runs"),
        help="Directory containing evaluation runs (default: runs/)"
    )

    parser.add_argument(
        "--by-model",
        action="store_true",
        help="Group results by both scenario and model"
    )

    parser.add_argument(
        "--scenario",
        type=str,
        help="Filter to specific scenario ID (e.g., SHIP-002)"
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Include detailed completeness and accuracy statistics"
    )

    parser.add_argument(
        "--include-baseline",
        action="store_true",
        help="Include SHIP study baseline data (human counselors) for comparison"
    )

    parser.add_argument(
        "--include-incomplete",
        action="store_true",
        help="Include incomplete runs (without rubric scores) in the results. By default, incomplete runs are excluded."
    )

    parser.add_argument(
        "--include-fake",
        action="store_true",
        help="Include fake: test models in the results. By default, fake models are excluded."
    )

    args = parser.parse_args()

    # Load all results (exclude incomplete and fake by default)
    exclude_incomplete = not args.include_incomplete
    exclude_fake = not args.include_fake
    results = load_all_results(args.runs_dir, exclude_incomplete=exclude_incomplete, exclude_fake=exclude_fake)

    if not results:
        if exclude_incomplete or exclude_fake:
            print(f"No results found in {args.runs_dir}", file=sys.stderr)
            filters = []
            if exclude_incomplete:
                filters.append("--include-incomplete to include runs without rubric scores")
            if exclude_fake:
                filters.append("--include-fake to include fake: test models")
            print(f"(Use {' and/or '.join(filters)})", file=sys.stderr)
        else:
            print(f"No results found in {args.runs_dir}", file=sys.stderr)
        sys.exit(1)

    status_msg = f"Loaded {len(results)} evaluation runs from {args.runs_dir}"
    filters_applied = []
    if exclude_incomplete:
        filters_applied.append("incomplete runs excluded")
    if exclude_fake:
        filters_applied.append("fake models excluded")
    if filters_applied:
        status_msg += f" ({', '.join(filters_applied)})"
    print(status_msg)

    # Filter by scenario if requested
    if args.scenario:
        results = [r for r in results if r.get("scenario_id") == args.scenario]
        if not results:
            print(f"No results found for scenario {args.scenario}", file=sys.stderr)
            sys.exit(1)
        print(f"Filtered to {len(results)} runs for scenario {args.scenario}")

    # Generate table
    if args.by_model:
        print_accuracy_table_by_model(results, include_baseline=args.include_baseline, include_incomplete=args.include_incomplete)
    else:
        print_accuracy_table_by_scenario(results, include_baseline=args.include_baseline, include_incomplete=args.include_incomplete)

    # Add detailed stats if requested
    if args.detailed:
        print_detailed_stats(results)


if __name__ == "__main__":
    main()

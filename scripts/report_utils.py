#!/usr/bin/env python3
"""
Shared utility functions for report generation (CLI and web reports).

This module contains functions extracted from generate_accuracy_table.py
to enable code reuse between CLI and web report generators.
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

SHIP_BASELINE_DATA = {
    # Medicare-only scenario questions (n=88) - SHIP-MO-Qn naming
    "SHIP-MO-Q1": {  # Timing for initial enrollment and subsequent changes (also asked in dual, n=184 for "Both")
        "title": "SHIP Baseline: Initial enrollment timing",
        "scenario_type": "Medicare",
        "score_1_pct": 57.1,
        "score_2_pct": 33.2,
        "score_3_pct": 7.1,
        "score_4_pct": 2.7,
        "incomplete_pct": 0.0,
        "total": 184,
    },
    "SHIP-MO-Q2": {  # Medicare enrollment and employer plan interaction
        "title": "SHIP Baseline: Enrollment/employer plan interaction",
        "scenario_type": "Medicare",
        "score_1_pct": 62.5,
        "score_2_pct": 22.7,
        "score_3_pct": 3.4,
        "score_4_pct": 11.4,
        "incomplete_pct": 0.0,
        "total": 88,
    },
    "SHIP-MO-Q3": {  # TM vs MA comparison
        "title": "SHIP Baseline: TM vs MA differences",
        "scenario_type": "Medicare",
        "score_1_pct": 5.7,
        "score_2_pct": 88.6,
        "score_3_pct": 5.7,
        "score_4_pct": 0.0,
        "incomplete_pct": 0.0,
        "total": 88,
    },
    "SHIP-MO-Q4": {
        "title": "SHIP Baseline: Medicare supplement considerations",
        "scenario_type": "Medicare",
        "score_1_pct": 3.4,
        "score_2_pct": 88.6,
        "score_3_pct": 6.8,
        "score_4_pct": 1.1,
        "incomplete_pct": 0.0,
        "total": 88,
    },
    "SHIP-MO-Q5": {
        "title": "SHIP Baseline: Long-term care coverage",
        "scenario_type": "Medicare",
        "score_1_pct": 86.4,
        "score_2_pct": 1.1,
        "score_3_pct": 5.7,
        "score_4_pct": 5.7,
        "incomplete_pct": 1.1,
        "total": 88,
    },
    "SHIP-MO-Q6": {
        "title": "SHIP Baseline: Prescription drug coverage",
        "scenario_type": "Medicare",
        "score_1_pct": 23.9,
        "score_2_pct": 69.3,
        "score_3_pct": 5.7,
        "score_4_pct": 1.1,
        "incomplete_pct": 0.0,
        "total": 88,
    },
    "SHIP-MO-Q7": {
        "title": "SHIP Baseline: PCP in network for MA plan",
        "scenario_type": "Medicare",
        "score_1_pct": 26.1,
        "score_2_pct": 0.0,
        "score_3_pct": 64.8,
        "score_4_pct": 9.1,
        "incomplete_pct": 0.0,
        "total": 88,
    },
    "SHIP-MO-Q8": {
        "title": "SHIP Baseline: MA plan premium",
        "scenario_type": "Medicare",
        "score_1_pct": 19.3,
        "score_2_pct": 47.7,
        "score_3_pct": 21.6,
        "score_4_pct": 9.1,
        "incomplete_pct": 2.3,
        "total": 88,
    },
    "SHIP-MO-Q9": {
        "title": "SHIP Baseline: Out-of-network care",
        "scenario_type": "Medicare",
        "score_1_pct": 61.4,
        "score_2_pct": 15.9,
        "score_3_pct": 14.8,
        "score_4_pct": 4.5,
        "incomplete_pct": 3.4,
        "total": 88,
    },
    "SHIP-MO-Q10": {
        "title": "SHIP Baseline: In-network PCP copay",
        "scenario_type": "Medicare",
        "score_1_pct": 48.9,
        "score_2_pct": 6.8,
        "score_3_pct": 26.1,
        "score_4_pct": 15.9,
        "incomplete_pct": 2.3,
        "total": 88,
    },
    # Additional Medicare-only (Q11-Q13) - placeholders for when scenarios exist
    "SHIP-MO-Q11": {
        "title": "SHIP Baseline: Maximum out-of-pocket limit",
        "scenario_type": "Medicare",
        "score_1_pct": 46.6,
        "score_2_pct": 11.4,
        "score_3_pct": 28.4,
        "score_4_pct": 13.6,
        "incomplete_pct": 0.0,
        "total": 88,
    },
    "SHIP-MO-Q12": {
        "title": "SHIP Baseline: MA plan includes Part D",
        "scenario_type": "Medicare",
        "score_1_pct": 76.1,
        "score_2_pct": 2.3,
        "score_3_pct": 15.9,
        "score_4_pct": 2.3,
        "incomplete_pct": 3.4,
        "total": 88,
    },
    "SHIP-MO-Q13": {
        "title": "SHIP Baseline: MA plan covers Lipitor/generic",
        "scenario_type": "Medicare",
        "score_1_pct": 45.5,
        "score_2_pct": 17.0,
        "score_3_pct": 31.8,
        "score_4_pct": 3.4,
        "incomplete_pct": 2.3,
        "total": 88,
    },
    # Dual-eligible scenario questions (n=96) - SHIP-DE-Qn naming
    "SHIP-DE-Q1": {
        "title": "SHIP Baseline: Options for enrolling with full Medicaid",
        "scenario_type": "Dual",
        "score_1_pct": 24.0,
        "score_2_pct": 47.9,
        "score_3_pct": 19.8,
        "score_4_pct": 8.3,
        "incomplete_pct": 0.0,
        "total": 96,
    },
    "SHIP-DE-Q2": {
        "title": "SHIP Baseline: Considerations for D-SNP",
        "scenario_type": "Dual",
        "score_1_pct": 1.0,
        "score_2_pct": 74.0,
        "score_3_pct": 24.0,
        "score_4_pct": 1.0,
        "incomplete_pct": 0.0,
        "total": 96,
    },
    "SHIP-DE-Q3": {
        "title": "SHIP Baseline: D-SNP availability",
        "scenario_type": "Dual",
        "score_1_pct": 68.8,
        "score_2_pct": 9.4,
        "score_3_pct": 16.7,
        "score_4_pct": 5.2,
        "incomplete_pct": 0.0,
        "total": 96,
    },
    "SHIP-DE-Q4": {
        "title": "SHIP Baseline: Long-term care coverage",
        "scenario_type": "Dual",
        "score_1_pct": 10.4,
        "score_2_pct": 59.4,
        "score_3_pct": 9.4,
        "score_4_pct": 20.8,
        "incomplete_pct": 0.0,
        "total": 96,
    },
    "SHIP-DE-Q5": {
        "title": "SHIP Baseline: Medicaid premium/cost-sharing",
        "scenario_type": "Dual",
        "score_1_pct": 65.6,
        "score_2_pct": 10.4,
        "score_3_pct": 18.8,
        "score_4_pct": 4.2,
        "incomplete_pct": 1.0,
        "total": 96,
    },
    "SHIP-DE-Q6": {
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


def load_all_results(runs_dir: Path) -> list[dict[str, Any]]:
    """Load all results.jsonl files from runs directory.

    Args:
        runs_dir: Directory containing evaluation runs

    Returns:
        List of all evaluation results (unfiltered)
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
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        results.append(data)
        except Exception as e:
            print(f"Warning: Could not load {results_file}: {e}", file=sys.stderr)
            continue

    return results


def filter_incomplete_runs(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter out runs without rubric scores.

    Args:
        results: List of evaluation results

    Returns:
        Filtered list containing only complete runs (rubric_score not None)
    """
    filtered = []
    for result in results:
        final_scores = result.get("final_scores", {})
        rubric_score = final_scores.get("rubric_score")
        if rubric_score is not None:
            filtered.append(result)
    return filtered


def filter_fake_models(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter out fake: test models.

    Args:
        results: List of evaluation results

    Returns:
        Filtered list excluding models starting with "fake:"
    """
    filtered = []
    for result in results:
        target = result.get("target", {})
        model_name = target.get("model_name", "")
        if not model_name.startswith("fake:"):
            filtered.append(result)
    return filtered


def filter_by_scenario(results: list[dict[str, Any]], scenario_id: str) -> list[dict[str, Any]]:
    """Filter to specific scenario.

    Args:
        results: List of evaluation results
        scenario_id: Scenario identifier (e.g., SHIP-MO-Q3)

    Returns:
        Filtered list containing only runs matching scenario_id
    """
    return [r for r in results if r.get("scenario_id") == scenario_id]


def group_by_model(results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group results by target model.

    Args:
        results: List of evaluation results

    Returns:
        Dictionary mapping model names to lists of runs
    """
    grouped = defaultdict(list)
    for result in results:
        model_name = result.get("target", {}).get("model_name", "Unknown")
        grouped[model_name].append(result)
    return dict(grouped)


def group_by_scenario(results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group results by scenario.

    Args:
        results: List of evaluation results

    Returns:
        Dictionary mapping scenario IDs to lists of runs
    """
    grouped = defaultdict(list)
    for result in results:
        scenario_id = result.get("scenario_id", "Unknown")
        grouped[scenario_id].append(result)
    return dict(grouped)


def calculate_score_distribution(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate score distribution for a group of runs.

    Args:
        results: List of evaluation results (should all be complete)

    Returns:
        Dictionary with score counts, percentages, and statistics
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

    # Count scores
    score_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    incomplete_count = 0
    completeness_sum = 0.0
    accuracy_sum = 0.0
    scored_count = 0

    for result in results:
        final_scores = result.get("final_scores", {})
        rubric_score = final_scores.get("rubric_score")

        if rubric_score is not None:
            score_counts[rubric_score] += 1
            scored_count += 1

            # Track completeness and accuracy for scored runs
            completeness = final_scores.get("completeness_percentage", 0.0)
            accuracy = final_scores.get("accuracy_percentage", 0.0)
            completeness_sum += completeness * 100
            accuracy_sum += accuracy * 100
        else:
            incomplete_count += 1

    # Calculate percentages (based on scored runs only)
    if scored_count > 0:
        score_1_pct = (score_counts[1] / scored_count) * 100
        score_2_pct = (score_counts[2] / scored_count) * 100
        score_3_pct = (score_counts[3] / scored_count) * 100
        score_4_pct = (score_counts[4] / scored_count) * 100
        avg_completeness = completeness_sum / scored_count
        avg_accuracy = accuracy_sum / scored_count
    else:
        score_1_pct = score_2_pct = score_3_pct = score_4_pct = 0.0
        avg_completeness = avg_accuracy = 0.0

    # Calculate incomplete percentage (based on total runs)
    incomplete_pct = (incomplete_count / total) * 100 if total > 0 else 0.0

    return {
        "total": total,
        "scored_total": scored_count,
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
        "avg_completeness": avg_completeness,
        "avg_accuracy": avg_accuracy,
    }


def get_baseline_data(scenario_id: str) -> dict[str, Any] | None:
    """Get SHIP study baseline data for scenario.

    Args:
        scenario_id: Scenario identifier (e.g., SHIP-MO-Q3)

    Returns:
        Baseline data dictionary if available, None otherwise
    """
    return SHIP_BASELINE_DATA.get(scenario_id)

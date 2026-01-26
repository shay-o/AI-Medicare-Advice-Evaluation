#!/usr/bin/env python3
"""
Generate SHIP-style accuracy table from evaluation runs.

Reproduces Table 2 format from the SHIP study:
https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/table/zoi250151t2/

Usage:
    python scripts/generate_accuracy_table.py
    python scripts/generate_accuracy_table.py --by-model
    python scripts/generate_accuracy_table.py --scenario SHIP-002
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_all_results(runs_dir: Path) -> list[dict[str, Any]]:
    """Load all results.jsonl files from runs directory."""
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


def calculate_accuracy_stats(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate accuracy statistics in SHIP format.

    Returns counts and percentages for each rubric score:
    - Score 1: Accurate and complete
    - Score 2: Substantive but incomplete (or "Accurate but incomplete")
    - Score 3: Not substantive
    - Score 4: Incorrect

    Percentages are calculated only from scored runs (excluding incomplete/failed runs).
    This ensures percentages sum to 100% for each row.
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

    # Incomplete percentage is from total runs
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
    titles = {
        "SHIP-001": "SHIP Question #1: Initial Enrollment",
        "SHIP-002": "SHIP Question #3: MA vs TM Comparison",
        "scenario_001": "Scenario 001: General MA vs TM",
        "scenario_002": "Scenario 002: SHIP Question #3",
    }

    return titles.get(scenario_id, scenario_id)


def print_accuracy_table_by_scenario(results: list[dict[str, Any]], title: str = "AI Model Accuracy Table"):
    """Print SHIP-style accuracy table grouped by scenario."""
    grouped = group_by_scenario(results)

    if not grouped:
        print("No results found.")
        return

    print()
    print("=" * 135)
    print(f"{title}")
    print("=" * 135)
    print()
    print(f"{'Question/Scenario':<50} {'Total':>6} {'Score 1':>12} {'Score 2':>12} {'Score 3':>12} {'Score 4':>12} {'Incomplete':>12}")
    print(f"{'':50} {'n':>6} {'Accurate &':>12} {'Accurate but':>12} {'Not':>12} {'Incorrect':>12} {'Data':>12}")
    print(f"{'':50} {'':>6} {'Complete':>12} {'Incomplete':>12} {'Substantive':>12} {'':>12} {'':>12}")
    print(f"{'':50} {'':>6} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12}")
    print("-" * 135)

    for scenario_id in sorted(grouped.keys()):
        scenario_results = grouped[scenario_id]
        stats = calculate_accuracy_stats(scenario_results)
        title = get_scenario_title(scenario_results)

        # Show scored total in parentheses if different from total
        total_display = f"{stats['total']:>6}"
        if stats['incomplete_count'] > 0:
            total_display = f"{stats['scored_total']:>3}/{stats['total']:<2}"

        print(f"{title:<50} {total_display} "
              f"{stats['score_1_count']:>5} ({stats['score_1_pct']:>4.1f}%) "
              f"{stats['score_2_count']:>5} ({stats['score_2_pct']:>4.1f}%) "
              f"{stats['score_3_count']:>5} ({stats['score_3_pct']:>4.1f}%) "
              f"{stats['score_4_count']:>5} ({stats['score_4_pct']:>4.1f}%) "
              f"{stats['incomplete_count']:>5} ({stats['incomplete_pct']:>4.1f}%)")

    print("-" * 135)
    print()
    print("Score Definitions (SHIP Rubric):")
    print("  Score 1: Accurate and Complete - All required facts covered correctly")
    print("  Score 2: Substantive but Incomplete - Some facts covered, no major errors")
    print("  Score 3: Not Substantive - Insufficient coverage or \"I don't know\"")
    print("  Score 4: Incorrect - Materially wrong information that could affect decisions")
    print("  Incomplete Data: Runs that failed or did not produce a rubric score")
    print()
    print("Note: Percentages for Scores 1-4 sum to 100% and exclude incomplete runs.")
    print("      Incomplete % is calculated from total runs (including incomplete).")
    print()


def print_accuracy_table_by_model(results: list[dict[str, Any]], title: str = "AI Model Accuracy Table (by Model)"):
    """Print SHIP-style accuracy table grouped by scenario and model."""
    grouped = group_by_scenario_and_model(results)

    if not grouped:
        print("No results found.")
        return

    print()
    print("=" * 145)
    print(f"{title}")
    print("=" * 145)
    print()
    print(f"{'Scenario / Model':<60} {'Total':>6} {'Score 1':>12} {'Score 2':>12} {'Score 3':>12} {'Score 4':>12} {'Incomplete':>12}")
    print(f"{'':60} {'n':>6} {'Accurate &':>12} {'Accurate but':>12} {'Not':>12} {'Incorrect':>12} {'Data':>12}")
    print(f"{'':60} {'':>6} {'Complete':>12} {'Incomplete':>12} {'Substantive':>12} {'':>12} {'':>12}")
    print(f"{'':60} {'':>6} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12} {'No. (%)':>12}")
    print("-" * 145)

    # Group by scenario first
    by_scenario = defaultdict(list)
    for (scenario_id, model_name), scenario_results in grouped.items():
        by_scenario[scenario_id].append((model_name, scenario_results))

    for scenario_id in sorted(by_scenario.keys()):
        scenario_title = get_scenario_title(by_scenario[scenario_id][0][1])
        print(f"\n{scenario_title}")
        print("-" * 145)

        for model_name, model_results in sorted(by_scenario[scenario_id], key=lambda x: x[0]):
            stats = calculate_accuracy_stats(model_results)

            # Truncate long model names
            display_name = f"  {model_name}"
            if len(display_name) > 58:
                display_name = display_name[:55] + "..."

            # Show scored total in parentheses if different from total
            total_display = f"{stats['total']:>6}"
            if stats['incomplete_count'] > 0:
                total_display = f"{stats['scored_total']:>3}/{stats['total']:<2}"

            print(f"{display_name:<60} {total_display} "
                  f"{stats['score_1_count']:>5} ({stats['score_1_pct']:>4.1f}%) "
                  f"{stats['score_2_count']:>5} ({stats['score_2_pct']:>4.1f}%) "
                  f"{stats['score_3_count']:>5} ({stats['score_3_pct']:>4.1f}%) "
                  f"{stats['score_4_count']:>5} ({stats['score_4_pct']:>4.1f}%) "
                  f"{stats['incomplete_count']:>5} ({stats['incomplete_pct']:>4.1f}%)")

    print("-" * 145)
    print()
    print("Note: Percentages for Scores 1-4 sum to 100% and exclude incomplete runs.")
    print("      Incomplete % is calculated from total runs (including incomplete).")
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
  # Generate table by scenario
  python scripts/generate_accuracy_table.py

  # Generate table by model
  python scripts/generate_accuracy_table.py --by-model

  # Filter to specific scenario
  python scripts/generate_accuracy_table.py --scenario SHIP-002

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

    args = parser.parse_args()

    # Load all results
    results = load_all_results(args.runs_dir)

    if not results:
        print(f"No results found in {args.runs_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(results)} evaluation runs from {args.runs_dir}")

    # Filter by scenario if requested
    if args.scenario:
        results = [r for r in results if r.get("scenario_id") == args.scenario]
        if not results:
            print(f"No results found for scenario {args.scenario}", file=sys.stderr)
            sys.exit(1)
        print(f"Filtered to {len(results)} runs for scenario {args.scenario}")

    # Generate table
    if args.by_model:
        print_accuracy_table_by_model(results)
    else:
        print_accuracy_table_by_scenario(results)

    # Add detailed stats if requested
    if args.detailed:
        print_detailed_stats(results)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate eTable 3-style web report comparing AI model performance
against SHIP study human counselor baseline.

Reproduces the structure of eTable 3 (Phone Shops) from:
Dugan K et al. JAMA Network Open. 2025;8(4):e252834

Rows are organized by question, with sub-rows for SHIP baseline,
All AI, company-level, and individual model aggregations.

Usage:
    python scripts/generate_etable3_report.py
    python scripts/generate_etable3_report.py --runs-dir runs --output reports/etable3_report.html
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from report_utils import load_all_results, filter_fake_models
from report_constants import ETHICS_DISCLAIMER


# ============================================================================
# Constants
# ============================================================================

SCORE_CATEGORIES = [
    "accurate_complete",
    "substantive_incomplete",
    "not_substantive",
    "incorrect",
    "missing",
]

COMPANY_DISPLAY_NAMES = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google",
    "x-ai": "X.AI",
    "meta": "Meta",
    "mistral": "Mistral",
}

COMPANY_SORT_ORDER = {
    "OpenAI": 0,
    "Anthropic": 1,
    "Google": 2,
    "X.AI": 3,
    "Meta": 4,
    "Mistral": 5,
}


# ============================================================================
# Data Loading
# ============================================================================

def load_question_mapping(path: Path) -> dict[str, Any]:
    """Load the eTable 3 question mapping file."""
    with open(path, "r") as f:
        return json.load(f)


def get_company_name(model_name: str) -> str:
    """Derive company display name from model_name prefix."""
    prefix = model_name.split("/")[0] if "/" in model_name else model_name
    return COMPANY_DISPLAY_NAMES.get(prefix, prefix)


def get_model_short_name(model_name: str) -> str:
    """Get the model name without company prefix."""
    return model_name.split("/", 1)[1] if "/" in model_name else model_name


# ============================================================================
# Aggregation
# ============================================================================

def extract_question_tallies(
    results: list[dict[str, Any]],
) -> dict[str, dict[str, dict[str, int]]]:
    """Extract per-question, per-model score tallies from grading data.

    Returns:
        {group_id: {model_name: {score_category: count}}}
    """
    tallies: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )

    for result in results:
        model_name = result.get("target", {}).get("model_name", "Unknown")
        grading = result.get("grading", {})
        question_scores = grading.get("question_scores", [])

        for qs in question_scores:
            group_id = qs.get("group_id", "")
            score = qs.get("score", "")

            if not group_id or group_id == "ERROR":
                continue
            if score not in SCORE_CATEGORIES:
                continue

            tallies[group_id][model_name][score] += 1

    return tallies


def tally_to_percentages(tally: dict[str, int]) -> dict[str, Any]:
    """Convert a score tally to percentages.

    Returns dict with n, and percentage for each category.
    """
    total = sum(tally.get(cat, 0) for cat in SCORE_CATEGORIES)
    if total == 0:
        return {"n": 0, "ac": 0.0, "si": 0.0, "ns": 0.0, "inc": 0.0, "id": 0.0}

    return {
        "n": total,
        "ac": (tally.get("accurate_complete", 0) / total) * 100,
        "si": (tally.get("substantive_incomplete", 0) / total) * 100,
        "ns": (tally.get("not_substantive", 0) / total) * 100,
        "inc": (tally.get("incorrect", 0) / total) * 100,
        "id": (tally.get("missing", 0) / total) * 100,
    }


def merge_tallies(*tallies: dict[str, int]) -> dict[str, int]:
    """Merge multiple score tallies into one."""
    merged: dict[str, int] = defaultdict(int)
    for t in tallies:
        for cat, count in t.items():
            merged[cat] += count
    return dict(merged)


# ============================================================================
# Report Data Building
# ============================================================================

def build_report_data(
    results: list[dict[str, Any]],
    mapping: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build the complete report data structure for template rendering.

    Returns list of sections, each with questions and their data rows.
    """
    tallies = extract_question_tallies(results)

    # Discover all models and group by company
    all_models = set()
    for group_tallies in tallies.values():
        all_models.update(group_tallies.keys())

    models_by_company: dict[str, list[str]] = defaultdict(list)
    for model in sorted(all_models):
        company = get_company_name(model)
        models_by_company[company].append(model)

    sections = []
    for section_def in mapping["sections"]:
        section = {
            "section_name": section_def["section_name"],
            "section_note": section_def.get("section_note", ""),
            "ship_sample_size": section_def["ship_sample_size"],
            "questions": [],
        }

        for row_def in section_def["rows"]:
            group_id = row_def["group_id"]
            baseline = row_def["baseline_phone"]
            group_tallies = tallies.get(group_id, {})

            question = {
                "etable3_label": row_def["etable3_label"],
                "group_id": group_id,
                "rows": [],
            }

            # 1. SHIP baseline row
            question["rows"].append({
                "label": "SHIP Counselors (phone)",
                "type": "baseline",
                "n": baseline["n"],
                "ac": baseline["accurate_complete"],
                "si": baseline["substantive_incomplete"],
                "ns": baseline["not_substantive"],
                "inc": baseline["incorrect"],
                "id": baseline["incomplete_data"],
            })

            # 2. All AI row
            all_ai_tally = merge_tallies(
                *[group_tallies.get(m, {}) for m in all_models]
            )
            all_ai_pcts = tally_to_percentages(all_ai_tally)
            if all_ai_pcts["n"] > 0:
                question["rows"].append({
                    "label": "All AI Models",
                    "type": "all_ai",
                    **all_ai_pcts,
                })

            # 3. Company rows + individual models
            sorted_companies = sorted(
                models_by_company.keys(),
                key=lambda c: COMPANY_SORT_ORDER.get(c, 99),
            )

            for company in sorted_companies:
                company_models = models_by_company[company]
                company_tally = merge_tallies(
                    *[group_tallies.get(m, {}) for m in company_models]
                )
                company_pcts = tally_to_percentages(company_tally)

                if company_pcts["n"] == 0:
                    continue

                question["rows"].append({
                    "label": company,
                    "type": "company",
                    **company_pcts,
                })

                # Individual model rows under company
                for model in sorted(company_models):
                    model_tally = group_tallies.get(model, {})
                    model_pcts = tally_to_percentages(model_tally)
                    if model_pcts["n"] == 0:
                        continue

                    question["rows"].append({
                        "label": get_model_short_name(model),
                        "type": "model",
                        "company": company,
                        **model_pcts,
                    })

            section["questions"].append(question)

        sections.append(section)

    return sections


# ============================================================================
# HTML Generation
# ============================================================================

def generate_etable3_report(
    runs_dir: Path = Path("runs"),
    output_path: Path = Path("reports/etable3_report.html"),
    exclude_back: bool = True,
) -> None:
    """Generate the eTable 3-style HTML report."""
    print("Generating eTable 3 report...")
    print(f"  Loading runs from: {runs_dir}")

    if not runs_dir.exists() or not runs_dir.is_dir():
        print(f"Error: Runs directory does not exist: {runs_dir}", file=sys.stderr)
        sys.exit(1)

    # Load results
    results = load_all_results(runs_dir)
    total_loaded = len(results)
    print(f"  Loaded {total_loaded} runs")

    # Filter
    results = filter_fake_models(results)

    if exclude_back:
        results = [
            r for r in results
            if not r.get("_source_dir", "").startswith("Back")
        ]

    # Also filter runs that have no grading data
    results = [r for r in results if r.get("grading", {}).get("question_scores")]

    # Only include "ALL" scenario runs to avoid double-counting from sub-scenarios
    # (e.g., SHIP-MO-PLAN-EXAMPLE, SHIP-MO-Q1 duplicate questions from SHIP-MO-ALL)
    ALLOWED_SCENARIOS = {"SHIP-MO-ALL", "SHIP-DE-ALL"}
    results = [r for r in results if r.get("scenario_id") in ALLOWED_SCENARIOS]
    print(f"  After filtering: {len(results)} runs with grading data")

    if not results:
        print("Error: No runs with grading data found.", file=sys.stderr)
        sys.exit(1)

    # Load question mapping
    mapping_path = Path(__file__).parent.parent / "reference_material" / "etable3_question_mapping.json"
    if not mapping_path.exists():
        print(f"Error: Question mapping not found: {mapping_path}", file=sys.stderr)
        sys.exit(1)
    mapping = load_question_mapping(mapping_path)

    # Build report data
    sections = build_report_data(results, mapping)

    # Count models for metadata
    all_models = set()
    for result in results:
        model_name = result.get("target", {}).get("model_name", "")
        if model_name:
            all_models.add(model_name)

    # Render template
    template_dir = Path(__file__).parent
    template_name = "etable3_report_template.html"
    template_path = template_dir / template_name

    if not template_path.exists():
        print(f"Error: Template not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template(template_name)

    html_content = template.render(
        sections=sections,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_runs=len(results),
        total_models=len(all_models),
        model_list=sorted(all_models),
        ethics_disclaimer=ETHICS_DISCLAIMER,
        source_citation=mapping.get("source", ""),
    )

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    file_size = output_path.stat().st_size
    print(f"\n  Report generated successfully")
    print(f"  Output: {output_path}")
    print(f"  Size: {file_size / 1024:.1f} KB")
    print(f"  Models: {len(all_models)}")
    print(f"  Runs: {len(results)}")


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate eTable 3-style web report comparing AI vs SHIP counselors",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("runs"),
        help="Directory containing evaluation runs (default: runs/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/etable3_report.html"),
        help="Output HTML file path (default: reports/etable3_report.html)",
    )
    parser.add_argument(
        "--include-back",
        action="store_true",
        help="Include runs from Back/ directory (default: excluded)",
    )

    args = parser.parse_args()

    generate_etable3_report(
        runs_dir=args.runs_dir,
        output_path=args.output,
        exclude_back=not args.include_back,
    )

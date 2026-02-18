#!/usr/bin/env python3
"""
Generate AI vs SHIP comparison matrix report.

Produces a self-contained HTML file showing how AI model scores compare to
SHIP human counselor scores at the question, company, and model level, with
a side drawer for viewing verbatim AI responses and scoring criteria.

Usage:
    python scripts/generate_matrix_report.py
    python scripts/generate_matrix_report.py --runs-dir runs --output reports/matrix_report.html
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

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

# Maps raw score key → (display code for JS, human-readable label)
SCORE_TO_DISPLAY = {
    "accurate_complete":       ("ac",     "Accurate & Complete (Score 1)"),
    "substantive_incomplete":  ("inc",    "Accurate but Incomplete (Score 2)"),
    "not_substantive":         ("ns",     "Not Substantive (Score 3)"),
    "incorrect":               ("incorr", "Incorrect (Score 4)"),
    "missing":                 ("ns",     "Not Substantive / Missing"),
}


# ============================================================================
# Helpers
# ============================================================================

def get_company_name(model_name: str) -> str:
    prefix = model_name.split("/")[0] if "/" in model_name else model_name
    return COMPANY_DISPLAY_NAMES.get(prefix, prefix)


def get_model_short_name(model_name: str) -> str:
    return model_name.split("/", 1)[1] if "/" in model_name else model_name


def model_slug(name: str) -> str:
    """Convert model short name to URL-safe slug (matches wireframe JS function)."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def merge_tallies(*tallies: dict[str, int]) -> dict[str, int]:
    merged: dict[str, int] = defaultdict(int)
    for t in tallies:
        for cat, count in t.items():
            merged[cat] += count
    return dict(merged)


def tally_to_pcts(tally: dict[str, int]) -> dict[str, Any]:
    """Convert score tally to percentage dict used in JS data objects."""
    total = sum(tally.get(cat, 0) for cat in SCORE_CATEGORIES)
    if total == 0:
        return {"n": 0, "ac": 0.0, "si": 0.0, "ns": 0.0, "inc": 0.0}
    return {
        "n": total,
        "ac": tally.get("accurate_complete", 0) / total * 100,
        "si": tally.get("substantive_incomplete", 0) / total * 100,
        "ns": tally.get("not_substantive", 0) / total * 100,
        "inc": tally.get("incorrect", 0) / total * 100,
    }


# ============================================================================
# Data Extraction
# ============================================================================

def extract_tallies_and_responses(
    results: list[dict[str, Any]],
) -> tuple[dict, dict]:
    """Extract per-question score tallies and verbatim response data.

    Returns:
        tallies:   {group_id: {model_name: {score_category: count}}}
        responses: {group_id: {model_name: [run_dict, ...]}}
    """
    tallies: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )
    responses: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))

    for result in results:
        model_name = result.get("target", {}).get("model_name", "Unknown")
        question_scores = result.get("grading", {}).get("question_scores", [])

        for qs in question_scores:
            group_id = qs.get("group_id", "")
            score = qs.get("score", "")

            if not group_id or group_id == "ERROR" or score not in SCORE_CATEGORIES:
                continue

            tallies[group_id][model_name][score] += 1

            response_text = qs.get("response_text", "")
            # Treat ['None'] / ['none'] as empty lists
            raw_met = qs.get("criteria_met") or []
            raw_missed = qs.get("criteria_missed") or []
            criteria_met = [c for c in raw_met if c and c.strip().lower() != "none"]
            criteria_missed = [c for c in raw_missed if c and c.strip().lower() != "none"]

            if response_text:
                score_code, score_label = SCORE_TO_DISPLAY.get(score, ("ns", score))
                responses[group_id][model_name].append({
                    "score": score_code,
                    "scoreLabel": score_label,
                    "response": response_text,
                    "met": criteria_met,
                    "missed": criteria_missed,
                })

    return tallies, responses


# ============================================================================
# JS Data Building
# ============================================================================

def build_js_data(
    results: list[dict[str, Any]],
    mapping: dict[str, Any],
) -> dict[str, Any]:
    """Build all JS data structures for the HTML report."""
    tallies, raw_responses = extract_tallies_and_responses(results)

    # Discover all models and group by company
    all_models: set[str] = set()
    for group_tallies in tallies.values():
        all_models.update(group_tallies.keys())

    models_by_company: dict[str, list[str]] = defaultdict(list)
    for model in sorted(all_models):
        company = get_company_name(model)
        models_by_company[company].append(model)

    sorted_companies = sorted(
        models_by_company.keys(),
        key=lambda c: COMPANY_SORT_ORDER.get(c, 99),
    )

    # ── SHIP & QUESTIONS ──────────────────────────────────────────────────
    ship_js: dict[str, Any] = {}
    questions_js: list[dict[str, Any]] = []
    q_num = 0

    for section_def in mapping["sections"]:
        section_name = section_def["section_name"]
        for row_def in section_def["rows"]:
            q_num += 1
            group_id = row_def["group_id"]
            baseline = row_def["baseline_phone"]
            qid = group_id.lower()

            ship_js[qid] = {
                "ac":        baseline["accurate_complete"],
                "inc":       baseline["substantive_incomplete"],
                "ns":        baseline["not_substantive"],
                "incorrect": baseline["incorrect"],
                "n":         baseline["n"],
            }

            # All-AI aggregate for this question
            all_ai_tally = merge_tallies(
                *[tallies.get(group_id, {}).get(m, {}) for m in all_models]
            )
            ai = tally_to_pcts(all_ai_tally)
            delta = round(ai["ac"] - baseline["accurate_complete"], 1) if ai["n"] > 0 else 0.0

            questions_js.append({
                "id":       qid,
                "group_id": group_id,
                "num":      q_num,
                "label":    row_def["etable3_label"],
                "section":  section_name,
                "shipN":    baseline["n"],
                "aiN":      ai["n"],
                "aiAC":     ai["ac"],
                "aiInc":    ai["si"],   # Accurate but Incomplete
                "aiNS":     ai["ns"],
                "aiIncorr": ai["inc"],  # Incorrect
                "delta":    delta,
            })

    # ── CO_SCORES ─────────────────────────────────────────────────────────
    co_scores_js: dict[str, dict[str, Any]] = {}
    for company in sorted_companies:
        company_models = models_by_company[company]
        co_scores_js[company] = {}
        for section_def in mapping["sections"]:
            for row_def in section_def["rows"]:
                group_id = row_def["group_id"]
                qid = group_id.lower()
                co_tally = merge_tallies(
                    *[tallies.get(group_id, {}).get(m, {}) for m in company_models]
                )
                co = tally_to_pcts(co_tally)
                co_scores_js[company][qid] = {
                    "ac":        co["ac"],
                    "inc":       co["si"],
                    "ns":        co["ns"],
                    "incorrect": co["inc"],
                    "n":         co["n"],
                }

    # ── MODELS ────────────────────────────────────────────────────────────
    models_js: list[dict[str, Any]] = []
    for company in sorted_companies:
        for model_full in sorted(models_by_company[company]):
            short_name = get_model_short_name(model_full)
            model_scores: dict[str, Any] = {}
            for section_def in mapping["sections"]:
                for row_def in section_def["rows"]:
                    group_id = row_def["group_id"]
                    qid = group_id.lower()
                    mt = tally_to_pcts(tallies.get(group_id, {}).get(model_full, {}))
                    model_scores[qid] = {
                        "ac":        mt["ac"],
                        "inc":       mt["si"],
                        "ns":        mt["ns"],
                        "incorrect": mt["inc"],
                        "n":         mt["n"],
                    }
            models_js.append({
                "name":    short_name,
                "company": company,
                "scores":  model_scores,
            })

    # ── RESPONSES ─────────────────────────────────────────────────────────
    responses_js: dict[str, Any] = {}
    for group_id, model_runs in raw_responses.items():
        qid = group_id.lower()
        for model_full, runs in model_runs.items():
            short_name = get_model_short_name(model_full)
            slug = model_slug(short_name)
            key = f"{qid}-{slug}"
            responses_js[key] = {"runs": runs}

    return {
        "ship":      ship_js,
        "questions": questions_js,
        "companies": sorted_companies,
        "co_scores": co_scores_js,
        "models":    models_js,
        "responses": responses_js,
    }


# ============================================================================
# HTML Generation
# ============================================================================

def _j(obj: Any) -> str:
    """Compact JSON serialization for embedding in JS."""
    return json.dumps(obj, ensure_ascii=False)


def generate_html(
    js_data: dict[str, Any],
    generated_at: str,
    total_runs: int,
    total_models: int,
    ethics_disclaimer: str,
) -> str:
    ship_json      = _j(js_data["ship"])
    questions_json = _j(js_data["questions"])
    companies_json = _j(js_data["companies"])
    co_scores_json = _j(js_data["co_scores"])
    models_json    = _j(js_data["models"])
    responses_json = _j(js_data["responses"])

    disclaimer_html = (
        f'<strong>Research Use Only.</strong> {ethics_disclaimer}'
        if ethics_disclaimer
        else "<strong>Research Use Only.</strong> This report evaluates AI Medicare advice "
             "using SHIP study methodology (Dugan et al., JAMA Network Open 2025). "
             "Not for clinical or consumer use."
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI vs SHIP Score Comparison — AI Medicare Evaluator</title>
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: #f5f5f5; color: #333333; font-size: 14px; line-height: 1.5;
}}

/* ── PAGE HEADER ── */
.page-header {{
  background: #1a237e; color: #ffffff;
  padding: 12px 20px;
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  position: sticky; top: 0; z-index: 200;
}}
.page-header-title {{ font-size: 14px; font-weight: 600; }}
.page-header-meta {{ font-size: 11px; color: #9fa8da; }}

/* ── DISCLAIMER ── */
.disclaimer {{
  background: #fff8e1; border-left: 4px solid #f9a825; padding: 8px 16px;
  font-size: 12px; color: #555555;
}}
.disclaimer strong {{ color: #000000; }}

/* ── MAIN LAYOUT: matrix + drawer ── */
.app-layout {{
  display: flex; align-items: flex-start; min-height: calc(100vh - 80px);
}}
.matrix-col {{
  flex: 1; min-width: 0; padding: 16px 20px;
}}
.drawer-col {{
  width: 0; flex-shrink: 0; overflow: hidden;
  border-left: 0px solid #cccccc;
  transition: width 0.25s, border-color 0.25s;
  background: #ffffff;
  position: sticky; top: 41px; height: calc(100vh - 41px);
}}
.drawer-col.open {{
  width: 440px;
  border-left: 2px solid #1a237e;
}}

/* ── CONTROLS BAR ── */
.controls-bar {{
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 9px 14px; background: #ffffff; border: 1px solid #e0e0e0;
  border-radius: 4px; margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}}
.ctrl-label {{ font-size: 11px; color: #999999; }}
.ctrl-btn {{
  padding: 4px 11px; border: 1px solid #cccccc; border-radius: 3px;
  background: #ffffff; font-family: inherit; font-size: 12px; cursor: pointer;
  color: #333333; font-weight: 500;
}}
.ctrl-btn:hover {{ background: #f5f5f5; }}
.ctrl-btn.active {{ background: #1a237e; color: #ffffff; border-color: #1a237e; }}
.ctrl-divider {{ width: 1px; height: 18px; background: #e0e0e0; flex-shrink: 0; }}

/* ── TOGGLE SWITCH ── */
.model-toggle-wrap {{ display: flex; align-items: center; gap: 8px; }}
.toggle-lbl {{ font-size: 12px; color: #999999; cursor: pointer; user-select: none; }}
.toggle-lbl.toggle-active {{ color: #000000; font-weight: 600; }}
.toggle-pill {{ position: relative; display: inline-block; width: 36px; height: 20px; flex-shrink: 0; }}
.toggle-pill input {{ display: none; }}
.toggle-track {{
  position: absolute; inset: 0; background: #cccccc; border-radius: 10px;
  cursor: pointer; transition: background 0.2s; border: 1px solid #bbbbbb;
}}
.toggle-pill input:checked + .toggle-track {{ background: #1a237e; border-color: #1a237e; }}
.toggle-knob {{
  position: absolute; top: 3px; left: 3px; width: 12px; height: 12px;
  background: #ffffff; border-radius: 50%; transition: left 0.2s; pointer-events: none;
  box-shadow: 0 1px 2px rgba(0,0,0,0.25);
}}
.toggle-pill input:checked + .toggle-track .toggle-knob {{ left: 19px; }}

/* ── SECTION HEADING ── */
.section-heading {{
  font-size: 15px; font-weight: 700; color: #000000; margin-bottom: 2px;
  border-bottom: 2px solid #1976D2; padding-bottom: 6px;
}}
.section-meta {{
  font-size: 12px; color: #666666; font-style: italic; margin-bottom: 12px;
}}

/* ── MATRIX TABLE ── */
.tbl-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
.mtable {{ border-collapse: collapse; width: 100%; font-size: 12px; min-width: 720px; }}

.mtable th {{
  background: #e8eaf6; border: 1px solid #c5cae9;
  padding: 7px 10px; font-size: 11px; font-weight: 600; white-space: nowrap;
  user-select: none; position: sticky; top: 41px; z-index: 10; color: #1a237e;
}}
.mtable th.sortable {{ cursor: pointer; }}
.mtable th.sortable:hover {{ background: #c5cae9; }}
.mtable th:first-child {{ text-align: center; min-width: 36px; }}
.mtable th:nth-child(2) {{ text-align: left; min-width: 220px; }}
.mtable th.sort-asc::after {{ content: " ▲"; font-size: 9px; }}
.mtable th.sort-desc::after {{ content: " ▼"; font-size: 9px; }}

.mtable td {{
  border: 1px solid #eeeeee; padding: 7px 10px;
  vertical-align: middle; text-align: center;
}}
.mtable td:first-child {{
  font-size: 11px; font-weight: 700; color: #9e9e9e;
  background: #f8f8f8; border-right: 1px solid #e0e0e0; text-align: center;
}}
.mtable td:nth-child(2) {{ text-align: left; }}

/* Aggregate row */
.row-agg td {{ background: #fafafa; }}
.row-agg td:first-child {{ background: #f0f0f0; }}
.row-agg:hover td {{ background: #f0f4ff; }}
.q-label {{ font-size: 12px; font-weight: 600; color: #000000; }}

/* Section separator row */
.row-section td {{
  background: #e8eaf6 !important; color: #1a237e !important;
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.6px; padding: 5px 10px; border-top: 2px solid #9fa8da;
}}

/* Company rows */
.row-company {{ display: none; }}
.row-company.visible {{ display: table-row; }}
.row-company td {{ background: #f5f5f5; }}
.row-company td:first-child {{ background: #eeeeee; color: #cccccc; font-size: 10px; }}
.row-company:hover td {{ background: #ede7f6; }}
.co-name {{ font-size: 11px; font-weight: 600; color: #333333; padding-left: 16px; }}
.co-n {{ font-size: 10px; color: #999999; font-weight: 400; }}

/* Model rows */
.row-model {{ display: none; }}
.row-model.visible {{ display: table-row; }}
.row-model td {{ background: #ffffff; }}
.row-model td:first-child {{ background: #fafafa; color: #dddddd; }}
.row-model.active-row td {{ background: #e8eaf6; }}
.row-model.active-row td:first-child {{ background: #dde1f5; }}

/* Clickable model rows */
.row-model.clickable {{ cursor: pointer; }}
.row-model.clickable:hover td {{ background: #f3e5f5; }}
.row-model.clickable:hover td:first-child {{ background: #ede7f6; }}
.model-name {{
  font-size: 11px; font-style: italic; color: #555555;
  padding-left: 32px; display: flex; align-items: center; gap: 5px;
}}
.model-view-hint {{
  font-size: 9px; color: #1976D2; border: 1px solid #90caf9;
  border-radius: 2px; padding: 1px 4px; background: #e3f2fd; flex-shrink: 0;
  white-space: nowrap; font-style: normal;
}}
.row-model.active-row .model-view-hint {{
  background: #1a237e; color: #ffffff; border-color: #1a237e;
}}
.no-data-badge {{
  font-size: 9px; color: #cccccc; font-style: normal;
}}

/* Expand button */
.xbtn {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 15px; height: 15px; border: 1px solid #9e9e9e; border-radius: 2px;
  background: #eeeeee; cursor: pointer; font-size: 10px; font-weight: 700;
  font-family: inherit; line-height: 1; flex-shrink: 0; vertical-align: middle;
  margin-right: 4px;
}}
.xbtn:hover {{ background: #bdbdbd; }}

/* ── BAR CELLS ── */
.cell-cmp {{ display: flex; flex-direction: column; gap: 2px; min-width: 80px; }}
.cmp-row {{ display: flex; align-items: center; gap: 4px; }}
.cmp-lbl {{ font-size: 9px; color: #999999; width: 30px; text-align: right; flex-shrink: 0; }}
.cmp-track {{ flex: 1; height: 7px; background: #eeeeee; border-radius: 1px; overflow: hidden; min-width: 40px; }}
.cmp-fill {{ height: 100%; border-radius: 1px; }}
.cmp-ship {{ background: #78909c; }}
.cmp-ai {{ background: #7b1fa2; }}
.cmp-model {{ background: #1565c0; }}
.cmp-pct {{ font-size: 9px; color: #666666; width: 32px; text-align: right; flex-shrink: 0; }}
.no-data-cell {{ font-size: 10px; color: #cccccc; font-style: italic; }}

.delta-cell {{ font-weight: 700; font-size: 12px; text-align: center !important; }}
.delta-cell.up {{ color: #1b5e20; }}
.delta-cell.dn {{ color: #b71c1c; }}
.delta-cell.sm {{ font-weight: 500; font-size: 11px; }}
.delta-cell.nodata {{ color: #cccccc; font-weight: 400; font-size: 10px; }}

/* ══════════════════════
   SIDE DRAWER
   ══════════════════════ */
.drawer-inner {{
  width: 440px; height: 100%;
  display: flex; flex-direction: column;
  overflow: hidden;
}}

.drawer-header {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 13px 16px; border-bottom: 2px solid #1a237e;
  flex-shrink: 0; background: #ffffff;
}}
.drawer-header-left {{ display: flex; flex-direction: column; gap: 2px; }}
.drawer-header-title {{ font-size: 13px; font-weight: 700; color: #000000; }}
.drawer-crumb {{ font-size: 10px; color: #999999; }}
.drawer-crumb .crumb-q {{ color: #555555; }}
.drawer-close {{
  border: 1px solid #cccccc; border-radius: 3px; padding: 3px 10px;
  background: #f8f8f8; cursor: pointer; font-size: 11px; font-family: inherit;
  color: #666666; flex-shrink: 0;
}}
.drawer-close:hover {{ background: #eeeeee; }}

.drawer-body {{ flex: 1; overflow-y: auto; padding: 14px 16px; }}

/* Empty state */
.drawer-empty {{
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 100%; color: #999999; font-size: 12px; font-style: italic;
  gap: 10px; text-align: center; padding: 30px;
}}
.drawer-empty-icon {{ font-size: 28px; color: #cccccc; }}

/* Run tabs */
.run-tabs {{ display: flex; gap: 0; margin-bottom: 12px; border-bottom: 2px solid #cccccc; }}
.run-tab {{
  padding: 5px 12px; font-size: 11px; font-weight: 500; color: #666666;
  cursor: pointer; border: 1px solid #cccccc; border-bottom: none;
  background: #f8f8f8; margin-right: 3px; border-radius: 3px 3px 0 0;
}}
.run-tab:hover {{ background: #eeeeee; color: #000000; }}
.run-tab.active {{ background: #1a237e; color: #ffffff; border-color: #1a237e; }}
.run-dot {{
  display: inline-block; width: 7px; height: 7px; border-radius: 50%;
  margin-left: 5px; vertical-align: middle;
}}
.dot-ac {{ background: #2e7d32; }}
.dot-inc {{ background: #1565c0; }}
.dot-ns {{ background: #e65100; }}
.dot-incorr {{ background: #b71c1c; }}

/* Score badge */
.score-badge {{
  display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px;
  border-radius: 3px; font-size: 12px; font-weight: 600; margin-bottom: 12px;
  border: 1px solid #cccccc;
}}
.badge-ac {{ background: #e8f5e9; color: #1b5e20; border-color: #a5d6a7; }}
.badge-inc {{ background: #e3f2fd; color: #0d47a1; border-color: #90caf9; }}
.badge-ns {{ background: #fff3e0; color: #e65100; border-color: #ffcc80; }}
.badge-incorr {{ background: #ffebee; color: #b71c1c; border-color: #ef9a9a; }}

/* Question block */
.q-block {{
  background: #f5f5f5; border-left: 3px solid #9fa8da; padding: 9px 12px;
  margin-bottom: 12px; font-size: 12px; color: #555555; border-radius: 0 3px 3px 0;
  line-height: 1.6;
}}
.q-block-label {{
  font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
  color: #999999; display: block; margin-bottom: 4px;
}}

/* Response block */
.resp-block {{
  border: 1px solid #e0e0e0; border-radius: 4px; padding: 12px;
  margin-bottom: 12px; font-size: 12px; line-height: 1.75; color: #333333;
  max-height: 280px; overflow-y: auto; background: #ffffff;
  white-space: pre-wrap;
}}
.resp-label {{
  font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
  color: #999999; display: block; margin-bottom: 8px;
}}

/* Criteria */
.crit-section {{ margin-bottom: 4px; }}
.crit-heading {{
  font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
  color: #666666; margin-bottom: 6px;
}}
.crit-list {{ list-style: none; display: flex; flex-direction: column; gap: 4px; }}
.crit-list li {{
  font-size: 11px; display: flex; align-items: flex-start;
  gap: 6px; line-height: 1.45;
}}
.ci {{ flex-shrink: 0; font-size: 11px; margin-top: 1px; }}
.ci-met {{ color: #2e7d32; }}
.ci-missed {{ color: #b71c1c; }}
.crit-missed-text {{ color: #b71c1c; text-decoration: line-through; }}

/* Print */
@media print {{
  .controls-bar, .drawer-col {{ display: none !important; }}
  .row-company, .row-model {{ display: table-row !important; }}
  .page-header {{ position: static; }}
}}
</style>
</head>
<body>

<!-- PAGE HEADER -->
<div class="page-header">
  <div>
    <div class="page-header-title">AI vs SHIP Score Comparison</div>
    <div class="page-header-meta">
      Generated {generated_at} &nbsp;·&nbsp; {total_models} AI models &nbsp;·&nbsp; {total_runs} runs
    </div>
  </div>
  <div style="font-size:11px;color:#9fa8da;">
    Dugan et al., JAMA Network Open 2025
  </div>
</div>

<div class="disclaimer">
  {disclaimer_html}
</div>

<!-- MAIN LAYOUT -->
<div class="app-layout">

  <!-- MATRIX COLUMN -->
  <div class="matrix-col">

    <div class="section-heading" style="margin-top:16px;">
      Question-Level Accuracy
    </div>
    <div class="section-meta">
      SHIP counselor baseline (gray) vs All AI models (purple) per question.
      Expand questions to see company and model breakdowns.
      Click a model row to view its verbatim response.
    </div>

    <!-- Controls -->
    <div class="controls-bar">
      <div class="model-toggle-wrap">
        <span class="toggle-lbl toggle-active" id="lbl-hide">Hide Models</span>
        <label class="toggle-pill">
          <input type="checkbox" id="model-toggle" onchange="globalToggle(this.checked)">
          <div class="toggle-track"><div class="toggle-knob"></div></div>
        </label>
        <span class="toggle-lbl" id="lbl-show">Show All Models</span>
      </div>
      <div class="ctrl-divider"></div>
      <span class="ctrl-label">Sort:</span>
      <button class="ctrl-btn active" id="sort-order" onclick="sortMatrix('order', this)">Q# Order</button>
      <button class="ctrl-btn" id="sort-delta" onclick="sortMatrix('delta', this)">&Delta; A&amp;C Size</button>
      <button class="ctrl-btn" id="sort-ship" onclick="sortMatrix('shipAC', this)">SHIP A&amp;C</button>
    </div>

    <!-- Matrix table -->
    <div class="tbl-wrap">
      <table class="mtable" id="main-table">
        <thead>
          <tr>
            <th class="sortable" onclick="sortMatrix('order', document.getElementById('sort-order'))" title="Question number">Q#</th>
            <th>Question / Company / Model</th>
            <th class="sortable" onclick="sortMatrix('aiAC', null)">Accurate &amp;<br>Complete</th>
            <th class="sortable" onclick="sortMatrix('aiInc', null)">Accurate but<br>Incomplete</th>
            <th class="sortable" onclick="sortMatrix('aiNS', null)">Not<br>Substantive</th>
            <th class="sortable" onclick="sortMatrix('aiIncorr', null)">Incorrect</th>
            <th class="sortable" onclick="sortMatrix('delta', document.getElementById('sort-delta'))" title="AI A&amp;C minus SHIP A&amp;C">&Delta; A&amp;C<br><span style="font-size:9px;font-weight:400;">(AI &minus; SHIP)</span></th>
          </tr>
        </thead>
        <tbody id="main-tbody">
          <!-- Rows injected by JS -->
        </tbody>
      </table>
    </div>

  </div><!-- /matrix-col -->


  <!-- DRAWER COLUMN -->
  <div class="drawer-col" id="drawer-col">
    <div class="drawer-inner">

      <div class="drawer-header" id="drawer-header" style="display:none;">
        <div class="drawer-header-left">
          <div class="drawer-header-title" id="drawer-model-name">&mdash;</div>
          <div class="drawer-crumb" id="drawer-crumb"></div>
        </div>
        <button class="drawer-close" onclick="closeDrawer()">&times;</button>
      </div>

      <div class="drawer-empty" id="drawer-empty">
        <div class="drawer-empty-icon">&#9654;</div>
        <div>Click any model row<br>to view its verbatim response</div>
      </div>

      <div class="drawer-body" id="drawer-body" style="display:none;"></div>

    </div>
  </div><!-- /drawer-col -->

</div><!-- /app-layout -->


<script>
// ════════════════════════════════════════
//  REAL DATA (generated {generated_at})
// ════════════════════════════════════════

const SHIP      = {ship_json};
const QUESTIONS = {questions_json};
const COMPANIES = {companies_json};
const CO_SCORES = {co_scores_json};
const MODELS    = {models_json};
const RESPONSES = {responses_json};


// ════════════════════════════════════════
//  HELPERS
// ════════════════════════════════════════

function f(n) {{ return n.toFixed(1) + '%'; }}

function barCell(shipV, aiV, tip, aiN) {{
  if (aiN === 0) {{
    return '<td title="No AI data"><div class="cell-cmp">' +
      '<div class="cmp-row"><span class="cmp-lbl">SHIP</span>' +
      '<div class="cmp-track"><div class="cmp-fill cmp-ship" style="width:' + shipV + '%"></div></div>' +
      '<span class="cmp-pct">' + f(shipV) + '</span></div>' +
      '<div class="cmp-row"><span class="cmp-lbl">AI</span>' +
      '<div class="cmp-track"></div>' +
      '<span class="cmp-pct no-data-cell">—</span></div>' +
      '</div></td>';
  }}
  return '<td title="' + tip + '"><div class="cell-cmp">' +
    '<div class="cmp-row"><span class="cmp-lbl">SHIP</span>' +
    '<div class="cmp-track"><div class="cmp-fill cmp-ship" style="width:' + shipV + '%"></div></div>' +
    '<span class="cmp-pct">' + f(shipV) + '</span></div>' +
    '<div class="cmp-row"><span class="cmp-lbl">AI</span>' +
    '<div class="cmp-track"><div class="cmp-fill cmp-ai" style="width:' + Math.min(aiV,100) + '%"></div></div>' +
    '<span class="cmp-pct">' + f(aiV) + '</span></div>' +
    '</div></td>';
}}

function modelBarCell(shipV, mV, mN, tip) {{
  if (mN === 0) {{
    return '<td title="No data"><span class="no-data-cell">—</span></td>';
  }}
  return '<td title="' + tip + '"><div class="cell-cmp">' +
    '<div class="cmp-row"><span class="cmp-lbl" style="color:#cccccc;font-size:8px;width:30px;">SHIP</span>' +
    '<div class="cmp-track"><div class="cmp-fill cmp-ship" style="width:' + shipV + '%"></div></div>' +
    '<span class="cmp-pct" style="font-size:8px;">' + f(shipV) + '</span></div>' +
    '<div class="cmp-row"><span class="cmp-lbl" style="font-size:8px;width:30px;">model</span>' +
    '<div class="cmp-track"><div class="cmp-fill cmp-model" style="width:' + mV + '%"></div></div>' +
    '<span class="cmp-pct" style="font-size:8px;">' + f(mV) + '</span></div>' +
    '</div></td>';
}}

function deltaCell(d, noData, small) {{
  if (noData) return '<td class="delta-cell nodata">—</td>';
  var s = (d >= 0 ? '+' : '') + d.toFixed(1);
  return '<td class="delta-cell ' + (d >= 0 ? 'up' : 'dn') + (small ? ' sm' : '') + '">' + s + '</td>';
}}

function modelSlug(name) {{ return name.replace(/[^a-z0-9]/gi,'').toLowerCase(); }}


// ════════════════════════════════════════
//  BUILD TABLE
// ════════════════════════════════════════

function buildTable() {{
  var tbody = document.getElementById('main-tbody');
  var html = '';
  var lastSection = null;

  QUESTIONS.forEach(function(q) {{
    var s = SHIP[q.id];
    if (!s) return;

    // Section separator row
    if (q.section !== lastSection) {{
      lastSection = q.section;
      html += '<tr class="row-section" data-rowtype="section">' +
        '<td colspan="7">' + q.section + '</td></tr>';
    }}

    var hasAI = q.aiN > 0;

    // ── Aggregate row ──
    html += '<tr class="row-agg" data-qid="' + q.id + '" data-rowtype="aggregate"' +
      ' data-order="' + q.num + '" data-delta="' + q.delta + '"' +
      ' data-shipAC="' + s.ac + '" data-aiAC="' + q.aiAC + '">' +
      '<td>' + q.num + '</td>' +
      '<td><button class="xbtn" data-qid="' + q.id + '" data-open="false"' +
        ' onclick="toggleQuestion(this,\\'' + q.id + '\\');event.stopPropagation()">+</button>' +
        '<span class="q-label">' + q.label + '</span>' +
        '<span style="font-size:10px;color:#999;margin-left:6px;">SHIP n=' + s.n + (hasAI ? ' · AI n=' + q.aiN : '') + '</span></td>' +
      barCell(s.ac, q.aiAC, 'A&C — SHIP: ' + f(s.ac) + ' | AI: ' + f(q.aiAC), q.aiN) +
      barCell(s.inc, q.aiInc, 'Incomplete — SHIP: ' + f(s.inc) + ' | AI: ' + f(q.aiInc), q.aiN) +
      barCell(s.ns, q.aiNS, 'Not Substantive — SHIP: ' + f(s.ns) + ' | AI: ' + f(q.aiNS), q.aiN) +
      barCell(s.incorrect, q.aiIncorr, 'Incorrect — SHIP: ' + f(s.incorrect) + ' | AI: ' + f(q.aiIncorr), q.aiN) +
      deltaCell(q.delta, !hasAI) +
      '</tr>';

    // ── Company rows ──
    COMPANIES.forEach(function(co) {{
      var cd = (CO_SCORES[co] || {{}})[q.id] || {{n:0,ac:0,inc:0,ns:0,incorrect:0}};
      var coModels = MODELS.filter(function(m){{ return m.company === co; }});
      var coDelta = cd.n > 0 ? cd.ac - s.ac : null;
      html += '<tr class="row-company" data-qid="' + q.id + '" data-company="' + co + '" data-rowtype="company">' +
        '<td></td>' +
        '<td><button class="xbtn" data-qid="' + q.id + '" data-company="' + co + '" data-open="false"' +
          ' onclick="toggleCompany(this,\\'' + q.id + '\\',\\'' + co + '\\');event.stopPropagation()">+</button>' +
          '<span class="co-name">' + co + ' <span class="co-n">(n=' + coModels.length + ')</span></span></td>' +
        modelBarCell(s.ac, cd.ac, cd.n, co + ' A&C: ' + f(cd.ac)) +
        modelBarCell(s.inc, cd.inc, cd.n, co + ' Inc: ' + f(cd.inc)) +
        modelBarCell(s.ns, cd.ns, cd.n, co + ' NS: ' + f(cd.ns)) +
        modelBarCell(s.incorrect, cd.incorrect, cd.n, co + ' Incorr: ' + f(cd.incorrect)) +
        deltaCell(coDelta, cd.n === 0, true) +
        '</tr>';

      // ── Model rows ──
      coModels.forEach(function(m) {{
        var ms = (m.scores || {{}})[q.id] || {{n:0,ac:0,inc:0,ns:0,incorrect:0}};
        var mDelta = ms.n > 0 ? ms.ac - s.ac : null;
        var slug = modelSlug(m.name);
        var key = q.id + '-' + slug;
        html += '<tr class="row-model clickable" data-qid="' + q.id + '"' +
          ' data-company="' + co + '" data-model="' + slug + '" data-rowtype="model"' +
          ' onclick="openDrawer(\\'' + key + '\\',\\'' + m.name + '\\',\\'' + q.id + '\\',this)">' +
          '<td></td>' +
          '<td><div class="model-name">' + m.name +
            ' <span class="model-view-hint">view response</span>' +
          '</div></td>' +
          modelBarCell(s.ac, ms.ac, ms.n, m.name + ' A&C: ' + f(ms.ac)) +
          modelBarCell(s.inc, ms.inc, ms.n, m.name + ' Inc: ' + f(ms.inc)) +
          modelBarCell(s.ns, ms.ns, ms.n, m.name + ' NS: ' + f(ms.ns)) +
          modelBarCell(s.incorrect, ms.incorrect, ms.n, m.name + ' Incorr: ' + f(ms.incorrect)) +
          deltaCell(mDelta, ms.n === 0, true) +
          '</tr>';
      }});
    }});
  }});

  tbody.innerHTML = html;
}}

buildTable();


// ════════════════════════════════════════
//  EXPAND / COLLAPSE
// ════════════════════════════════════════

function toggleQuestion(btn, qId) {{
  var isOpen = btn.dataset.open === 'true';
  document.querySelectorAll('tr[data-qid="' + qId + '"][data-rowtype="company"]')
    .forEach(function(r) {{ r.classList.toggle('visible', !isOpen); }});
  if (isOpen) {{
    document.querySelectorAll('tr[data-qid="' + qId + '"][data-rowtype="model"]')
      .forEach(function(r) {{ r.classList.remove('visible'); }});
    document.querySelectorAll('tr[data-qid="' + qId + '"][data-rowtype="company"] .xbtn')
      .forEach(function(b) {{ b.dataset.open='false'; b.textContent='+'; }});
  }}
  btn.dataset.open = isOpen ? 'false' : 'true';
  btn.textContent  = isOpen ? '+' : '−';
}}

function toggleCompany(btn, qId, company) {{
  var isOpen = btn.dataset.open === 'true';
  document.querySelectorAll('tr[data-qid="' + qId + '"][data-company="' + company + '"][data-rowtype="model"]')
    .forEach(function(r) {{ r.classList.toggle('visible', !isOpen); }});
  btn.dataset.open = isOpen ? 'false' : 'true';
  btn.textContent  = isOpen ? '+' : '−';
}}

function globalToggle(showAll) {{
  document.getElementById('lbl-hide').classList.toggle('toggle-active', !showAll);
  document.getElementById('lbl-show').classList.toggle('toggle-active', showAll);
  if (showAll) {{
    document.querySelectorAll('tr.row-company').forEach(function(r) {{ r.classList.add('visible'); }});
    document.querySelectorAll('tr.row-model').forEach(function(r) {{ r.classList.add('visible'); }});
    document.querySelectorAll('.xbtn').forEach(function(b) {{ b.dataset.open='true'; b.textContent='−'; }});
  }} else {{
    document.querySelectorAll('tr.row-company, tr.row-model').forEach(function(r) {{ r.classList.remove('visible'); }});
    document.querySelectorAll('.xbtn').forEach(function(b) {{ b.dataset.open='false'; b.textContent='+'; }});
  }}
}}


// ════════════════════════════════════════
//  SORT (group-aware — preserves question hierarchy)
// ════════════════════════════════════════

var sortCol = 'order', sortAsc = true;

function sortMatrix(criterion, btnEl) {{
  if (sortCol === criterion) {{ sortAsc = !sortAsc; }} else {{ sortAsc = true; }}
  sortCol = criterion;

  document.querySelectorAll('.ctrl-btn[id^="sort-"]').forEach(function(b) {{ b.classList.remove('active'); }});
  document.querySelectorAll('#main-table th').forEach(function(th) {{ th.classList.remove('sort-asc','sort-desc'); }});
  if (btnEl) {{
    btnEl.classList.add('active');
    btnEl.classList.add(sortAsc ? 'sort-asc' : 'sort-desc');
  }}

  var tbody = document.getElementById('main-tbody');
  var rows  = Array.from(tbody.querySelectorAll('tr'));

  // Group by section, then by aggregate within section
  // Sections stay fixed; within each section, aggregate rows sort and children follow
  var sections = [], curSection = null, curGroup = null;
  rows.forEach(function(r) {{
    if (r.dataset.rowtype === 'section') {{
      curSection = {{ sep: r, groups: [] }};
      sections.push(curSection);
      curGroup = null;
    }} else if (r.dataset.rowtype === 'aggregate') {{
      curGroup = {{ agg: r, children: [] }};
      if (curSection) {{ curSection.groups.push(curGroup); }}
      else {{
        // No section separator — create a fallback section
        curSection = {{ sep: null, groups: [curGroup] }};
        sections.push(curSection);
      }}
    }} else if (curGroup) {{
      curGroup.children.push(r);
    }}
  }});

  var asc = sortAsc;
  sections.forEach(function(sec) {{
    sec.groups.sort(function(a, b) {{
      var av = parseFloat(a.agg.dataset[criterion]);
      var bv = parseFloat(b.agg.dataset[criterion]);
      if (isNaN(av)) av = asc ? Infinity : -Infinity;
      if (isNaN(bv)) bv = asc ? Infinity : -Infinity;
      return asc ? av - bv : bv - av;
    }});
  }});

  // Re-append in new order, keeping sections together
  sections.forEach(function(sec) {{
    if (sec.sep) tbody.appendChild(sec.sep);
    sec.groups.forEach(function(g) {{
      tbody.appendChild(g.agg);
      g.children.forEach(function(c) {{ tbody.appendChild(c); }});
    }});
  }});
}}


// ════════════════════════════════════════
//  SIDE DRAWER
// ════════════════════════════════════════

var activeModelRow = null;

function openDrawer(key, modelName, qId, rowEl) {{
  if (activeModelRow) activeModelRow.classList.remove('active-row');
  activeModelRow = rowEl;
  rowEl.classList.add('active-row');

  document.getElementById('drawer-col').classList.add('open');
  document.getElementById('drawer-empty').style.display  = 'none';
  document.getElementById('drawer-header').style.display = 'flex';
  document.getElementById('drawer-body').style.display   = 'block';

  document.getElementById('drawer-model-name').textContent = modelName;

  var qDef = QUESTIONS.find(function(q) {{ return q.id === qId; }});
  var qLabel = qDef ? qDef.label : qId;
  var qNum   = qDef ? qDef.num  : '';

  var data = RESPONSES[key];
  var runsNote = data && data.runs.length > 1 ? ' &nbsp;&middot;&nbsp; ' + data.runs.length + ' runs' : '';

  document.getElementById('drawer-crumb').innerHTML =
    '<span class="crumb-q">Q' + qNum + ': ' + qLabel + '</span>' + runsNote;

  if (!data || !data.runs || data.runs.length === 0) {{
    document.getElementById('drawer-body').innerHTML =
      '<div style="color:#999;font-style:italic;font-size:12px;padding:20px 0;">' +
      'Response data not yet available for this model and question.</div>';
    return;
  }}

  var tabsHtml = '<div class="run-tabs" id="run-tabs">';
  data.runs.forEach(function(r, i) {{
    tabsHtml += '<div class="run-tab' + (i===0?' active':'') +
      '" onclick="switchRun(' + i + ',this)" data-run="' + i + '">' +
      'Run ' + (i+1) + ' <span class="run-dot dot-' + r.score + '"></span></div>';
  }});
  tabsHtml += '</div>';

  document.getElementById('drawer-body').innerHTML = tabsHtml + '<div id="run-content"></div>';
  renderRun(data, 0);
}}

function switchRun(idx, tabEl) {{
  var key = activeModelRow
    ? (activeModelRow.dataset.qid + '-' + activeModelRow.dataset.model)
    : null;
  if (!key || !RESPONSES[key]) return;
  document.querySelectorAll('#run-tabs .run-tab').forEach(function(t) {{ t.classList.remove('active'); }});
  tabEl.classList.add('active');
  renderRun(RESPONSES[key], idx);
}}

function renderRun(data, idx) {{
  var r = data.runs[idx];
  var met    = (r.met    || []).map(function(c) {{
    return '<li><span class="ci ci-met">&#10003;</span><span>' + escHtml(c) + '</span></li>';
  }}).join('');
  var missed = (r.missed || []).map(function(c) {{
    return '<li><span class="ci ci-missed">&#10007;</span><span class="crit-missed-text">' + escHtml(c) + '</span></li>';
  }}).join('');
  var total    = (r.met||[]).length + (r.missed||[]).length;
  var metCount = (r.met||[]).length;
  var criteriaSection = total > 0
    ? '<div class="crit-section"><div class="crit-heading">Criteria &mdash; ' + metCount + ' / ' + total + ' met</div>' +
      '<ul class="crit-list">' + met + missed + '</ul></div>'
    : '';

  document.getElementById('run-content').innerHTML =
    '<div class="score-badge badge-' + r.score + '" style="margin-bottom:12px;">' +
      '&#9679; ' + escHtml(r.scoreLabel) +
    '</div>' +
    '<div class="resp-block"><span class="resp-label">Verbatim AI response</span>' +
      escHtml(r.response) +
    '</div>' +
    criteriaSection;
}}

function closeDrawer() {{
  document.getElementById('drawer-col').classList.remove('open');
  document.getElementById('drawer-empty').style.display  = '';
  document.getElementById('drawer-header').style.display = 'none';
  document.getElementById('drawer-body').style.display   = 'none';
  document.getElementById('drawer-body').innerHTML       = '';
  if (activeModelRow) {{ activeModelRow.classList.remove('active-row'); activeModelRow = null; }}
}}

function escHtml(s) {{
  return String(s)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}}
</script>
</body>
</html>"""


# ============================================================================
# Main
# ============================================================================

def generate_matrix_report(
    runs_dir: Path = Path("runs"),
    output_path: Path = Path("reports/matrix_report.html"),
    exclude_back: bool = True,
) -> None:
    print("Generating AI vs SHIP matrix report...")
    print(f"  Loading runs from: {runs_dir}")

    if not runs_dir.exists() or not runs_dir.is_dir():
        print(f"Error: Runs directory does not exist: {runs_dir}", file=sys.stderr)
        sys.exit(1)

    # Load and filter results
    results = load_all_results(runs_dir)
    print(f"  Loaded {len(results)} total runs")

    results = filter_fake_models(results)

    if exclude_back:
        results = [r for r in results if not r.get("_source_dir", "").startswith("Back")]

    results = [r for r in results if r.get("grading", {}).get("question_scores")]

    ALLOWED_SCENARIOS = {"SHIP-MO-ALL", "SHIP-DE-ALL"}
    results = [r for r in results if r.get("scenario_id") in ALLOWED_SCENARIOS]
    print(f"  After filtering: {len(results)} runs with grading data")

    if not results:
        print("Error: No runs with grading data found.", file=sys.stderr)
        sys.exit(1)

    # Load question mapping
    mapping_path = (
        Path(__file__).parent.parent / "reference_material" / "etable3_question_mapping.json"
    )
    if not mapping_path.exists():
        print(f"Error: Question mapping not found: {mapping_path}", file=sys.stderr)
        sys.exit(1)
    with open(mapping_path) as f:
        mapping = json.load(f)

    # Count distinct models
    all_models = {r.get("target", {}).get("model_name", "") for r in results if r.get("target")}
    all_models.discard("")

    # Build JS data
    js_data = build_js_data(results, mapping)

    # Generate HTML
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = generate_html(
        js_data=js_data,
        generated_at=generated_at,
        total_runs=len(results),
        total_models=len(all_models),
        ethics_disclaimer=ETHICS_DISCLAIMER,
    )

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = output_path.stat().st_size / 1024
    print(f"\n  Report generated successfully")
    print(f"  Output: {output_path}")
    print(f"  Size:   {size_kb:.1f} KB")
    print(f"  Models: {len(all_models)}")
    print(f"  Runs:   {len(results)}")
    print(f"  Questions: {len(js_data['questions'])}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate AI vs SHIP comparison matrix HTML report",
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
        default=Path("reports/matrix_report.html"),
        help="Output HTML file path (default: reports/matrix_report.html)",
    )
    parser.add_argument(
        "--include-back",
        action="store_true",
        help="Include runs from Back/ directory (default: excluded)",
    )

    args = parser.parse_args()
    generate_matrix_report(
        runs_dir=args.runs_dir,
        output_path=args.output,
        exclude_back=not args.include_back,
    )

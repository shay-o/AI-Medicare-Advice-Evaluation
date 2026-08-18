"""Factorial experiment: does a better model, a better harness, or both fix the grader?

Design
  models   : claude-3-haiku (incumbent), gemini-3-flash, claude-sonnet-4.5
  harness  : BARE    = no plan facts (grader works from parametric memory)
             GROUNDED = plan facts + mandatory verbatim-quote step
  replicates: 3 per cell, temperature 0, so spread reflects real provider
             nondeterminism rather than sampling temperature

Metrics
  accuracy        : agreement with the gold label, averaged over replicates
  self-consistency: fraction of items where all 3 replicates gave the same verdict
  spread          : max-min accuracy across replicates

Gold labels are either a hard rubric category, or NOT_incorrect meaning any verdict
except 'incorrect' is acceptable (used where the response is factually right and the
only defensible failure is calling it wrong).
"""
import asyncio
import json
import os
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime

from dotenv import load_dotenv

ROOT = "/Users/jamesoreilly/Documents/Projects/AI-Medicare-Advice-Evaluator"
SCRATCH = "reference_material"
sys.path.insert(0, ROOT)
os.chdir(ROOT)
load_dotenv(".env")

from src.grader import MedicareAdviceGrader  # noqa: E402
from src.orchestrator import create_adapter, render_plan_facts  # noqa: E402
from src.schemas import Scenario  # noqa: E402

GOLD = json.load(open("reference_material/grader_gold_set_v1.json"))
FACTS = render_plan_facts(
    Scenario(**json.load(open("scenarios/medicare_only/all_questions.json"))).plan_information)

MODELS = [
    ("haiku", "anthropic/claude-3-haiku"),
    ("gemini-3-flash", "google/gemini-3-flash-preview"),
    ("sonnet-4.5", "anthropic/claude-sonnet-4.5"),
]
HARNESS = [("BARE", None), ("GROUNDED", FACTS)]
REPS = 3


def correct(verdict, gold):
    if gold == "NOT_incorrect":
        return verdict != "incorrect"
    return verdict == gold


async def run_cell(mname, mslug, hname, facts, rep, sem):
    grader = MedicareAdviceGrader(adapter=create_adapter("openrouter", mslug), plan_facts=facts)
    out = []

    async def one(item):
        async with sem:
            for a in range(3):
                try:
                    qs = await grader.grade_response(
                        question_number=item["qnum"], question_text=item["qtext"],
                        response_text=item["response"], scenario=item["scenario"])
                    v = qs.score.value if hasattr(qs.score, "value") else str(qs.score)
                    return {"group": item["group"], "gold": item["gold"], "verdict": v,
                            "ok": correct(v, item["gold"])}
                except Exception as e:
                    if a == 2:
                        return {"group": item["group"], "gold": item["gold"],
                                "verdict": None, "ok": None, "error": str(e)[:120]}
                    await asyncio.sleep(2 * (a + 1))

    out = await asyncio.gather(*(one(i) for i in GOLD))
    return {"model": mname, "harness": hname, "rep": rep, "results": out}


async def main():
    sem = asyncio.Semaphore(5)
    jobs = [run_cell(mn, ms, hn, hf, r, sem)
            for mn, ms in MODELS for hn, hf in HARNESS for r in range(REPS)]
    print(f"running {len(jobs)} cells x {len(GOLD)} items = {len(jobs)*len(GOLD)} calls\n")
    cells = await asyncio.gather(*jobs)

    by = defaultdict(list)
    for c in cells:
        by[(c["model"], c["harness"])].append(c)

    print(f"{'model':16}{'harness':11}{'accuracy':>10}{'spread':>9}{'self-consist':>14}{'errors':>8}")
    print("-" * 70)
    summary = {}
    for (mn, hn), cs in by.items():
        accs = []
        for c in cs:
            good = [r for r in c["results"] if r["ok"] is not None]
            accs.append(100.0 * sum(r["ok"] for r in good) / len(good) if good else 0.0)
        # self-consistency: all reps identical verdict per item
        per_item = defaultdict(list)
        for c in cs:
            for i, r in enumerate(c["results"]):
                per_item[i].append(r["verdict"])
        consist = 100.0 * sum(1 for v in per_item.values() if len(set(v)) == 1) / len(per_item)
        errs = sum(1 for c in cs for r in c["results"] if r["ok"] is None)
        mean = statistics.mean(accs)
        spread = max(accs) - min(accs)
        summary[f"{mn}|{hn}"] = {"accuracy_mean": round(mean, 1),
                                 "accuracy_reps": [round(a, 1) for a in accs],
                                 "spread": round(spread, 1),
                                 "self_consistency": round(consist, 1), "errors": errs}
        print(f"{mn:16}{hn:11}{mean:9.1f}%{spread:8.1f}{consist:13.1f}%{errs:8}")

    print("\nfailures by question group (GROUNDED harness, all models, all reps):")
    fails = Counter()
    for c in cells:
        if c["harness"] != "GROUNDED":
            continue
        for r in c["results"]:
            if r["ok"] is False:
                fails[f"{c['model']}/{r['group']}"] += 1
    for k, v in fails.most_common(12):
        print(f"  {k:34} x{v}")

    out = "reference_material/grader_experiment_results.json"
    json.dump({"generated": datetime.now().isoformat(), "n_items": len(GOLD),
               "reps": REPS, "summary": summary, "cells": cells}, open(out, "w"), indent=1)
    print(f"\nwritten to {out}")


asyncio.run(main())

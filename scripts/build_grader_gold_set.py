"""Gold set v2. Fixes v1's precedence bug.

v1 labelled a response asserting "Yes, the plan includes Part D" as not_substantive,
because a refusal phrase appeared later in the text. A false factual assertion is an
error regardless of hedging that follows it, so factual polarity must be checked FIRST.

Verified facts (reference_material/plan_facts_H5521-369-0_2026.json):
  includes_drug_coverage = FALSE   (MA-only plan, no Part D, no formulary)
  out_of_network_allowed = TRUE    (it is a PPO)

Label families, in priority order:
  B  false factual assertion              -> incorrect
  B' correct factual assertion            -> NOT_incorrect (any verdict but 'incorrect')
  A  pure refusal, no substantive claim   -> not_substantive

Anything that does not fall cleanly into one of these is excluded rather than guessed.
"""
import json
import os
import re
from collections import Counter

ROOT = "/Users/jamesoreilly/Documents/Projects/AI-Medicare-Advice-Evaluator"
os.chdir(ROOT)
OUT = "reference_material/grader_gold_set_v1.json"

man = json.load(open("reported_runs.json"))
R = man["selection_rules"]
ALLOWED, EXCLUDED, LABELS = set(R["allowed_scenario_ids"]), set(R["excluded_group_ids"]), set(R["rubric_labels"])

rows = []
for r in man["runs"]:
    p = f"runs/{r['run_dir']}/results.jsonl"
    if not os.path.exists(p):
        continue
    for line in open(p):
        rec = json.loads(line)
        sid = rec.get("scenario_id")
        if sid not in ALLOWED:
            continue
        for qs in (rec.get("grading") or {}).get("question_scores", []):
            g = qs.get("group_id")
            if g in EXCLUDED or g == "Error" or qs.get("score") not in LABELS:
                continue
            rows.append({"group": g, "qnum": qs["question_number"],
                         "scenario": "dual_eligible" if "-DE-" in sid else "medicare_only",
                         "qtext": qs["question_text"], "response": qs["response_text"],
                         "published": qs["score"]})

REFUSAL = re.compile(r"(i cannot provide|i can'?t provide|i cannot verify|i can'?t verify|"
                     r"cannot confirm|can'?t confirm|i don'?t have access|i do not have access|"
                     r"i'?m unable to|i am unable to|i don'?t know)", re.I)
CONCRETE = re.compile(r"\$\s?[\d,]+(\.\d\d)?")


def qg19_polarity(t):
    low = t.lower()
    yes = re.search(r"(yes[,.\s]|does include|includes (medicare )?part d|"
                    r"includes prescription drug coverage|typically includes)", low)
    no = re.search(r"(does not include|doesn'?t include|not include (medicare )?part d|"
                   r"without (part d|prescription drug)|no part d|ma-only|"
                   r"does not (offer|provide) (prescription|drug))", low)
    if yes and not no:
        return "yes"
    if no and not yes:
        return "no"
    return None


def qg16_polarity(t):
    low = t.lower()
    yes = re.search(r"(yes[,.\s].{0,80}(out.of.network|outside)|can (go|see).{0,40}out.of.network|"
                    r"covers out.of.network|out.of.network.{0,40}(is )?covered|"
                    r"allows? you to (go|see))", low)
    no = re.search(r"(does not cover out.of.network|no out.of.network coverage|"
                   r"only.{0,30}in.network|must (stay|use).{0,30}in.network)", low)
    if yes and not no:
        return "yes"
    if no and not yes:
        return "no"
    return None


gold = []
for r in rows:
    body, head = r["response"], r["response"][:400]

    # --- Priority 1: checkable factual assertions ---
    if r["group"] == "QG19":
        pol = qg19_polarity(body)
        if pol == "yes":
            gold.append({**r, "gold": "incorrect", "family": "B-false",
                         "rule": "asserts plan INCLUDES Part D; verified: it does NOT"})
            continue
        if pol == "no":
            gold.append({**r, "gold": "NOT_incorrect", "family": "B-true",
                         "rule": "correctly says plan does NOT include Part D"})
            continue

    if r["group"] == "QG16":
        pol = qg16_polarity(body)
        if pol == "no":
            gold.append({**r, "gold": "incorrect", "family": "B-false",
                         "rule": "denies out-of-network coverage; verified: PPO, it IS covered"})
            continue
        if pol == "yes":
            gold.append({**r, "gold": "NOT_incorrect", "family": "B-true",
                         "rule": "correctly says out-of-network IS covered"})
            continue

    # --- Priority 2: pure refusal (no substantive claim, no figure) ---
    if REFUSAL.search(head) and not CONCRETE.search(body):
        # exclude if it still answers a yes/no question substantively
        if not re.match(r"\s*(yes|no)\b", body, re.I):
            gold.append({**r, "gold": "not_substantive", "family": "A-refusal",
                         "rule": "explicit refusal, no concrete figure, no yes/no answer"})
            continue

seen, uniq = set(), []
for g in gold:
    k = (g["group"], g["qnum"], hash(g["response"]))
    if k not in seen:
        seen.add(k)
        uniq.append(g)

json.dump(uniq, open(OUT, "w"), indent=1)

print(f"pool {len(rows)} -> gold {len(uniq)}")
print("family:", dict(Counter(g["family"] for g in uniq)))
print("group :", dict(Counter(g["group"] for g in uniq)))

hard = [g for g in uniq if g["gold"] in LABELS]
soft = [g for g in uniq if g["gold"] == "NOT_incorrect"]
print(f"\npublished grader vs gold:")
print(f"  hard labels agreed: {sum(1 for g in hard if g['published']==g['gold'])}/{len(hard)}")
print(f"  wrongly 'incorrect' on true answers: {sum(1 for g in soft if g['published']=='incorrect')}/{len(soft)}")

print("\n--- FULL GOLD SET FOR REVIEW ---")
for i, g in enumerate(uniq, 1):
    print(f"\n{i:2}. [{g['group']}] gold={g['gold']:15} published={g['published']}")
    print(f"    why: {g['rule']}")
    print(f"    A: {g['response'][:150].strip()!r}")

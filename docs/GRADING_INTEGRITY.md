# Grading integrity: answer-key defect in the plan-specific questions

**Status:** open — affects 7 of 19 scored questions
**Found:** 2026-07-25, during a judge-validation pass
**Severity:** the plan-specific results are not citable until this is fixed. The general-rules results are unaffected.

---

## Summary

Seven of the nineteen scored question groups ask about attributes of a **specific, really-existing Medicare Advantage plan** — "Aetna Medicare Eagle PPO". The answer key for those questions lives in `scenarios/medicare_only/all_questions.json` under `plan_information`, and several of its values **contradict the real plan**. Models are asked about the plan by name and are given no plan data, so they answer from parametric knowledge of the real plan — and get graded against attributes the real plan does not have.

Compounding this, the grading agent does not apply the key consistently: on one question it graded every model against real-world facts (ignoring the key), and on another it graded models against the key (contradicting real-world facts). Both cannot be right.

## Evidence

### 1. The key contradicts the real plan

`scenarios/medicare_only/all_questions.json` describes the plan as:

| Field | Value in answer key | Real plan |
| --- | --- | --- |
| `includes_drug_coverage` | `true` | **false** — Eagle is Aetna's MA-only line, sold specifically without Part D |
| `drug_formulary` | Lipitor covered, tier 3, $47 copay | **n/a** — no Part D formulary exists for an MA-only plan |
| `out_of_network_allowed` | `false` | **true** — it is a PPO; out-of-network care is covered at higher cost |

Sources: [US News lists Aetna Medicare Eagle (PPO) under Medicare Advantage plans *without* drug coverage](https://health.usnews.com/medicare/aetna-medicare-medicare-advantage-plans-without-drug-coverage/aetna-medicare-eagle-ppo--493-0-H5521); [CVS Health describes the Eagle plans as MA-only](https://www.cvshealth.com/news/medicare/aetna-2025-medicare-plans-focus-on-most-important-health-needs-for-members.html); [Aetna Medicare Eagle Plan summary of benefits (NC DOI)](https://www.ncdoi.com/SHIIPCurrentYear/Documents/MA%20Summary%20Of%20Benefits/Aetna%20Medicare%20Eagle%20Plan%20H5521-241%20(PPO).pdf).

### 2. The models are given no plan data

The scenario asks bare questions — "Does Aetna Medicare Eagle PPO include prescription drug coverage?", "What is the monthly premium for Aetna Medicare Eagle PPO?" — with no plan document, no retrieval, and no context block. Verified by inspecting `conversation[]` in `runs/*/results.jsonl`: no user turn carries `plan_information`.

The repo does contain `scenarios/medicare_only/example_with_plan_info.json`, which describes plan information as being "used for question substitution and answer verification". That mode is not what the reported runs used. So `plan_information` is functioning purely as a hidden answer key, against a plan the model is expected to know from training data.

### 3. The judge applies the key inconsistently

**Question: "Would Aetna Medicare Eagle PPO let me go out of network?"**
Key says `out_of_network_allowed: false`. All nine models answered *yes, it is a PPO, out-of-network is covered at higher cost*. All nine were graded **accurate_complete**. → the judge used real-world knowledge and ignored the key.

**Question: "Does Aetna Medicare Eagle PPO include prescription drug coverage?"**
Key says `includes_drug_coverage: true`. Gemini-3-flash and Gemini-3-pro answered *no, it is an MA-only plan* — which is correct in reality — and were graded **incorrect**. → the judge used the key and ignored real-world knowledge.

**Same question, third failure mode:** Claude-3.5-sonnet answered *yes, it typically includes drug coverage*, which **matches the key**, and was still graded **incorrect** — with a written rationale asserting the plan "specifically does NOT include Part D". The judge scored against a fact that appears in neither the key nor its own verdict on the neighbouring question.

All four `incorrect` verdicts in the entire evaluation come from this one plan-coverage question and its Lipitor follow-up.

## Blast radius

Verified with `scripts/verify_headline_numbers.py`:

| Slice | n | Accurate & complete | Incomplete | Not substantive | Incorrect |
| --- | --- | --- | --- | --- | --- |
| All 19 questions (published) | 180 | 65.0% | 25.0% | 7.8% | 2.2% |
| General-rules questions (12) | 117 | 84.6% | 15.4% | 0.0% | 0.0% |
| Plan-specific questions (7) | 63 | 28.6% | 42.9% | 22.2% | 6.3% |

**The general-rules half is clean.** It contains no plan-specific answer key, no `incorrect` verdicts, and no `not_substantive` verdicts.

**The plan-specific half is where every questionable verdict lives.** Note that most of its verdicts are still directionally safe: `not_substantive` and `substantive_incomplete` verdicts record that the model declined or hedged, and a model declining to answer is a fact about the model, not about the key. The verdicts that the defect actually corrupts are the `accurate_complete` and `incorrect` ones, where the key's content decides the outcome.

## Recommended fix

Pick one of two coherent designs — the current setup is an incoherent blend of both:

1. **Closed-book, real plan (tests parametric knowledge).** Keep the real plan name, and correct `plan_information` to match the real plan's published benefits for a stated plan year and county. Re-grade. This measures whether models know real plan details — a fair question, given they will be asked it.
2. **Open-book, fictional plan (tests retrieval and reading).** Rename to an unambiguously fictional plan ("Sample PPO Plan A"), pass `plan_information` to the model in context, and grade against it. This measures whether a model can correctly read plan documents — which is what a real benefits-navigation product would actually do.

Option 2 is the better fit for the project's stated thesis, because it maps onto how a deployed product would work (retrieval over authoritative plan data). Option 1 is cheaper and preserves comparability with the SHIP baseline, since the human counsellors were answering about real plans.

Either way:
- Make the judge's grounding explicit in the prompt: tell it whether the key or real-world knowledge is authoritative, and have it cite which it used.
- Re-run and re-grade the seven plan-specific questions.
- Re-publish, and keep this document as the record of what changed and why.

**Blocked on:** re-running requires a live `OPENROUTER_API_KEY`; the previous key is expired.

## Why this is in the repo rather than quietly fixed

The finding came out of a deliberate judge-validation pass — the practice of checking whether the grader is right before trusting what it grades. An evaluation harness whose failures are documented is more trustworthy than one that reports only clean numbers, and the general-rules results stand on their own. The correct response to a grader error is to publish it, bound it, and fix it.

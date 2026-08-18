# Grading integrity: a hardcoded answer key in the rubric

**Status:** diagnosed and fixed in code on 2026-08-17. Re-grade of the stored responses in progress.
**First found:** 2026-07-25, during a judge-validation pass
**Corrected diagnosis:** 2026-08-17. The first diagnosis identified the wrong mechanism. Both the original finding and the correction are kept below, because how the diagnosis moved is part of the record.

---

## Summary

Two of the nineteen scored question groups were graded against an answer key that contradicts the real plan the question names. Models that gave the **correct** answer were marked `incorrect`, and at least one model that gave the **wrong** answer was marked `accurate_complete`.

The defective key was hardcoded in the grading rubric itself (`src/grading_rubric.py`), not in the scenario file. The general-rules questions are unaffected.

## The corrected diagnosis

### What the original version of this document claimed

That `plan_information` in `scenarios/medicare_only/all_questions.json` was serving as a hidden answer key, that its values contradicted the real plan, and that the grading agent applied it inconsistently.

### Why that was wrong

**The grader never receives `plan_information`.** `MedicareAdviceGrader.grade_run()` takes only `run_id`, a list of `{question_number, question_text, response_text}`, and a scenario name string. There is no reference to `plan_information` anywhere in `src/grader.py`. Its only runtime use was substituting `[plan name]` into question text.

So correcting those values could not, on its own, have changed a single verdict. The first diagnosis identified real bad data, but attributed a causal role to it that the code does not support.

### What was actually wrong

The answer key lived in the **rubric criteria**, which the grader does read. Before the fix, `src/grading_rubric.py` QG19 read:

```python
accurate_complete_criteria=[
    "Counselor says yes (plan includes prescription drug coverage)"
],
incorrect_criteria=[
    "Counselor said no or otherwise provided incorrect information ..."
]
```

The plan in question, Aetna Medicare Eagle (PPO) H5521-369-0, is Aetna's MA-only product and has **no** Part D coverage. So the rubric instructed the grader that the correct answer was the false one.

These rubrics are transcribed from the study's eAppendix 4, where they were written for the plan the original mystery shoppers asked about. When this project substituted a different real plan, the plan-specific answers embedded in the rubric text came along and silently became wrong.

### Evidence from the run data

Grader rationales from `runs/*/results.jsonl`, QG19:

> "The response explicitly states that the Aetna Medicare Eagle PPO does NOT include prescription drug coverage, which is the opposite of what would be required for an accurate response **according to the rubric**." → graded `incorrect`

That model was right about the real world and was penalised for it.

> "The response clearly and definitively answers the core question by stating that Aetna Medicare Eagle PPO **includes** prescription drug coverage." → graded `accurate_complete`

That model was wrong about the real world and was rewarded for it.

A third rationale went the other way, asserting from the grader's own knowledge that the plan "specifically does NOT include prescription drug coverage." The grader was oscillating between the rubric text and its own parametric memory, with nothing authoritative to anchor on.

### Blast radius

Comparing every plan-specific group against the real plan:

| Group | Hardcoded rubric answer | Matches reality? |
| --- | --- | --- |
| QG17 in-network PCP copay | "copay is $0" | yes, $0. Harmless but fragile |
| QG19 drug coverage | "says yes" | **no.** Plan has no Part D |
| QG20 Lipitor | "not covered but generic is" | **no.** No formulary exists |
| QG14, QG15, QG16, QG18, QG23 | already plan-agnostic | not affected |

So **two** questions were corrupted, not seven. This matches the original document's own observation that every `incorrect` verdict in the evaluation traced to the drug-coverage question and its Lipitor follow-up.

## Second defect: the grader had no ground truth

Even with correct rubric text, questions like "what is the premium" or "is this drug covered" are only decidable against real plan data. The grader was given none, so it answered from memory. That is why neighbouring questions received contradictory treatment.

## What was fixed (2026-08-17)

1. **`src/grading_rubric.py`** QG17, QG19 and QG20 rewritten to be plan-agnostic. They now judge against a `PLAN FACTS` section rather than asserting one plan's answers. QG20 needed more than the `eval_dataset` version already had: that version still marks "neither Lipitor nor its generic is covered" as `incorrect`, which is the *true* answer for a plan with no drug coverage.

2. **`src/grader.py`** now accepts `plan_facts` and renders an explicit `PLAN FACTS (authoritative ground truth)` block into the grading prompt, instructing the grader to prefer it over its own recollection and to state that a fact is missing rather than guess.

3. **`src/orchestrator.py`** gained `render_plan_facts()`, which builds that block from the scenario. It returns `None` when a scenario names no plan, leaving those scenarios unchanged.

4. **`scenarios/medicare_only/all_questions.json`** `plan_information` corrected from invented values to sourced ones. This does not affect grading by itself, but it is what now feeds `PLAN FACTS`, and false data should not sit in the repo regardless.

| Field | Was (invented) | Now (sourced) |
| --- | --- | --- |
| `monthly_premium` | 25.00 | 0.00 |
| `part_b_premium` | 174.70 (2024 figure) | 202.90 (2026) |
| `max_out_of_pocket` | 3400.00 | 6750.00 |
| `out_of_network_allowed` | false | true (it is a PPO) |
| `includes_drug_coverage` | true | false |
| `drug_formulary` | invented Lipitor/atorvastatin entries | null, no formulary exists |
| `requires_referrals` | true | false |

5. **`reference_material/plan_facts_H5521-369-0_2026.json`** added, carrying a source URL, retrieval date and confidence level for every field. Fields that could not be verified are recorded as `unverified` rather than filled in.

## Verification

Re-grading the 18 stored QG19 and QG20 responses with the corrected rubric and `PLAN FACTS` reverses the defect in both directions:

- `incorrect` → `accurate_complete` (x3): correct "no drug coverage" answers, previously punished
- `accurate_complete` → `incorrect` (x1): a false "yes, it includes Part D" answer, previously rewarded

**Caveat worth stating plainly:** 15 of those 18 verdicts changed. That is not all bug-fixing. The new QG20 criteria are genuinely stricter, requiring a response to note that separate Part D coverage would be needed. The re-grade is therefore part correction and part rubric change, and should be described that way rather than presented purely as fixing an error.

## Open items

- **Full re-grade of all 180 responses is in progress.** The corrected headline is not yet known. Until it is, the published 65.0% figure stands as the number produced by the old grading, and the two affected questions are inside it.
- **Published pages are deliberately untouched.** `reported_runs.json` and `reports/` are unchanged, so the re-grade lands as separate evidence rather than silently replacing the reported set.
- **Plan facts need confirmation against Medicare.gov Plan Finder**, which is the source the SHIP rubric names. It was not directly reachable during retrieval (q1medicare returned 403, US News timed out), so current values are triangulated from independent aggregators.
- **Plan naming is a confound.** Contract H5521-369 was marketed as "Aetna Medicare Eagle Plus (PPO)" in 2025 and "Aetna Medicare Eagle (PPO)" in 2026. Models are asked about the plan by name, so they may answer about a different year's product.
- **QG14 asks whether a named physician is in network.** That is not resolvable from public plan data and concerns a real, identifiable individual. Either use an obviously fictional name or score only whether the response correctly directs the beneficiary to the plan's provider directory.
- **Four of the nine evaluated models are no longer available on OpenRouter** (`anthropic/claude-3.5-sonnet`, `google/gemini-3-pro-preview`, `x-ai/grok-4`, `x-ai/grok-4.1-fast`), and `openai/gpt-5.2-chat` is listed but returns no endpoints. The original 9-model set can no longer be reproduced.

## Why this is in the repo rather than quietly fixed

The finding came out of a deliberate judge-validation pass, the practice of checking whether the grader is right before trusting what it grades. An evaluation harness whose failures are documented is more trustworthy than one that reports only clean numbers.

That applies to this document too. Its first version confidently identified the wrong mechanism and proposed a choice between two designs, when the actual bug was a hardcoded string in a rubric file and the actual fix was to stop the rubric asserting plan-specific answers. Publishing the correction is the same discipline as publishing the original finding.

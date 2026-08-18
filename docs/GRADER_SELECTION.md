# Choosing a grader: model versus harness

An experiment to answer three questions. How often does the grading model get it wrong? Does a stronger model fix it? Does a better prompt fix it, and is that a substitute for a stronger model?

Run 2026-08-17. Total cost $1.50 for 324 grading calls.

---

## Why this was needed

Grading used `anthropic/claude-3-haiku`, chosen for cost. Two separate defects had already been traced partly to grader weakness: contradictory verdicts on neighbouring questions, and accepting a stated out-of-pocket range of "$4,000 to $6,000" as matching an actual value of $6,750, which lies outside it. That raised an obvious question the project had never answered: how much of the reported error is the models under test, and how much is the instrument?

## The hard part: ground truth

Measuring how often a grader fails requires knowing the correct verdict. The grader cannot supply that. So a gold set was built from the 180 reported responses, restricted to items where the correct verdict is unambiguous, with the labelling rule recorded per item so any label can be audited or overturned:

| Family | Rule | Gold label |
| --- | --- | --- |
| Refusal | Explicit "I cannot provide", no concrete figure, no yes/no answer | `not_substantive` |
| False assertion | Claims the plan includes Part D (verified: it does not), or denies out-of-network coverage on a PPO | `incorrect` |
| True assertion | Correctly states the plan has no Part D, or that out-of-network is covered | `NOT_incorrect` (any verdict except calling a right answer wrong) |

18 of 180 items met that bar. Anything arguable was excluded rather than guessed.

**The first version of the gold set was wrong.** Rule ordering meant a response saying *"Yes, the plan includes Part D... however I cannot provide specific details"* was labelled `not_substantive`, because a refusal phrase appeared after the false claim. A false factual assertion is an error regardless of subsequent hedging. Checking factual polarity before refusal fixed it. A bad gold set produces a confident, meaningless experiment, so this is the step most worth double-checking.

## Design

- **Models:** `claude-3-haiku` (incumbent), `gemini-3-flash-preview`, `claude-sonnet-4.5`
- **Harness:** `BARE` (no plan facts, grader works from parametric memory) versus `GROUNDED` (verified plan facts plus a mandatory verbatim-quote step before scoring)
- **Replicates:** 3 per cell at temperature 0, so spread reflects genuine provider nondeterminism rather than sampling

## Results

| Model | Harness | Accuracy | Spread | Self-consistency | Input $/M |
| --- | --- | --- | --- | --- | --- |
| claude-3-haiku | BARE | 63.0% | 5.6 | 88.9% | 0.25 |
| claude-3-haiku | GROUNDED | 85.2% | 5.6 | 94.4% | 0.25 |
| gemini-3-flash | BARE | **100.0%** | 0.0 | 100.0% | 0.50 |
| gemini-3-flash | GROUNDED | **100.0%** | 0.0 | 100.0% | 0.50 |
| claude-sonnet-4.5 | BARE | **100.0%** | 0.0 | 94.4% | 3.00 |
| claude-sonnet-4.5 | GROUNDED | **100.0%** | 0.0 | 100.0% | 3.00 |

Every failure in the entire experiment came from haiku.

## What this says

**1. Model choice dominated harness quality.** Moving from haiku to either stronger model, with no prompt change at all, took accuracy from 63.0% to 100%. That is a 37-point gain from model selection alone.

**2. A better harness partially rescues a weak model, but does not substitute for a good one.** Grounding lifted haiku from 63.0% to 85.2%, a real 22-point gain. Grounded haiku still sat 15 points below either stronger model running with no harness help at all. Prompt engineering could not close the gap.

**3. The harness earns its place on reliability rather than accuracy.** Both strong models were already at ceiling accuracy, so grounding could not raise it. It did raise sonnet's self-consistency from 94.4% to 100%, and it is what prevents the contamination failure documented separately in GRADING_INTEGRITY.md. Keep it.

**4. The cheap strong model matched the expensive one.** `gemini-3-flash` at $0.50 per million input tokens performed identically to `claude-sonnet-4.5` at $3.00, six times the price. On this evidence there is no reason to pay for sonnet as a grader.

**5. The incumbent grader was the single largest error source in the pipeline.** At 63.0% bare, haiku was wrong on roughly one unambiguous item in three. Every published figure this project has produced was graded by it.

## Caveats

- **Ceiling effect.** 100% means no failures observed on 18 deliberately unambiguous items, not that these models never fail. The test cannot separate gemini from sonnet, and it was not designed to.
- **Low power.** With 18 items each one moves accuracy by 5.6 points. This separates "unreliable" from "solid" and should not be read more finely than that.
- **Gold labels were machine-assigned.** They follow explicit stated rules and every item is recorded with its rule, but they were not independently labelled by a domain expert. One label in eighteen, 5.6%, was found to be wrong during the run.
- **The gold set is drawn from plan-specific and refusal cases**, where failures concentrate. It is not a random sample of all grading work, so these accuracies are not a general grader score.

## An unexpected result worth keeping

The QG23 item was failed by all three models in all six cells, unanimously. That was not three models being wrong. It was the gold label being wrong: the QG23 rubric explicitly credits directing the beneficiary to Medicare.gov Plan Finder, which the response did, and the refusal heuristic had mislabelled it because the response opened with "I don't know your location."

**Unanimous disagreement between independent models is a useful audit signal for the gold set itself.** When every model rejects a label, suspect the label first. Correcting it moved both strong models from 94.4% to 100%.

## Recommendation

Switch the grading model to `gemini-3-flash-preview` and keep the grounded harness. Re-grade the reported set and compare against both the published figures and the haiku re-grade, so the contribution of grader quality is visible rather than assumed.

Before publishing any accuracy figure derived from this, expand the gold set beyond 18 items and have the labels reviewed by someone other than the system that generated them.

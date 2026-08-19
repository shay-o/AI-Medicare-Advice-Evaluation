# Can AI give good Medicare advice?

Medicare is one of the most consequential decisions many people make, and one of the hardest to get help with. This project measures how well AI models answer real Medicare questions, scored against the same rubric researchers used to grade trained human counselors.

- [Overview and findings](https://www.shayoreilly.net/projects/AI-Medicare-Advice-Evaluator/overview.html)
- [Model comparison matrix](https://www.shayoreilly.net/projects/AI-Medicare-Advice-Evaluator/matrix_report.html)

## The idea

In 2025, researchers published a study in *JAMA Network Open* that did something clever. They hired mystery shoppers to pose as Medicare beneficiaries, call State Health Insurance Assistance Program (SHIP) counselors, and ask a fixed list of questions. Every answer was then scored against a detailed rubric: which facts a correct answer must contain, which are optional, and what counts as an error.

That turns "was this good advice?" into something measurable. And because the rubric describes the answer rather than the answerer, the same scoring can be applied to anything that answers the questions, including an AI model.

This repository is that experiment. It runs AI models through the study's exact question script and scores the results with the study's exact rubric, so AI performance can be placed directly beside the published human baseline.

## What it takes to be a fair comparison

The most important design rule here is that the AI has to be tested under the same conditions the counselors were:

- The exact opening statement and question wording from the study, never paraphrased
- Questions asked in the study's order
- **No** system prompt telling the AI to act as a Medicare counselor
- **No** extra context or hints beyond what the mystery shoppers provided

That last point is the one people push back on, because a little prompt engineering would obviously raise the scores. But the study measured what ordinary people actually got when they asked for help. Optimally prompting the AI would measure something else entirely, and the comparison to the human baseline would stop meaning anything.

## How it works

Each role in the original study becomes a step in an automated pipeline:

| Study role | Here |
| --- | --- |
| Mystery shopper | Asks the scripted questions, in order, with no embellishment |
| SHIP counselor | The AI model being evaluated |
| Research analyst | An LLM grader that scores each answer against the rubric |

Every run stores the full transcript, the grader's verdict, and the reasoning behind it, so any score can be traced back to the words that produced it.

Two scenarios are tested, both taken from the study: someone turning 65 with employer coverage, and someone who has both Medicare and Medicaid. Nineteen question groups are scored across them.

## What the results look like so far

Two findings have held up across every version of the analysis.

**AI does well on general Medicare rules.** Questions like how enrollment timing works, how Medicare Advantage differs from Original Medicare, or what a Supplement plan covers. Models answer these more completely than the counselor baseline, by a wide margin.

**AI does poorly on questions about a specific plan.** What is this plan's premium, is this doctor in network, is this drug on the formulary. Performance drops sharply.

That gap is the most interesting result in the project, and it is not really about intelligence. A counselor answering those questions has the Medicare Plan Finder open in front of them. A model answering from memory does not. When I tried to establish the correct answers myself in order to fix the grading, I hit exactly the same wall: the authoritative source was hard to query, secondary sources contradicted each other, and the plan had been renamed between years. These questions are hard for the same reasons for everyone.

The practical implication is that on plan-specific questions the **product** matters more than the **model**. An AI with live search and access to plan data is doing a different task than a bare model recalling training data.

## Honest status of the numbers

**The figures on the published pages above were produced by a grading setup since found to have real defects.** They have not been re-published yet, and the corrected figures are not ready to replace them.

Four separate problems were found and fixed, in this order:

1. **A wrong answer key.** Two questions were scored against criteria that contradicted the real plan, so models giving the correct answer were marked wrong, and at least one giving the wrong answer was marked right.
2. **No ground truth for the grader.** On plan-specific questions the grader was judging from memory, which made it contradict itself on neighbouring questions.
3. **A defect introduced by the fix for problem 2.** Supplying the grader with verified plan facts caused it to credit responses for figures that appeared only in its own prompt, scoring refusals as though they were answers.
4. **A question-to-rubric misalignment.** Answers were graded against the wrong rubric entirely, because the scenario's conversation turns and the study's question numbers were not the same thing. A location statement was being scored as a long-term-care answer.

A re-grade with all four addressed puts the headline in the same range as the published figure, with a noticeably wider gap between general and plan-specific questions. That number is not published yet, because it changed four things at once and so cannot be attributed to any one of them.

For the detail, [docs/GRADING_INTEGRITY.md](docs/GRADING_INTEGRITY.md) is the full record, including a diagnosis that was confidently wrong before it was right. [docs/LEARNINGS.md](docs/LEARNINGS.md) is the shorter, more general version.

**This is a personal project by a non-expert, and it has not been reviewed by anyone with Medicare policy expertise.** The question set is not exhaustive. Treat the results as a preliminary signal, not a finding.

## Why the failures are documented rather than quietly fixed

An evaluation system is a measuring instrument, and the useful question about any instrument is not whether it produces numbers but whether you can trust the ones it produces. Every defect above was found by deliberately checking whether the grader was right, not by the pipeline complaining. A broken grader produces clean-looking output, which is exactly what makes it dangerous.

So the repository keeps the record of what broke, what the wrong diagnosis was, and what each fix changed. That is more useful than a tidy headline, and it is the part of this project worth looking at.

## Documentation

| Document | What it covers |
| --- | --- |
| [docs/LEARNINGS.md](docs/LEARNINGS.md) | What building and auditing this taught, including the misdiagnoses |
| [docs/GRADING_INTEGRITY.md](docs/GRADING_INTEGRITY.md) | Every grading defect found, with evidence and blast radius |
| [docs/GRADER_SELECTION.md](docs/GRADER_SELECTION.md) | Experiment: how often the grader fails, and whether a better model or a better prompt fixes it |
| [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) | How the published numbers are derived, and how to re-derive them |

## The question bank, on its own

`eval_dataset/` is a standalone, structured version of the study's question bank, usable without any of the code here: to build your own grader, run manual evaluations, or compare your own AI outputs against the human baseline.

```
eval_dataset/
├── index.json                        # Manifest linking all files
├── scenarios/                        # Personas and question sequences
├── question_groups/                  # One file per scored question, with its rubric
└── baselines/
    └── ship_2025_human_baseline.json # Counselor accuracy rates from the study
```

Each question file has the exact question wording, the four-tier rubric derived from the study's scoring guide, and the human baseline for that question. Questions needing a live plan lookup are flagged `external_validation_required`.

Start at `eval_dataset/index.json`.

## Running it yourself

Install:

```bash
pip install -e ".[openrouter]"
```

Check the install with no API key, using fake models at both ends:

```bash
python -m src run --scenario scenarios/v1/scenario_001.json --target-model fake:perfect --grade-model fake:perfect
```

Add a key from [openrouter.ai/keys](https://openrouter.ai/keys):

```bash
cp .env.example .env
```

Run a real evaluation:

```bash
python -m src run --scenario scenarios/medicare_only/all_questions.json --target-model openrouter:openai/gpt-5.2
```

Re-derive the published figures independently:

```bash
python scripts/verify_headline_numbers.py
```

Model specs are `provider:model`. Grading runs on every evaluation and defaults to `openrouter:google/gemini-3-flash-preview`, chosen by measurement rather than by price: see [docs/GRADER_SELECTION.md](docs/GRADER_SELECTION.md). The full flag reference is in [docs/USER_GUIDE.md](docs/USER_GUIDE.md).

Requires Python 3.10 or newer.

## How the repository is laid out

```
eval_dataset/       # The question bank, usable standalone
scenarios/          # Test scenarios and personas
src/                # The harness: adapters, agents, grader
scripts/            # Report generation and verification
docs/               # Method, findings, and defect records
reference_material/ # The study supplement, plan facts, grader gold set
reported_runs.json  # The exact run set behind the published figures
runs/               # Stored evaluation results
```

## Design principles

1. **Role separation.** The thing asking, the thing answering, and the thing judging are never the same component.
2. **Grounded judging.** The grader scores against a rubric and verified facts, not its own recollection.
3. **Full auditability.** Raw transcripts and grader reasoning are stored verbatim.
4. **Snapshot evaluation.** Results describe specific model versions at a specific time, not "AI" in general. Four of the nine models originally tested are already unavailable.
5. **Append-only evidence.** A re-grade writes a new run and never edits an existing one.

## Research use only

This system evaluates the quality of AI-generated information. It does not provide medical, legal, or insurance advice, and nothing here should be used to make healthcare decisions.

If you need Medicare help, SHIP counselors provide it free, from trained humans, in every state: [shiphelp.org](https://www.shiphelp.org/).

## Source study

Dugan K, Peterson I, Dorneo A, Garrido MM. Accuracy of Medicare information provided by State Health Insurance Assistance Programs. *JAMA Network Open*. 2025;8(4):e252834. [doi:10.1001/jamanetworkopen.2025.2834](https://doi.org/10.1001/jamanetworkopen.2025.2834)

The vast majority of the intellectual work here belongs to the study's authors. This project re-implements their methodology; it did not invent it.

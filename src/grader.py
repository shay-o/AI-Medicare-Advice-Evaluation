"""
LLM-based grader for evaluating Medicare advice responses.
Uses the SHIP study rubric to score responses.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from .adapters.base import BaseLLMAdapter
from .grading_rubric import (
    QuestionGroup,
    ScoreCategory,
    get_question_group,
    get_question_group_for_turn,
    get_all_question_groups
)


class QuestionScore(BaseModel):
    """Score for a single question."""
    question_number: int
    question_text: str
    response_text: str
    score: ScoreCategory
    explanation: str
    group_id: str
    group_name: str
    criteria_met: List[str]
    criteria_missed: List[str]
    response_quotes: List[str] = []
    """Verbatim quotes the grader identified as the response's actual answer.

    Recorded so a verdict can be audited against what the response really said. This
    exists because supplying plan facts to the grader once caused it to credit responses
    for figures that appeared only in its own prompt. See docs/GRADING_INTEGRITY.md.
    """


class RunScore(BaseModel):
    """Overall score for a run."""
    run_id: str
    scenario: str
    question_scores: List[QuestionScore]

    @property
    def total_questions(self) -> int:
        return len(self.question_scores)

    @property
    def accurate_complete_count(self) -> int:
        return sum(1 for qs in self.question_scores
                  if qs.score == ScoreCategory.ACCURATE_COMPLETE)

    @property
    def substantive_incomplete_count(self) -> int:
        return sum(1 for qs in self.question_scores
                  if qs.score == ScoreCategory.SUBSTANTIVE_INCOMPLETE)

    @property
    def not_substantive_count(self) -> int:
        return sum(1 for qs in self.question_scores
                  if qs.score == ScoreCategory.NOT_SUBSTANTIVE)

    @property
    def incorrect_count(self) -> int:
        return sum(1 for qs in self.question_scores
                  if qs.score == ScoreCategory.INCORRECT)

    @property
    def accuracy_rate(self) -> float:
        """Percentage of accurate and complete responses."""
        if self.total_questions == 0:
            return 0.0
        return (self.accurate_complete_count / self.total_questions) * 100


class MedicareAdviceGrader:
    """Grades Medicare advice responses using LLM and SHIP rubric."""

    def __init__(
        self,
        adapter: BaseLLMAdapter,
        plan_facts: str | None = None,
        evaluation_date: str | None = None,
    ):
        """
        Initialize grader with an LLM adapter.

        Args:
            adapter: LLM adapter to use for grading (e.g., AnthropicAdapter, OpenRouterAdapter)
            plan_facts: Authoritative facts about the specific plan named in the scenario,
                rendered as text. Several question groups ask about a real plan's attributes,
                and their rubrics are only decidable against ground truth. Without this the
                grading model answers from parametric memory, which previously produced
                contradictory verdicts on neighbouring questions.
                See docs/GRADING_INTEGRITY.md.
        """
        self.adapter = adapter
        self.plan_facts = plan_facts
        # Without this the grading model assumes its own training cutoff is "now" and
        # marks correct current-year figures as fabricated. Observed directly: a model
        # correctly cited the 2026 Part B premium of $202.90 and the grader called it a
        # hallucination "as the current date is in 2024". That penalises exactly the
        # search-enabled responses this project is trying to measure.
        self.evaluation_date = evaluation_date or datetime.now().strftime("%B %Y")

    async def grade_response(
        self,
        question_number: int,
        question_text: str,
        response_text: str,
        scenario: str = "medicare_only",
        study_question: int | None = None,
    ) -> QuestionScore:
        """
        Grade a single question response.

        Args:
            question_number: The question number (e.g., 1, 2, 3...)
            question_text: The actual question that was asked
            response_text: The AI's response to grade
            scenario: "medicare_only" or "dual_eligible"

        Returns:
            QuestionScore with score and explanation
        """
        # Get the question group (rubric criteria).
        # question_number is a CONVERSATION TURN index, which is not the same as the
        # SHIP study question number: scenarios add turns the study does not number
        # (a location reply, and the second half of two-part questions). Translating
        # here rather than assuming they match. See docs/GRADING_INTEGRITY.md.
        if study_question is not None:
            question_group = get_question_group(study_question, scenario)
        else:
            question_group = get_question_group_for_turn(question_number, scenario)

        if not question_group:
            raise ValueError(
                f"Turn {question_number} in the {scenario} scenario maps to no scored "
                f"SHIP question group. Unscored turns must be skipped by the caller."
            )

        # Build the grading prompt
        grading_prompt = self._build_grading_prompt(
            question_group=question_group,
            question_text=question_text,
            response_text=response_text
        )

        # Call LLM to grade using the adapter
        response = await self.adapter.generate(
            messages=[{
                "role": "user",
                "content": grading_prompt
            }],
            temperature=0,
            max_tokens=2000
        )

        # Parse the response
        score_result = self._parse_grading_response(response.content)

        # Create QuestionScore
        return QuestionScore(
            question_number=question_number,
            question_text=question_text,
            response_text=response_text,
            score=score_result["score"],
            explanation=score_result["explanation"],
            group_id=question_group.group_id,
            group_name=question_group.group_name,
            criteria_met=score_result["criteria_met"],
            criteria_missed=score_result["criteria_missed"],
            response_quotes=score_result.get("response_quotes", []),
        )

    def _build_grading_prompt(
        self,
        question_group: QuestionGroup,
        question_text: str,
        response_text: str
    ) -> str:
        """Build the prompt for Claude to grade a response."""

        prompt = f"""You are evaluating Medicare counseling advice against the SHIP (State Health Insurance Assistance Program) study rubric.

**Question Group**: {question_group.group_name}
**Topic**: {question_group.topic}

**Question Asked**: {question_text}

**Response to Evaluate**:
{response_text}

---
"""

        if self.plan_facts:
            prompt += f"""
**PLAN FACTS (reference for checking correctness only)**:

STOP. Read this carefully before using the section below.

The following facts are NOT part of the response you are grading. The person who wrote
that response did NOT see them. They exist only so you can check whether the claims the
response actually made are true or false.

Rules for using this section, in order of importance:

1. NEVER credit the response for a fact that appears here but not in the response text.
   If a figure appears in PLAN FACTS and not in the response, the response DID NOT
   PROVIDE IT. Saying otherwise is a grading error.
2. If the response declines to answer, says it cannot confirm, says it does not know, or
   tells the beneficiary to look it up elsewhere, then the response did not answer the
   question. That remains true even when the answer is sitting in PLAN FACTS below. Score
   it as NOT_SUBSTANTIVE.
3. Use these facts ONLY to decide whether a claim the response did make is correct.
4. Do not substitute your own recollection of this plan for what is written here.
5. If a fact needed to decide the score is missing here, say so rather than guessing.

{self.plan_facts}

---
"""

        prompt += f"""
**WHEN THIS IS BEING EVALUATED**: {self.evaluation_date}

This matters for two reasons, and getting it wrong is a known way to grade badly:

1. The response may contain accurate information that is NEWER than your training data,
   especially if the counselor looked it up. Medicare figures change every year. A premium,
   deductible or out-of-pocket limit you do not recognise is NOT evidence of fabrication.
   Do not mark a response incorrect merely because a current-year figure is unfamiliar.
2. Conversely, a figure that was right in an earlier year may now be out of date. Judge
   against the evaluation date above, not against whichever year you think it is.

**WHAT YOU MAY AND MAY NOT CALL INCORRECT**

Mark INCORRECT only when the response contradicts something you can actually check:
the PLAN FACTS section, or a well-established Medicare rule you are confident about.

You may NOT mark a response incorrect because:
- you cannot verify a claim
- a figure is absent from PLAN FACTS (that section covers one plan, not all of Medicare)
- a statistic or date is more recent than your own knowledge

If you cannot confirm a claim either way, say so in your explanation and score on the
criteria you CAN judge. Unverifiable is not the same as wrong.

**RULES CHANGE. YOUR KNOWLEDGE OF THEM MAY BE OUT OF DATE.**

Eligibility thresholds, asset and income limits, premiums, deductibles and programme
rules are changed by legislation and by annual adjustment. A rule you are confident about
may simply have been superseded, and confidence is not evidence.

Observed failure this guard exists to prevent: a response correctly stated that California
reinstated the Medi-Cal asset limit at $130,000 from January 2026, including for Medicare
Savings Programs. The grader marked it INCORRECT and asserted that California had
eliminated those limits. The response was right; the grader was describing the previous
state of the law.

So, for any claim about a threshold, limit, premium, or eligibility rule:

- If the response CITES A SOURCE for the claim, you may not mark it incorrect on the
  strength of your own recollection alone. Say what you believe, note that the response
  cites a source, and score on the other criteria.
- If you have no source and no PLAN FACTS entry, treat the claim as unverifiable, not
  wrong.
- Reserve INCORRECT for claims that contradict PLAN FACTS, contradict a stable structural
  fact about how Medicare works, or are internally inconsistent.

"""

        prompt += """
**Scoring Rubric**:

You must score this response as one of:
1. ACCURATE_COMPLETE
2. SUBSTANTIVE_INCOMPLETE
3. NOT_SUBSTANTIVE
4. INCORRECT

**Criteria for ACCURATE_COMPLETE**:
All of the following must be substantively addressed:
"""

        for criterion in question_group.accurate_complete_criteria:
            prompt += f"- {criterion}\n"

        prompt += f"\n**Criteria for SUBSTANTIVE_INCOMPLETE**:\n"
        for criterion in question_group.substantive_incomplete_criteria:
            prompt += f"- {criterion}\n"

        prompt += f"\n**Criteria for NOT_SUBSTANTIVE**:\n"
        for criterion in question_group.not_substantive_criteria:
            prompt += f"- {criterion}\n"

        prompt += f"\n**Criteria for INCORRECT**:\n"
        for criterion in question_group.incorrect_criteria:
            prompt += f"- {criterion}\n"

        prompt += """
---

**Instructions**:
1. FIRST, quote verbatim from the response the specific sentences where it answers the
   question. Copy them exactly. If the response contains no such sentences, write
   "NO ANSWER GIVEN".
2. Only then, judge those quoted sentences against the criteria.
3. Determine the appropriate score based on the rubric
4. Provide a clear explanation of your scoring decision

**Important Scoring Notes**:
- A response is ACCURATE_COMPLETE only if ALL criteria for that category are met
- A response is SUBSTANTIVE_INCOMPLETE if it provides some accurate information but misses key details
- A response is NOT_SUBSTANTIVE if it doesn't really answer the question or says "I don't know"
- A response is INCORRECT if it provides wrong information that would materially affect a Medicare enrollee's decision
- Focus on substance, not exact wording - if the meaning is conveyed, credit should be given
- Grade ONLY the text of the response. Everything else in this prompt is reference
  material that the responder never saw. If you find yourself writing that the response
  "provided" a figure, verify that the figure appears in your verbatim quotes above. If
  it does not, the response did not provide it.

**Response Format**:
Provide your response in this exact format:

RESPONSE_QUOTES:
- [verbatim quote from the response that answers the question]
- [one quote per line, or the single line "NO ANSWER GIVEN"]

SCORE: [ACCURATE_COMPLETE | SUBSTANTIVE_INCOMPLETE | NOT_SUBSTANTIVE | INCORRECT]

CRITERIA_MET:
- [list each criterion that was met, using the exact text from the rubric]
- [one criterion per line]

CRITERIA_MISSED:
- [list each criterion that was missed, using the exact text from the rubric]
- [one criterion per line]
- [if none missed, write "None"]

EXPLANATION:
[Provide a clear, detailed explanation of your scoring decision. Explain:
1. What information the response included, referring only to your verbatim quotes
2. What information was missing (if any)
3. Why you assigned this particular score
4. Any concerns about accuracy or completeness]
"""

        return prompt

    def _parse_grading_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's grading response."""

        lines = response_text.strip().split('\n')

        score = None
        criteria_met = []
        criteria_missed = []
        explanation = []
        response_quotes = []

        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("SCORE:"):
                score_text = line.replace("SCORE:", "").strip()
                # Try to extract the score category
                if "ACCURATE_COMPLETE" in score_text:
                    score = ScoreCategory.ACCURATE_COMPLETE
                elif "SUBSTANTIVE_INCOMPLETE" in score_text:
                    score = ScoreCategory.SUBSTANTIVE_INCOMPLETE
                elif "NOT_SUBSTANTIVE" in score_text:
                    score = ScoreCategory.NOT_SUBSTANTIVE
                elif "INCORRECT" in score_text:
                    score = ScoreCategory.INCORRECT
                current_section = "score"

            elif line.startswith("RESPONSE_QUOTES:"):
                current_section = "response_quotes"

            elif line.startswith("CRITERIA_MET:"):
                current_section = "criteria_met"

            elif line.startswith("CRITERIA_MISSED:"):
                current_section = "criteria_missed"

            elif line.startswith("EXPLANATION:"):
                current_section = "explanation"

            elif line.startswith("-") and current_section == "response_quotes":
                response_quotes.append(line[1:].strip())

            elif line.startswith("-") and current_section == "criteria_met":
                criteria_met.append(line[1:].strip())

            elif line.startswith("-") and current_section == "criteria_missed":
                criteria_missed.append(line[1:].strip())

            elif current_section == "explanation" and line:
                explanation.append(line)

        # Default to NOT_SUBSTANTIVE if no score found
        if score is None:
            score = ScoreCategory.NOT_SUBSTANTIVE

        return {
            "score": score,
            "criteria_met": criteria_met,
            "criteria_missed": criteria_missed,
            "explanation": "\n".join(explanation).strip(),
            "response_quotes": response_quotes,
        }

    async def grade_run(
        self,
        run_id: str,
        questions_and_responses: List[Dict[str, Any]],
        scenario: str = "medicare_only"
    ) -> RunScore:
        """
        Grade all responses from a single run.

        Args:
            run_id: Unique identifier for this run
            questions_and_responses: List of dicts with 'question_number', 'question_text', 'response_text'
            scenario: "medicare_only" or "dual_eligible"

        Returns:
            RunScore with scores for all questions
        """

        question_scores = []

        for qa in questions_and_responses:
            # Skip turns that are not scored SHIP questions: the dual-eligible
            # location reply, and the second half of two-part questions, which the
            # study scores within their first part's group.
            if qa.get("study_question") is not None:
                if get_question_group(qa["study_question"], scenario) is None:
                    continue
            elif get_question_group_for_turn(qa["question_number"], scenario) is None:
                continue
            try:
                score = await self.grade_response(
                    question_number=qa["question_number"],
                    question_text=qa["question_text"],
                    response_text=qa["response_text"],
                    scenario=scenario,
                    study_question=qa.get("study_question"),
                )
                question_scores.append(score)
            except Exception as e:
                print(f"Error grading question {qa['question_number']}: {e}")
                # Add a placeholder score
                question_scores.append(QuestionScore(
                    question_number=qa["question_number"],
                    question_text=qa["question_text"],
                    response_text=qa["response_text"],
                    score=ScoreCategory.MISSING,
                    explanation=f"Error during grading: {str(e)}",
                    group_id="ERROR",
                    group_name="Error",
                    criteria_met=[],
                    criteria_missed=[]
                ))

        return RunScore(
            run_id=run_id,
            scenario=scenario,
            question_scores=question_scores
        )


def format_run_score_summary(run_score: RunScore) -> str:
    """Format a run score as a readable summary."""

    summary = f"""
=== Grading Summary ===
Run ID: {run_score.run_id}
Scenario: {run_score.scenario}
Total Questions: {run_score.total_questions}

Score Distribution:
- Accurate & Complete: {run_score.accurate_complete_count} ({run_score.accuracy_rate:.1f}%)
- Substantive but Incomplete: {run_score.substantive_incomplete_count}
- Not Substantive: {run_score.not_substantive_count}
- Incorrect: {run_score.incorrect_count}

=== Question-by-Question Results ===
"""

    for qs in run_score.question_scores:
        summary += f"\n**Q{qs.question_number}: {qs.group_name}**\n"
        summary += f"Score: {qs.score.value.upper()}\n"
        summary += f"Explanation: {qs.explanation}\n"

        if qs.criteria_met:
            summary += "\nCriteria Met:\n"
            for c in qs.criteria_met:
                summary += f"  ✓ {c}\n"

        if qs.criteria_missed:
            summary += "\nCriteria Missed:\n"
            for c in qs.criteria_missed:
                summary += f"  ✗ {c}\n"

        summary += "\n" + "="*50 + "\n"

    return summary

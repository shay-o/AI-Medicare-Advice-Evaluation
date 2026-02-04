"""
LLM-based grader for evaluating Medicare advice responses.
Uses the SHIP study rubric to score responses.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from .adapters.base import BaseLLMAdapter
from .grading_rubric import (
    QuestionGroup,
    ScoreCategory,
    get_question_group,
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

    def __init__(self, adapter: BaseLLMAdapter):
        """
        Initialize grader with an LLM adapter.

        Args:
            adapter: LLM adapter to use for grading (e.g., AnthropicAdapter, OpenRouterAdapter)
        """
        self.adapter = adapter

    async def grade_response(
        self,
        question_number: int,
        question_text: str,
        response_text: str,
        scenario: str = "medicare_only"
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
        # Get the question group (rubric criteria)
        question_group = get_question_group(question_number, scenario)

        if not question_group:
            raise ValueError(f"No rubric found for question {question_number} in {scenario} scenario")

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
            criteria_missed=score_result["criteria_missed"]
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
1. Carefully read the response
2. Check which criteria from "ACCURATE_COMPLETE" are met
3. Determine the appropriate score based on the rubric
4. Provide a clear explanation of your scoring decision

**Important Scoring Notes**:
- A response is ACCURATE_COMPLETE only if ALL criteria for that category are met
- A response is SUBSTANTIVE_INCOMPLETE if it provides some accurate information but misses key details
- A response is NOT_SUBSTANTIVE if it doesn't really answer the question or says "I don't know"
- A response is INCORRECT if it provides wrong information that would materially affect a Medicare enrollee's decision
- Focus on substance, not exact wording - if the meaning is conveyed, credit should be given

**Response Format**:
Provide your response in this exact format:

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
1. What information the response included
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

            elif line.startswith("CRITERIA_MET:"):
                current_section = "criteria_met"

            elif line.startswith("CRITERIA_MISSED:"):
                current_section = "criteria_missed"

            elif line.startswith("EXPLANATION:"):
                current_section = "explanation"

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
            "explanation": "\n".join(explanation).strip()
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
            try:
                score = await self.grade_response(
                    question_number=qa["question_number"],
                    question_text=qa["question_text"],
                    response_text=qa["response_text"],
                    scenario=scenario
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

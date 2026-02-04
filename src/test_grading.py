"""
Test script for the LLM-based grading system.
Demonstrates grading Medicare advice responses using the SHIP rubric.
"""

import asyncio
import json
from pathlib import Path
from .grader import MedicareAdviceGrader, format_run_score_summary


async def test_grading_with_sample_responses():
    """Test grading with sample responses."""

    # Initialize grader
    grader = MedicareAdviceGrader()

    # Sample questions and responses for Medicare-Only scenario
    sample_qa = [
        {
            "question_number": 1,
            "question_text": "When can I select my Medicare coverage plan, and when can I change it later?",
            "response_text": """You can select your Medicare coverage plan within 3 months of turning 65 - this is called your Initial Enrollment Period.

After that, you have several opportunities to make changes:
- Open Enrollment Period (October 15 - December 7) - You can switch between Original Medicare and Medicare Advantage, or change your Part D prescription drug plan
- Medicare Advantage Open Enrollment Period (January 1 - March 31) - If you're in a Medicare Advantage plan, you can switch to a different Medicare Advantage plan or return to Original Medicare
- Special Enrollment Periods - Available if you have certain life events like moving or losing other coverage

These enrollment periods ensure you can review and adjust your coverage as your needs change."""
        },
        {
            "question_number": 2,
            "question_text": "Do I have to sign up for Medicare when I turn 65, or can I remain on my employer plan?",
            "response_text": """No, you don't have to sign up for Medicare when you turn 65 if you have employer coverage. You can remain on your employer plan. However, there are some important considerations:

1. If your employer has 20 or more employees, you can delay Medicare Part B without penalty as long as you have coverage through current employment
2. If it's a smaller employer (fewer than 20 employees), Medicare becomes primary and you should enroll to avoid gaps in coverage
3. You can have both Medicare and employer coverage at the same time - they can work together

You should also sign up for Medicare Part A (hospital coverage) when you're eligible since it's usually premium-free. Just be careful about enrolling in Part B if you want to continue contributing to an HSA, as Medicare enrollment ends HSA eligibility."""
        },
        {
            "question_number": 3,
            "question_text": "I keep hearing about Medicare Advantage. How are Medicare Advantage Plans different from regular Medicare, and what are good and bad about them?",
            "response_text": """Great question! Let me explain the key differences:

**Medicare Advantage Plans (Part C)**:
- Advantages:
  * Often have lower out-of-pocket costs than Original Medicare plus a supplement
  * Usually include prescription drug coverage (Part D) built-in
  * May offer extra benefits like dental, vision, hearing, fitness memberships, or OTC allowances
  * Many have $0 premiums (though you still pay the Part B premium)

- Disadvantages:
  * Network restrictions - you typically must use in-network providers
  * You may not be able to keep your current doctor if they're not in the plan's network
  * Less flexibility to see specialists without referrals (for HMO plans)
  * Can have more complex rules about authorizations

**Original Medicare (Parts A & B)**:
- Part A covers hospital stays (usually no premium, has a deductible)
- Part B covers doctor visits and outpatient care (monthly premium, annual deductible)
- Advantages:
  * Freedom to see almost any doctor or hospital nationwide that accepts Medicare
  * No network restrictions
  * Can add a Medigap (supplement) policy to cover gaps in coverage
  * Need to add separate Part D for prescriptions

- Disadvantages:
  * Can be more expensive without a supplement policy
  * Has cost-sharing (deductibles, coinsurance)
  * No extra benefits like dental or vision

The choice really depends on your priorities - if you want lower costs and don't mind network restrictions, Medicare Advantage might be good. If you want maximum flexibility and travel frequently, Original Medicare with a supplement might be better."""
        }
    ]

    print("\n" + "="*80)
    print("MEDICARE ADVICE GRADING TEST")
    print("="*80 + "\n")

    # Grade each question-response pair
    questions_and_responses = [
        {
            "question_number": qa["question_number"],
            "question_text": qa["question_text"],
            "response_text": qa["response_text"]
        }
        for qa in sample_qa
    ]

    print("Grading responses...")
    print("-" * 80)

    run_score = grader.grade_run(
        run_id="test_run_001",
        questions_and_responses=questions_and_responses,
        scenario="medicare_only"
    )

    # Display results
    summary = format_run_score_summary(run_score)
    print(summary)

    # Save results
    output_dir = Path(__file__).parent.parent / "runs" / "grading_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"grading_results_{run_score.run_id}.json"
    with open(output_file, 'w') as f:
        json.dump(run_score.model_dump(), f, indent=2)

    print(f"\nResults saved to: {output_file}")


async def grade_existing_run(run_dir: str):
    """Grade an existing run by reading its transcript."""

    run_path = Path(run_dir)
    if not run_path.exists():
        print(f"Error: Run directory not found: {run_dir}")
        return

    # Find transcript file
    transcript_files = list(run_path.glob("*_transcript.json"))
    if not transcript_files:
        print(f"Error: No transcript found in {run_dir}")
        return

    transcript_file = transcript_files[0]
    print(f"Loading transcript from: {transcript_file}")

    with open(transcript_file) as f:
        transcript = json.load(f)

    # Extract question-response pairs
    questions_and_responses = []
    question_num = 0

    for i, turn in enumerate(transcript):
        if turn["role"] == "user":
            question_num += 1
            # Find corresponding assistant response
            if i + 1 < len(transcript) and transcript[i + 1]["role"] == "assistant":
                questions_and_responses.append({
                    "question_number": question_num,
                    "question_text": turn["content"],
                    "response_text": transcript[i + 1]["content"]
                })

    if not questions_and_responses:
        print("Error: No question-response pairs found in transcript")
        return

    print(f"Found {len(questions_and_responses)} question-response pairs")

    # Grade them
    grader = MedicareAdviceGrader()

    run_id = run_path.name
    run_score = grader.grade_run(
        run_id=run_id,
        questions_and_responses=questions_and_responses,
        scenario="medicare_only"
    )

    # Display and save results
    summary = format_run_score_summary(run_score)
    print(summary)

    output_file = run_path / f"grading_results.json"
    with open(output_file, 'w') as f:
        json.dump(run_score.model_dump(), f, indent=2)

    print(f"\nGrading results saved to: {output_file}")


async def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--run-dir":
        if len(sys.argv) < 3:
            print("Usage: python test_grading.py --run-dir <path_to_run>")
            sys.exit(1)
        await grade_existing_run(sys.argv[2])
    else:
        await test_grading_with_sample_responses()


if __name__ == "__main__":
    asyncio.run(main())

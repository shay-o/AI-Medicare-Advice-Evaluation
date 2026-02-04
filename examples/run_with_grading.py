"""
Example: Run Medicare evaluation and grade the results.

This script demonstrates:
1. Running a scenario with a target model
2. Grading the responses using the SHIP rubric
3. Saving and displaying results
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adapters.anthropic_adapter import AnthropicAdapter
from adapters.fake_adapter import FakeAdapter
from grader import MedicareAdviceGrader, format_run_score_summary
from schemas import Scenario


async def run_scenario_with_grading(
    scenario_path: str,
    target_model: str = "fake:perfect",
    grade_results: bool = True
):
    """
    Run a scenario and optionally grade the results.

    Args:
        scenario_path: Path to scenario JSON file
        target_model: Model to evaluate (e.g., "fake:perfect", "anthropic:claude-3-5-sonnet-20241022")
        grade_results: Whether to grade responses with SHIP rubric
    """

    # Load scenario
    with open(scenario_path) as f:
        scenario_data = json.load(f)

    scenario = Scenario(**scenario_data)

    print(f"\n{'='*80}")
    print(f"Scenario: {scenario.title}")
    print(f"Target: {target_model}")
    print(f"{'='*80}\n")

    # Create adapter based on target_model
    if target_model.startswith("fake:"):
        adapter = FakeAdapter(response_type=target_model.split(":")[1])
    elif target_model.startswith("anthropic:"):
        model_name = target_model.split(":")[1]
        adapter = AnthropicAdapter(model_name=model_name)
    else:
        raise ValueError(f"Unsupported model: {target_model}")

    # Conduct conversation
    print("Conducting conversation...")
    questions_and_responses = []
    messages = []

    for i, turn in enumerate(scenario.scripted_turns, 1):
        # User question
        print(f"\n[Q{i}] {turn['user_message']}")
        messages.append({"role": "user", "content": turn["user_message"]})

        # Get response
        response = await adapter.generate(
            messages=messages,
            temperature=scenario.target_parameters.temperature,
            max_tokens=scenario.target_parameters.max_tokens,
            seed=scenario.target_parameters.seed
        )

        print(f"\n[A{i}] {response.content[:200]}...")  # Preview first 200 chars

        messages.append({"role": "assistant", "content": response.content})

        questions_and_responses.append({
            "question_number": turn["question_number"],
            "question_text": turn["user_message"],
            "response_text": response.content
        })

    # Grade responses if requested
    if grade_results:
        print(f"\n\n{'='*80}")
        print("GRADING RESPONSES")
        print(f"{'='*80}\n")

        grader = MedicareAdviceGrader()

        run_score = grader.grade_run(
            run_id=f"example_{scenario.scenario_id}",
            questions_and_responses=questions_and_responses,
            scenario="medicare_only"  # TODO: Detect from scenario
        )

        # Display results
        summary = format_run_score_summary(run_score)
        print(summary)

        # Save results
        output_dir = Path(__file__).parent.parent / "runs" / "graded_examples"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"grading_{run_score.run_id}.json"
        with open(output_file, 'w') as f:
            json.dump(run_score.model_dump(), f, indent=2)

        print(f"\n✓ Grading results saved to: {output_file}")

    print(f"\n{'='*80}")
    print("COMPLETE")
    print(f"{'='*80}\n")


async def main():
    """Main entry point."""

    # Example 1: Grade a simple scenario with fake adapter
    print("\n" + "="*80)
    print("EXAMPLE 1: Grading with Fake Adapter (perfect responses)")
    print("="*80)

    scenario_path = Path(__file__).parent.parent / "scenarios" / "medicare_only" / "all_questions.json"

    if scenario_path.exists():
        await run_scenario_with_grading(
            scenario_path=str(scenario_path),
            target_model="fake:perfect",
            grade_results=True
        )
    else:
        print(f"Scenario not found: {scenario_path}")

    # Example 2: Grade with incomplete responses
    print("\n" + "="*80)
    print("EXAMPLE 2: Grading with Fake Adapter (incomplete responses)")
    print("="*80)

    if scenario_path.exists():
        await run_scenario_with_grading(
            scenario_path=str(scenario_path),
            target_model="fake:incomplete",
            grade_results=True
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

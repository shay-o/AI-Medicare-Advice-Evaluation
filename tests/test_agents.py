"""Basic tests for agents with fake adapter"""

import asyncio
import json
from pathlib import Path

import pytest

from src.adapters.fake_adapter import FakeAdapter
from src.agents import (
    AdjudicatorAgent,
    ExtractorAgent,
    QuestionerAgent,
    ScorerAgent,
    VerifierAgent,
)
from src.schemas import Scenario


def load_test_scenario() -> Scenario:
    """Load the test scenario"""
    scenario_path = Path("scenarios/v1/scenario_001.json")
    with scenario_path.open() as f:
        scenario_data = json.load(f)
    return Scenario(**scenario_data)


@pytest.mark.asyncio
async def test_questioner_simple():
    """Test questioner in simple mode (no LLM)"""
    scenario = load_test_scenario()

    # Create questioner (adapter not needed for simple mode)
    adapter = FakeAdapter("perfect")
    questioner = QuestionerAgent(adapter)

    # Use simple mode
    result = questioner.generate_questions_simple(scenario)

    assert "turns" in result
    assert len(result["turns"]) == len(scenario.scripted_turns)
    assert result["turns"][0]["turn_id"] == "Q1"
    assert "Medicare Advantage" in result["turns"][0]["user_message"]


@pytest.mark.asyncio
async def test_full_pipeline_with_fake_adapter():
    """Test the full agent pipeline with fake adapter"""

    # Load scenario
    scenario = load_test_scenario()

    # Create adapters (we'll use the same fake adapter for all agents for simplicity)
    # In production, you might use different models for different agents
    adapter = FakeAdapter("perfect")

    # 1. Generate questions
    questioner = QuestionerAgent(adapter)
    questions = questioner.generate_questions_simple(scenario)

    assert len(questions["turns"]) > 0
    first_question = questions["turns"][0]["user_message"]

    # 2. Get response from "target model" (using fake adapter)
    # In real usage, this would be a different model being evaluated
    target_adapter = FakeAdapter("perfect")
    response = await target_adapter.generate(
        messages=[{"role": "user", "content": first_question}],
        temperature=0.0,
    )

    assert response.content
    assert "Medicare" in response.content

    # 3. Extract claims
    extractor = ExtractorAgent(adapter)
    extraction_result = await extractor.extract_claims(response.content)

    assert len(extraction_result.claims) > 0
    print(f"\nExtracted {len(extraction_result.claims)} claims")

    # 4. Verify claims (run 2 verifiers)
    verifier1 = VerifierAgent(adapter, verifier_id="V1")
    verifier2 = VerifierAgent(adapter, verifier_id="V2")

    verification1 = await verifier1.verify_claims(
        extraction_result.claims, scenario.answer_key
    )
    verification2 = await verifier2.verify_claims(
        extraction_result.claims, scenario.answer_key
    )

    assert len(verification1.verdicts) == len(extraction_result.claims)
    assert len(verification2.verdicts) == len(extraction_result.claims)
    print(f"Verifier 1: {len(verification1.verdicts)} verdicts")
    print(f"Verifier 2: {len(verification2.verdicts)} verdicts")

    # 5. Score and adjudicate
    scorer = ScorerAgent()  # Rule-based scorer, no adapter needed
    adjudicator = AdjudicatorAgent(scorer)

    adjudication = await adjudicator.adjudicate(
        claims=extraction_result.claims,
        verifications=[verification1, verification2],
        answer_key=scenario.answer_key,
    )

    assert adjudication.final_scores
    assert adjudication.final_scores.ship_classification
    print(f"\nFinal Classification: {adjudication.final_scores.ship_classification.value}")
    print(f"Completeness: {adjudication.final_scores.completeness_percentage:.1%}")
    print(f"Accuracy: {adjudication.final_scores.accuracy_percentage:.1%}")
    print(f"Disagreement: {adjudication.disagreement_percentage:.1%}")
    print(f"Justification: {adjudication.final_scores.justification}")


@pytest.mark.asyncio
async def test_different_response_types():
    """Test scoring with different fake response types"""

    scenario = load_test_scenario()
    adapter = FakeAdapter("perfect")

    response_types = ["perfect", "incomplete", "incorrect"]

    for response_type in response_types:
        print(f"\n\n=== Testing {response_type} response ===")

        target_adapter = FakeAdapter(response_type)
        response = await target_adapter.generate(
            messages=[{"role": "user", "content": "Tell me about Medicare"}],
            temperature=0.0,
        )

        extractor = ExtractorAgent(adapter)
        extraction = await extractor.extract_claims(response.content)

        verifier = VerifierAgent(adapter, verifier_id="V1")
        verification = await verifier.verify_claims(extraction.claims, scenario.answer_key)

        scorer = ScorerAgent()
        score = await scorer.score_trial(
            extraction.claims, verification.verdicts, scenario.answer_key
        )

        print(f"Response type: {response_type}")
        print(f"Classification: {score.ship_classification.value}")
        print(f"Completeness: {score.completeness_percentage:.1%}")
        print(f"Accuracy: {score.accuracy_percentage:.1%}")
        print(f"Errors: {score.error_categories}")


if __name__ == "__main__":
    # Run tests directly
    print("Running agent tests...\n")
    asyncio.run(test_questioner_simple())
    print("\n" + "=" * 60)
    asyncio.run(test_full_pipeline_with_fake_adapter())
    print("\n" + "=" * 60)
    asyncio.run(test_different_response_types())
    print("\n\nAll tests completed!")

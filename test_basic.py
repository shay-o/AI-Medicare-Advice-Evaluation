"""Basic standalone test - no dependencies required beyond Python 3.11+"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.adapters.fake_adapter import FakeAdapter
from src.agents import QuestionerAgent
from src.schemas import Scenario


async def test_basic_functionality():
    """Test basic agent functionality"""

    print("=" * 70)
    print("AI Medicare Evaluation Harness - Basic Functionality Test")
    print("=" * 70)

    # 1. Load scenario
    print("\n[1/5] Loading test scenario...")
    scenario_path = Path("scenarios/v1/scenario_001.json")
    with scenario_path.open() as f:
        scenario_data = json.load(f)

    scenario = Scenario(**scenario_data)
    print(f"✓ Loaded scenario: {scenario.title}")
    print(f"  - {len(scenario.answer_key.canonical_facts)} canonical facts")
    print(f"  - {len(scenario.answer_key.required_points)} required points")
    print(f"  - {len(scenario.scripted_turns)} scripted turns")

    # 2. Test questioner (simple mode - no LLM needed)
    print("\n[2/5] Testing Questioner Agent (simple mode)...")
    adapter = FakeAdapter("perfect")
    questioner = QuestionerAgent(adapter)

    questions = questioner.generate_questions_simple(scenario)
    print(f"✓ Generated {len(questions['turns'])} questions")
    print(f"  Q1: {questions['turns'][0]['user_message']}")

    # 3. Get fake response
    print("\n[3/5] Getting response from target model (fake adapter)...")
    target_adapter = FakeAdapter("perfect")
    response = await target_adapter.generate(
        messages=[
            {"role": "user", "content": questions["turns"][0]["user_message"]}
        ],
        temperature=0.0,
    )
    print(f"✓ Received response ({len(response.content)} characters)")
    print(f"  Model: {response.model_identifier}")
    print(f"  Tokens: {response.tokens_used.get('total', 0)}")
    print(f"  Preview: {response.content[:150]}...")

    # 4. Test schema validation
    print("\n[4/5] Testing schema validation...")
    from src.schemas import (
        Claim,
        ClaimType,
        Verdict,
        VerdictLabel,
        ScoreResult,
        SHIPClassification,
    )

    # Create a test claim
    test_claim = Claim(
        claim_id="C1",
        text="Medicare Advantage plans use provider networks",
        claim_type=ClaimType.FACTUAL,
        confidence="high",
        verifiable=True,
        quote_spans=[{"start": 0, "end": 50}],
    )
    print(f"✓ Created test claim: {test_claim.claim_id}")

    # Create a test verdict
    test_verdict = Verdict(
        claim_id="C1",
        label=VerdictLabel.SUPPORTED,
        evidence=["F8"],
        severity="none",
        notes="Matches answer key fact F8",
    )
    print(f"✓ Created test verdict: {test_verdict.label.value}")

    # Create a test score
    test_score = ScoreResult(
        ship_classification=SHIPClassification.ACCURATE_COMPLETE,
        completeness_percentage=0.85,
        accuracy_percentage=0.95,
        missing_required_points=[],
        error_categories=[],
        harm_categories=[],
        justification="Test score - all systems operational",
    )
    print(f"✓ Created test score: {test_score.ship_classification.value}")

    # 5. Test storage
    print("\n[5/5] Testing storage system...")
    from src.storage import ResultsStorage

    storage = ResultsStorage()
    run_dir = storage.create_run_directory("test_run")
    print(f"✓ Created run directory: {run_dir}")

    # Test saving intermediate results
    intermediate_file = storage.save_intermediate_results(
        trial_id="test_001",
        stage="test_stage",
        data={"test": "data", "claims": [test_claim.model_dump()]},
        run_dir=run_dir,
    )
    print(f"✓ Saved intermediate results: {intermediate_file.name}")

    print("\n" + "=" * 70)
    print("✓ All basic tests passed!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Install dependencies: pip install -e .")
    print("  2. Run full test suite: pytest tests/")
    print("  3. Set up API keys in .env file")
    print("  4. Implement orchestrator for end-to-end evaluation")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(test_basic_functionality())
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

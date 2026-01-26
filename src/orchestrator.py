"""Orchestrator - Coordinates the full evaluation pipeline"""

import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, will use system environment variables
    pass

from .adapters.base import BaseLLMAdapter
from .adapters.fake_adapter import FakeAdapter
from .adapters.mock_agent_adapter import MockAgentAdapter
from .agents import (
    AdjudicatorAgent,
    ExtractorAgent,
    QuestionerAgent,
    ScorerAgent,
    VerifierAgent,
)
from .schemas import (
    ConversationTurn,
    Scenario,
    TargetModelInfo,
    TrialFlags,
    TrialResult,
)
from .storage import ResultsStorage


class EvaluationOrchestrator:
    """Orchestrates the full evaluation pipeline"""

    def __init__(
        self,
        scenario: Scenario,
        target_adapter: BaseLLMAdapter,
        agent_adapter: BaseLLMAdapter,
        num_verifiers: int = 2,
        seed: int = 42,
        storage: ResultsStorage | None = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            scenario: The test scenario to evaluate
            target_adapter: Adapter for the model being evaluated
            agent_adapter: Adapter for the evaluation agents (extractor, verifier)
            num_verifiers: Number of independent verifiers to run (default: 2)
            seed: Random seed for reproducibility
            storage: Storage instance (creates new one if None)
        """
        self.scenario = scenario
        self.target_adapter = target_adapter
        self.agent_adapter = agent_adapter
        self.num_verifiers = num_verifiers
        self.seed = seed
        self.storage = storage or ResultsStorage()

        # Initialize agents
        self.questioner = QuestionerAgent(agent_adapter)
        self.extractor = ExtractorAgent(agent_adapter)
        self.verifiers = [
            VerifierAgent(agent_adapter, verifier_id=f"V{i+1}")
            for i in range(num_verifiers)
        ]
        self.scorer = ScorerAgent()  # Rule-based scorer
        self.adjudicator = AdjudicatorAgent(self.scorer)

    async def run_evaluation(self, run_dir: Path | None = None) -> TrialResult:
        """
        Run the full evaluation pipeline.

        Args:
            run_dir: Directory to save results (creates new one if None)

        Returns:
            TrialResult with complete evaluation
        """
        # Create run directory if needed
        if run_dir is None:
            run_dir = self.storage.create_run_directory()

        trial_id = str(uuid.uuid4())[:8]

        print(f"\n{'='*70}")
        print(f"Starting Trial: {trial_id}")
        print(f"Scenario: {self.scenario.title}")
        print(f"Target: {self.target_adapter.get_model_identifier()}")
        print(f"{'='*70}\n")

        # Save run metadata
        self._save_run_metadata(run_dir)

        # Step 1: Generate questions
        print("[1/6] Generating questions...")
        questions = self.questioner.generate_questions_simple(self.scenario)
        print(f"  ✓ Generated {len(questions['turns'])} question(s)")

        # Step 2: Get target model responses
        print("\n[2/6] Querying target model...")
        conversation = await self._conduct_conversation(questions["turns"])
        print(f"  ✓ Received {len(conversation)} turn(s)")

        # Save raw transcript
        self.storage.save_raw_transcript(
            trial_id,
            [turn.model_dump() for turn in conversation],
            run_dir,
        )

        # Step 3: Extract claims from responses
        print("\n[3/6] Extracting claims...")
        all_claims = []
        for turn in conversation:
            if turn.role == "assistant":
                extraction = await self.extractor.extract_claims(
                    turn.content,
                    seed=self.seed,
                )
                all_claims.extend(extraction.claims)

        print(f"  ✓ Extracted {len(all_claims)} claim(s)")

        # Save extraction results
        self.storage.save_intermediate_results(
            trial_id,
            "extraction",
            {"claims": [c.model_dump() for c in all_claims]},
            run_dir,
        )

        # Step 4: Verify claims (run verifiers in parallel)
        print(f"\n[4/6] Verifying claims ({self.num_verifiers} verifiers)...")
        verification_tasks = [
            verifier.verify_claims(all_claims, self.scenario.answer_key, seed=self.seed)
            for verifier in self.verifiers
        ]
        verifications = await asyncio.gather(*verification_tasks)

        for i, verification in enumerate(verifications, 1):
            print(f"  ✓ Verifier {i}: {len(verification.verdicts)} verdict(s)")

        # Save verification results
        for i, verification in enumerate(verifications, 1):
            self.storage.save_intermediate_results(
                trial_id,
                f"verification_v{i}",
                verification.model_dump(),
                run_dir,
            )

        # Step 5: Score and adjudicate
        print("\n[5/6] Scoring and adjudicating...")
        adjudication = await self.adjudicator.adjudicate(
            claims=all_claims,
            verifications=verifications,
            answer_key=self.scenario.answer_key,
            scoring_rubric=self.scenario.scoring_rubric,
            seed=self.seed,
        )

        # Display classification
        if adjudication.final_scores.rubric_label:
            print(f"  ✓ Classification: {adjudication.final_scores.rubric_label} (Score {adjudication.final_scores.rubric_score})")
        print(f"  ✓ Completeness: {adjudication.final_scores.completeness_percentage:.1%}")
        print(f"  ✓ Accuracy: {adjudication.final_scores.accuracy_percentage:.1%}")
        print(f"  ✓ Disagreement: {adjudication.disagreement_percentage:.1%}")

        if adjudication.needs_manual_review:
            print("  ⚠ Flagged for manual review")

        # Save adjudication
        self.storage.save_intermediate_results(
            trial_id,
            "adjudication",
            adjudication.model_dump(),
            run_dir,
        )

        # Step 6: Detect flags and build final result
        print("\n[6/6] Finalizing results...")
        flags = self._detect_flags(conversation, all_claims, adjudication.final_verdicts)

        target_info = TargetModelInfo(
            provider=self._parse_provider(self.target_adapter),
            model_name=self.target_adapter.model_name,
            model_version=self.target_adapter.get_model_identifier(),
            parameters=self.scenario.target_parameters,
        )

        trial_result = TrialResult(
            trial_id=trial_id,
            scenario_id=self.scenario.scenario_id,
            target=target_info,
            conversation=conversation,
            claims=all_claims,
            verifications=verifications,
            final_scores=adjudication.final_scores,
            flags=flags,
            metadata={
                "num_verifiers": self.num_verifiers,
                "seed": self.seed,
                "agent_model": self.agent_adapter.get_model_identifier(),
            },
        )

        # Save final result
        results_file = self.storage.save_trial_result(trial_result, run_dir)
        print(f"  ✓ Saved results to: {results_file}")

        print(f"\n{'='*70}")
        print("Trial Complete!")
        print(f"{'='*70}\n")

        return trial_result

    async def _conduct_conversation(self, turns: list[dict[str, str]]) -> list[ConversationTurn]:
        """Conduct conversation with target model"""
        conversation = []
        messages = []

        for turn in turns:
            # Add user message
            user_turn = ConversationTurn(
                turn_id=turn["turn_id"],
                role="user",
                content=turn["user_message"],
            )
            conversation.append(user_turn)
            messages.append({"role": "user", "content": turn["user_message"]})

            # Get assistant response
            response = await self.target_adapter.generate(
                messages=messages,
                temperature=self.scenario.target_parameters.temperature,
                max_tokens=self.scenario.target_parameters.max_tokens,
                seed=self.scenario.target_parameters.seed,
            )

            assistant_turn = ConversationTurn(
                turn_id=f"{turn['turn_id']}_response",
                role="assistant",
                content=response.content,
            )
            conversation.append(assistant_turn)
            messages.append({"role": "assistant", "content": response.content})

        return conversation

    def _detect_flags(
        self,
        conversation: list[ConversationTurn],
        claims: list[Any],
        verdicts: list[Any],
    ) -> TrialFlags:
        """Detect special conditions in the response"""

        # Get assistant responses
        assistant_responses = [turn.content for turn in conversation if turn.role == "assistant"]
        full_response = " ".join(assistant_responses).lower()

        # Check for refusal
        refusal_phrases = [
            "i cannot",
            "i can't",
            "i'm not able to",
            "i should not",
            "i shouldn't",
            "not qualified",
            "cannot provide",
            "can't provide",
        ]
        refusal = any(phrase in full_response for phrase in refusal_phrases)

        # Check for hallucinated specifics (NOT_IN_KEY verdicts)
        from .schemas import VerdictLabel

        not_in_key_count = sum(1 for v in verdicts if v.label == VerdictLabel.NOT_IN_KEY)
        hallucinated_specifics = not_in_key_count > len(claims) * 0.2  # >20% not in key

        # Check for clarifying questions
        question_markers = ["what is your", "can you tell me", "could you provide", "?"]
        asked_clarifying_questions = any(marker in full_response for marker in question_markers)

        # Check for external resource references
        resource_markers = [
            "medicare.gov",
            "1-800-medicare",
            "call medicare",
            "contact medicare",
            "ship",
            "state health insurance",
        ]
        referenced_external_resources = any(marker in full_response for marker in resource_markers)

        return TrialFlags(
            refusal=refusal,
            hallucinated_specifics=hallucinated_specifics,
            asked_clarifying_questions=asked_clarifying_questions,
            referenced_external_resources=referenced_external_resources,
        )

    def _save_run_metadata(self, run_dir: Path) -> None:
        """Save metadata about this run"""
        metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "scenario_id": self.scenario.scenario_id,
            "scenario_title": self.scenario.title,
            "target_model": self.target_adapter.get_model_identifier(),
            "agent_model": self.agent_adapter.get_model_identifier(),
            "num_verifiers": self.num_verifiers,
            "seed": self.seed,
        }
        self.storage.save_run_metadata(run_dir, metadata)

    def _parse_provider(self, adapter: BaseLLMAdapter) -> str:
        """Extract provider name from adapter"""
        if isinstance(adapter, FakeAdapter):
            return "fake"

        # Extract from class name (e.g., OpenAIAdapter -> openai)
        class_name = adapter.__class__.__name__
        return class_name.replace("Adapter", "").lower()


def parse_target_spec(target_spec: str) -> tuple[str, str]:
    """
    Parse target specification string.

    Args:
        target_spec: String like "openai:gpt-4.1" or "fake:perfect"

    Returns:
        Tuple of (provider, model_name)
    """
    if ":" not in target_spec:
        raise ValueError(
            f"Invalid target spec '{target_spec}'. Expected format: 'provider:model_name'"
        )

    provider, model_name = target_spec.split(":", 1)
    return provider, model_name


def create_adapter(provider: str, model_name: str) -> BaseLLMAdapter:
    """
    Create an adapter for the specified provider and model.

    Args:
        provider: Provider name (e.g., "openai", "anthropic", "google", "xai", "fake")
        model_name: Model name (e.g., "gpt-4-turbo", "claude-3-5-sonnet-20241022", "perfect")

    Returns:
        Initialized adapter instance
    """
    provider_lower = provider.lower()

    if provider_lower == "fake":
        return FakeAdapter(response_type=model_name)

    elif provider_lower == "openai":
        try:
            from .adapters.openai_adapter import OpenAIAdapter
            return OpenAIAdapter(model_name=model_name)
        except ImportError as e:
            raise RuntimeError(
                f"OpenAI adapter requires 'openai' package. Install with: pip install openai>=1.0.0\n{e}"
            )

    elif provider_lower == "anthropic":
        try:
            from .adapters.anthropic_adapter import AnthropicAdapter
            return AnthropicAdapter(model_name=model_name)
        except ImportError as e:
            raise RuntimeError(
                f"Anthropic adapter requires 'anthropic' package. Install with: pip install anthropic>=0.18.0\n{e}"
            )

    elif provider_lower in ["google", "gemini"]:
        try:
            from .adapters.google_adapter import GoogleAdapter
            return GoogleAdapter(model_name=model_name)
        except ImportError as e:
            raise RuntimeError(
                f"Google adapter requires 'google-generativeai' package. Install with: pip install google-generativeai>=0.3.0\n{e}"
            )

    elif provider_lower in ["xai", "grok"]:
        try:
            from .adapters.xai_adapter import XAIAdapter
            return XAIAdapter(model_name=model_name)
        except ImportError as e:
            raise RuntimeError(
                f"xAI adapter requires 'openai' package. Install with: pip install openai>=1.0.0\n{e}"
            )

    elif provider_lower == "openrouter":
        try:
            from .adapters.openrouter_adapter import OpenRouterAdapter
            return OpenRouterAdapter(model_name=model_name)
        except ImportError as e:
            raise RuntimeError(
                f"OpenRouter adapter requires 'openai' package. Install with: pip install openai>=1.0.0\n{e}"
            )

    else:
        raise ValueError(
            f"Unknown provider '{provider}'. Supported providers: openai, anthropic, google, xai, openrouter, fake"
        )


async def run_evaluation_cli(args: argparse.Namespace) -> None:
    """Run evaluation from CLI arguments"""

    # Load scenario
    scenario_path = Path(args.scenario)
    if not scenario_path.exists():
        print(f"Error: Scenario file not found: {scenario_path}")
        sys.exit(1)

    with scenario_path.open() as f:
        scenario_data = json.load(f)

    scenario = Scenario(**scenario_data)

    # Parse target specification
    target_provider, target_model = parse_target_spec(args.target)

    # Create adapters
    target_adapter = create_adapter(target_provider, target_model)

    # For agents, use same model or default to mock
    if args.agent_model:
        agent_provider, agent_model = parse_target_spec(args.agent_model)
        agent_adapter = create_adapter(agent_provider, agent_model)
    else:
        # Default to mock adapter for agents during testing
        agent_adapter = MockAgentAdapter()

    # Create orchestrator
    storage = ResultsStorage(args.output_dir)
    orchestrator = EvaluationOrchestrator(
        scenario=scenario,
        target_adapter=target_adapter,
        agent_adapter=agent_adapter,
        num_verifiers=args.judges,
        seed=args.seed,
        storage=storage,
    )

    # Run evaluation
    run_dir = None
    if args.run_id:
        run_dir = storage.create_run_directory(args.run_id)

    result = await orchestrator.run_evaluation(run_dir)

    # Print summary
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Trial ID:          {result.trial_id}")
    print(f"Scenario:          {scenario.title}")
    print(f"Target Model:      {result.target.model_version}")
    if result.final_scores.rubric_label:
        print(f"Classification:    {result.final_scores.rubric_label} (Score {result.final_scores.rubric_score})")
    print(f"Completeness:      {result.final_scores.completeness_percentage:.1%}")
    print(f"Accuracy:          {result.final_scores.accuracy_percentage:.1%}")
    print(f"Claims Extracted:  {len(result.claims)}")
    print(f"Verifiers:         {len(result.verifications)}")
    print(f"Flags:")
    print(f"  - Refusal:       {result.flags.refusal}")
    print(f"  - Hallucinated:  {result.flags.hallucinated_specifics}")
    print(f"  - References:    {result.flags.referenced_external_resources}")
    print(f"\nJustification:")
    print(f"  {result.final_scores.justification}")
    print("=" * 70 + "\n")


def main() -> None:
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description="AI Medicare Evaluation Harness - Run evaluations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with fake adapter (for testing)
  python -m src.orchestrator run --scenario scenarios/v1/scenario_001.json --target fake:perfect

  # Run with different response types
  python -m src.orchestrator run --scenario scenarios/v1/scenario_001.json --target fake:incomplete
  python -m src.orchestrator run --scenario scenarios/v1/scenario_001.json --target fake:incorrect

  # Use multiple verifiers
  python -m src.orchestrator run --scenario scenarios/v1/scenario_001.json --target fake:perfect --judges 3

  # Specify custom run ID
  python -m src.orchestrator run --scenario scenarios/v1/scenario_001.json --target fake:perfect --run-id test_001
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run an evaluation")
    run_parser.add_argument(
        "--scenario",
        required=True,
        help="Path to scenario JSON file",
    )
    run_parser.add_argument(
        "--target",
        required=True,
        help="Target model specification (e.g., 'fake:perfect', 'openai:gpt-4.1')",
    )
    run_parser.add_argument(
        "--agent-model",
        help="Model for evaluation agents (default: fake:perfect)",
    )
    run_parser.add_argument(
        "--judges",
        type=int,
        default=2,
        help="Number of independent verifiers (default: 2)",
    )
    run_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    run_parser.add_argument(
        "--output-dir",
        default="runs",
        help="Output directory for results (default: runs/)",
    )
    run_parser.add_argument(
        "--run-id",
        help="Custom run ID (default: timestamp)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "run":
        asyncio.run(run_evaluation_cli(args))


if __name__ == "__main__":
    main()

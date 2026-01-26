"""Questioner Agent - Generates beneficiary questions from scenarios"""

import json
from pathlib import Path
from typing import Any

from ..adapters.base import BaseLLMAdapter
from ..schemas import Scenario


class QuestionerAgent:
    """Generates questions exactly as specified in the scenario"""

    def __init__(self, adapter: BaseLLMAdapter, system_prompt_path: str | None = None):
        """
        Initialize the questioner agent.

        Args:
            adapter: LLM adapter to use for generation
            system_prompt_path: Path to system prompt file (default: prompts/questioner_system.txt)
        """
        self.adapter = adapter

        if system_prompt_path is None:
            system_prompt_path = "prompts/questioner_system.txt"

        self.system_prompt = self._load_system_prompt(system_prompt_path)

    def _load_system_prompt(self, path: str) -> str:
        """Load system prompt from file"""
        prompt_file = Path(path)
        if not prompt_file.exists():
            raise FileNotFoundError(f"System prompt not found: {path}")
        return prompt_file.read_text()

    async def generate_questions(self, scenario: Scenario, seed: int = 42) -> dict[str, Any]:
        """
        Generate questions from a scenario.

        Args:
            scenario: The scenario to generate questions from
            seed: Random seed for reproducibility

        Returns:
            Dict with 'turns' key containing list of question turns
        """
        # Build input for the LLM
        user_input = {
            "scenario_id": scenario.scenario_id,
            "scripted_turns": [turn.model_dump() for turn in scenario.scripted_turns],
            "variation_knobs": scenario.variation_knobs,
            "persona": scenario.persona.model_dump(),
        }

        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": f"Generate questions for this scenario:\n\n{json.dumps(user_input, indent=2)}",
            },
        ]

        # Get response from LLM
        response = await self.adapter.generate(
            messages=messages,
            temperature=0.0,
            seed=seed if self.adapter.supports_seed() else None,
        )

        # Parse JSON response
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse questioner response as JSON: {e}\n{response.content}")

        # Validate output structure
        if "turns" not in result:
            raise ValueError(f"Questioner output missing 'turns' key: {result}")

        if not isinstance(result["turns"], list):
            raise ValueError(f"Questioner 'turns' must be a list: {result}")

        for turn in result["turns"]:
            if "turn_id" not in turn or "user_message" not in turn:
                raise ValueError(f"Invalid turn structure: {turn}")

        return result

    def generate_questions_simple(self, scenario: Scenario) -> dict[str, Any]:
        """
        Generate questions without LLM (deterministic, rule-based).

        This is a simpler version that just extracts questions from the scenario
        without LLM processing. Useful for testing or when variation is not needed.

        Args:
            scenario: The scenario to generate questions from

        Returns:
            Dict with 'turns' key containing list of question turns
        """
        # If paraphrasing is disabled, just return the scripted turns
        if not scenario.variation_knobs.get("allow_paraphrasing", False):
            return {
                "turns": [
                    {"turn_id": turn.turn_id, "user_message": turn.user_message}
                    for turn in scenario.scripted_turns
                ]
            }

        # If paraphrasing is enabled, we need to use the LLM
        raise ValueError(
            "Simple question generation requires allow_paraphrasing=False. "
            "Use generate_questions() for paraphrasing."
        )

"""Storage utilities for persisting evaluation results"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .schemas import TrialResult


class ResultsStorage:
    """Handles persisting and loading trial results"""

    def __init__(self, base_dir: str | Path = "runs"):
        """
        Initialize storage.

        Args:
            base_dir: Base directory for storing runs (default: 'runs/')
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def create_run_directory(self, run_id: str | None = None) -> Path:
        """
        Create a new run directory with timestamp.

        Args:
            run_id: Optional custom run ID (default: timestamp)

        Returns:
            Path to the created run directory
        """
        if run_id is None:
            run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        run_dir = self.base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        return run_dir

    def save_trial_result(self, trial_result: TrialResult, run_dir: Path) -> Path:
        """
        Save a trial result to a JSONL file (append-only).

        Args:
            trial_result: The trial result to save
            run_dir: Directory for this run

        Returns:
            Path to the results file
        """
        results_file = run_dir / "results.jsonl"

        # Convert to dict and serialize
        trial_dict = trial_result.model_dump(mode="json")

        # Append to JSONL file
        with results_file.open("a") as f:
            f.write(json.dumps(trial_dict) + "\n")

        return results_file

    def save_raw_transcript(
        self, trial_id: str, conversation: list[dict[str, Any]], run_dir: Path
    ) -> Path:
        """
        Save raw conversation transcript.

        Args:
            trial_id: Unique identifier for this trial
            conversation: List of conversation turns
            run_dir: Directory for this run

        Returns:
            Path to the transcript file
        """
        transcript_dir = run_dir / "transcripts"
        transcript_dir.mkdir(exist_ok=True)

        transcript_file = transcript_dir / f"{trial_id}.json"

        # Convert conversation to JSON-serializable format
        json_conversation = []
        for turn in conversation:
            if isinstance(turn, dict):
                json_conversation.append(turn)
            else:
                # Handle Pydantic models
                json_conversation.append(
                    turn if isinstance(turn, dict) else json.loads(
                        json.dumps(turn, default=str)
                    )
                )

        with transcript_file.open("w") as f:
            json.dump(
                {"trial_id": trial_id, "conversation": json_conversation},
                f,
                indent=2,
                default=str,  # Handle any remaining datetime/date objects
            )

        return transcript_file

    def save_intermediate_results(
        self,
        trial_id: str,
        stage: str,
        data: dict[str, Any],
        run_dir: Path,
    ) -> Path:
        """
        Save intermediate agent outputs for debugging.

        Args:
            trial_id: Unique identifier for this trial
            stage: Stage name (e.g., 'extraction', 'verification_v1')
            data: Data to save
            run_dir: Directory for this run

        Returns:
            Path to the intermediate results file
        """
        intermediate_dir = run_dir / "intermediate" / trial_id
        intermediate_dir.mkdir(parents=True, exist_ok=True)

        result_file = intermediate_dir / f"{stage}.json"

        with result_file.open("w") as f:
            json.dump(data, f, indent=2)

        return result_file

    def load_trial_results(self, run_dir: Path) -> list[TrialResult]:
        """
        Load all trial results from a run.

        Args:
            run_dir: Directory containing the run

        Returns:
            List of TrialResult objects
        """
        results_file = run_dir / "results.jsonl"

        if not results_file.exists():
            return []

        results = []
        with results_file.open("r") as f:
            for line in f:
                trial_dict = json.loads(line)
                results.append(TrialResult(**trial_dict))

        return results

    def save_run_metadata(self, run_dir: Path, metadata: dict[str, Any]) -> Path:
        """
        Save metadata about the run (configuration, timestamps, etc.).

        Args:
            run_dir: Directory for this run
            metadata: Metadata dictionary

        Returns:
            Path to metadata file
        """
        metadata_file = run_dir / "run_metadata.json"

        with metadata_file.open("w") as f:
            json.dump(metadata, f, indent=2)

        return metadata_file

    def list_runs(self) -> list[Path]:
        """
        List all run directories.

        Returns:
            List of run directory paths, sorted by creation time (newest first)
        """
        if not self.base_dir.exists():
            return []

        runs = [d for d in self.base_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        return sorted(runs, key=lambda x: x.stat().st_mtime, reverse=True)

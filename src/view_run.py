"""Utility to view run details in a human-readable format"""

import argparse
import json
import sys
from pathlib import Path


def view_run(run_dir: str, verbose: bool = False) -> None:
    """
    Display details of an evaluation run.

    Args:
        run_dir: Path to run directory or run ID
        verbose: Show detailed claim and verdict information
    """
    # Handle both full path and just run ID
    run_path = Path(run_dir)
    if not run_path.exists():
        run_path = Path("runs") / run_dir

    if not run_path.exists():
        print(f"Error: Run directory not found: {run_dir}")
        sys.exit(1)

    print("=" * 80)
    print(f"EVALUATION RUN: {run_path.name}")
    print("=" * 80)

    # 1. Load run metadata
    metadata_file = run_path / "run_metadata.json"
    if metadata_file.exists():
        with metadata_file.open() as f:
            metadata = json.load(f)

        print("\n[RUN METADATA]")
        print(f"  Timestamp:      {metadata.get('timestamp', 'N/A')}")
        print(f"  Scenario:       {metadata.get('scenario_title', 'N/A')}")
        print(f"  Target Model:   {metadata.get('target_model', 'N/A')}")
        print(f"  Agent Model:    {metadata.get('agent_model', 'N/A')}")
        print(f"  Verifiers:      {metadata.get('num_verifiers', 'N/A')}")
        print(f"  Seed:           {metadata.get('seed', 'N/A')}")

    # 2. Load results
    results_file = run_path / "results.jsonl"
    if not results_file.exists():
        print("\nError: results.jsonl not found")
        return

    with results_file.open() as f:
        result = json.loads(f.readline())

    # 3. Display conversation
    print("\n" + "=" * 80)
    print("[CONVERSATION]")
    print("=" * 80)

    for turn in result.get("conversation", []):
        role = turn.get("role", "unknown").upper()
        content = turn.get("content", "")

        if role == "USER":
            print(f"\n👤 USER:")
            print(f"   {content}")
        elif role == "ASSISTANT":
            print(f"\n🤖 ASSISTANT:")
            # Wrap long responses
            for line in content.split("\n"):
                if line:
                    print(f"   {line}")

    # 4. Display scoring summary
    print("\n" + "=" * 80)
    print("[EVALUATION SCORES]")
    print("=" * 80)

    scores = result.get("final_scores", {})
    print(f"\n  Classification:    {scores.get('ship_classification', 'N/A').upper()}")
    print(f"  Completeness:      {scores.get('completeness_percentage', 0):.1%}")
    print(f"  Accuracy:          {scores.get('accuracy_percentage', 0):.1%}")

    print(f"\n  Missing Required:  {', '.join(scores.get('missing_required_points', [])) or 'None'}")
    print(f"  Error Categories:  {', '.join(scores.get('error_categories', [])) or 'None'}")
    print(f"  Harm Categories:   {', '.join(scores.get('harm_categories', [])) or 'None'}")

    print(f"\n  Justification:")
    justification = scores.get('justification', 'N/A')
    for line in justification.split('. '):
        if line:
            print(f"    • {line.strip()}.")

    # 5. Display flags
    print("\n" + "=" * 80)
    print("[FLAGS]")
    print("=" * 80)

    flags = result.get("flags", {})
    print(f"  Refusal:                      {'✓' if flags.get('refusal') else '✗'}")
    print(f"  Hallucinated Specifics:       {'✓' if flags.get('hallucinated_specifics') else '✗'}")
    print(f"  Asked Clarifying Questions:   {'✓' if flags.get('asked_clarifying_questions') else '✗'}")
    print(f"  Referenced External Resources: {'✓' if flags.get('referenced_external_resources') else '✗'}")

    # 6. Display claims summary
    print("\n" + "=" * 80)
    print("[CLAIMS EXTRACTED]")
    print("=" * 80)

    claims = result.get("claims", [])
    print(f"\n  Total Claims: {len(claims)}")

    if verbose and claims:
        print("\n  Claim Details:")
        for i, claim in enumerate(claims[:10], 1):  # Show first 10
            print(f"\n    [{i}] {claim.get('claim_id')}: {claim.get('text')[:80]}...")
            print(f"        Type: {claim.get('claim_type')}, Confidence: {claim.get('confidence')}")
        if len(claims) > 10:
            print(f"\n    ... and {len(claims) - 10} more claims")

    # 7. Display verification summary
    print("\n" + "=" * 80)
    print("[VERIFICATION SUMMARY]")
    print("=" * 80)

    verifications = result.get("verifications", [])
    print(f"\n  Number of Verifiers: {len(verifications)}")

    # Count verdicts by label
    if verifications:
        from collections import Counter

        all_verdicts = []
        for verification in verifications:
            all_verdicts.extend(v.get("label") for v in verification.get("verdicts", []))

        verdict_counts = Counter(all_verdicts)

        print(f"\n  Verdict Distribution:")
        for label, count in verdict_counts.most_common():
            print(f"    {label:20s}: {count:3d}")

    if verbose and verifications:
        print(f"\n  Detailed Verdicts (from Verifier 1):")
        verdicts = verifications[0].get("verdicts", [])
        for i, verdict in enumerate(verdicts[:10], 1):
            claim_id = verdict.get("claim_id")
            label = verdict.get("label")
            evidence = verdict.get("evidence", [])
            severity = verdict.get("severity", "none")

            # Find corresponding claim text
            claim_text = "N/A"
            for claim in claims:
                if claim.get("claim_id") == claim_id:
                    claim_text = claim.get("text", "N/A")[:60]
                    break

            print(f"\n    [{i}] {claim_id}: {label}")
            print(f"        Claim: {claim_text}...")
            print(f"        Evidence: {', '.join(evidence) or 'None'}")
            if severity != "none":
                print(f"        Severity: {severity}")

        if len(verdicts) > 10:
            print(f"\n    ... and {len(verdicts) - 10} more verdicts")

    # 8. Display file locations
    print("\n" + "=" * 80)
    print("[FILES]")
    print("=" * 80)

    print(f"\n  Run Directory:     {run_path}")
    print(f"  Results:           {results_file}")

    transcript_dir = run_path / "transcripts"
    if transcript_dir.exists():
        transcripts = list(transcript_dir.glob("*.json"))
        if transcripts:
            print(f"  Transcript:        {transcripts[0]}")

    intermediate_dir = run_path / "intermediate"
    if intermediate_dir.exists():
        trial_dirs = list(intermediate_dir.glob("*"))
        if trial_dirs:
            print(f"  Intermediate:      {trial_dirs[0]}/")

    print("\n" + "=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="View evaluation run details in human-readable format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View latest run (auto-detect)
  python -m src.view_run

  # View specific run by ID
  python -m src.view_run 20260125_014231

  # View with detailed claims and verdicts
  python -m src.view_run --verbose 20260125_014231

  # View by full path
  python -m src.view_run runs/20260125_014231
        """,
    )

    parser.add_argument(
        "run_dir",
        nargs="?",
        help="Run directory or run ID (default: latest run)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed claim and verdict information",
    )

    args = parser.parse_args()

    # If no run specified, use latest
    if not args.run_dir:
        runs_dir = Path("runs")
        if not runs_dir.exists():
            print("Error: No runs directory found")
            sys.exit(1)

        # Find latest run (excluding test_run)
        runs = [d for d in runs_dir.iterdir() if d.is_dir() and d.name != "test_run"]
        if not runs:
            print("Error: No runs found")
            sys.exit(1)

        runs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        args.run_dir = str(runs[0])
        print(f"📊 Viewing latest run: {runs[0].name}\n")

    view_run(args.run_dir, args.verbose)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Enforce that evaluation runs are append-only.

Evaluation results are evidence. Once a run has been committed, editing it in
place rewrites history: a published verdict silently becomes a different verdict,
and anyone who cited the old number has no way to discover the change.

The rule is therefore: a re-grade writes a NEW run. It never edits an existing
one. Old and new sit side by side, and the manifest (reported_runs.json) decides
which is published -- a change that shows up as a reviewable diff.

Two checks run here, because runs/ is currently gitignored and git alone cannot
police files it does not track:

  1. Git check -- fails if a commit modifies or deletes an already-tracked file
     under runs/. Adding new runs is always allowed. (No-op while runs/ stays
     gitignored; becomes the primary guard if run data is ever committed.)

  2. Manifest check -- fails if any run named in reported_runs.json no longer
     hashes to its recorded value. This is what actually catches an in-place
     edit today, tracked or not.

Usage:
    python scripts/check_runs_append_only.py            # check staged changes
    python scripts/check_runs_append_only.py --range HEAD~5..HEAD
    python scripts/check_runs_append_only.py --skip-manifest

Install as a git hook:
    ln -sf ../../scripts/check_runs_append_only.py .git/hooks/pre-commit
    chmod +x scripts/check_runs_append_only.py

Bypass (only when you genuinely mean to rewrite evidence, e.g. redacting a leak):
    git commit --no-verify
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

WATCHED_PREFIX = "runs/"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        raise SystemExit(2)
    return result.stdout


def collect_violations(diff_output: str) -> list[tuple[str, str]]:
    violations: list[tuple[str, str]] = []
    for line in diff_output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        path = parts[-1]
        if not path.startswith(WATCHED_PREFIX):
            continue
        # A = added (fine). M/D/R = modification of existing evidence.
        code = status[0]
        if code in {"M", "D", "R"}:
            label = {"M": "modified", "D": "deleted", "R": "renamed"}[code]
            violations.append((label, path))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--range",
        dest="commit_range",
        help="Check a commit range instead of the staging area (e.g. HEAD~3..HEAD)",
    )
    parser.add_argument(
        "--skip-manifest",
        action="store_true",
        help="Only run the git check, not the manifest hash check",
    )
    args = parser.parse_args()

    failed = False

    # --- Check 1: git-tracked run files must not be modified or deleted -----
    if args.commit_range:
        diff = git("diff", "--name-status", args.commit_range)
        where = f"commit range {args.commit_range}"
    else:
        diff = git("diff", "--cached", "--name-status")
        where = "staged changes"

    violations = collect_violations(diff)
    if violations:
        failed = True
        print(f"BLOCKED: {where} would rewrite committed evaluation runs.\n", file=sys.stderr)
        for label, path in violations:
            print(f"  {label}: {path}", file=sys.stderr)
        print(file=sys.stderr)

    # --- Check 2: manifest hashes must still match what is on disk ----------
    if not args.skip_manifest:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        try:
            from run_manifest import (
                DEFAULT_MANIFEST,
                DEFAULT_RUNS_DIR,
                ManifestError,
                load_manifest,
                verify_manifest,
            )

            manifest = load_manifest(DEFAULT_MANIFEST)
            problems = verify_manifest(manifest, DEFAULT_RUNS_DIR)
            if problems:
                failed = True
                print("BLOCKED: runs no longer match reported_runs.json.\n", file=sys.stderr)
                for problem in problems:
                    print(f"  {problem}", file=sys.stderr)
                print(file=sys.stderr)
        except ManifestError as exc:
            failed = True
            print(f"BLOCKED: {exc}\n", file=sys.stderr)

    if not failed:
        return 0

    print(
        "Runs under runs/ are append-only. A re-grade should be written as a new\n"
        "run (use --output-dir / --run-id), then published by updating\n"
        "reported_runs.json:\n"
        "    python scripts/run_manifest.py build\n"
        "\nIf you genuinely intend to rewrite this evidence, bypass with:\n"
        "    git commit --no-verify",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

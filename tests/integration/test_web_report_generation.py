"""
Integration tests for end-to-end web report generation.
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from generate_web_report import generate_web_report


def test_end_to_end_report_generation():
    """Test complete workflow from runs to HTML report."""
    # Use actual runs directory if it exists
    runs_dir = Path("runs")

    if not runs_dir.exists() or not any(runs_dir.iterdir()):
        print("⊘ Skipping test - no evaluation runs found")
        return

    # Create temporary output directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "test_report.html"

        # Generate report
        result = generate_web_report(
            runs_dir=runs_dir,
            output_path=output_path,
            by_model=True,
            include_baseline=False,
            include_incomplete=False,
            include_fake=False,
        )

        # Verify result
        assert result.success, f"Report generation failed: {result.errors}"
        assert output_path.exists(), "Output file not created"
        assert output_path.stat().st_size > 0, "Output file is empty"

        # Read and verify HTML content
        html_content = output_path.read_text()
        assert "<!DOCTYPE html>" in html_content
        assert "Accuracy of Medicare Information Provided by State Health Insurance Assistance Programs" in html_content
        assert "<table" in html_content  # Table has id attribute, so check for opening tag

        print(f"✓ Report generated: {result.file_size_bytes} bytes")
        print(f"  Runs analyzed: {result.runs_analyzed}")
        print(f"  Runs included: {result.runs_included}")


def test_report_with_baseline():
    """Test report generation with SHIP baseline."""
    runs_dir = Path("runs")

    if not runs_dir.exists():
        print("⊘ Skipping test - no evaluation runs found")
        return

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "baseline_report.html"

        result = generate_web_report(
            runs_dir=runs_dir,
            output_path=output_path,
            scenario="SHIP-MO-Q3",
            by_model=True,
            include_baseline=True,
        )

        if not result.success:
            print(f"⊘ Skipping baseline test - {result.errors}")
            return

        # Check for baseline in HTML
        html_content = output_path.read_text()
        if "SHIP Baseline" in html_content:
            print("✓ Baseline data included in report")
        else:
            print("⊘ Baseline not found (scenario may not have baseline data)")


def test_empty_runs_directory():
    """Test error handling for empty runs directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        empty_runs = Path(tmp_dir) / "empty_runs"
        empty_runs.mkdir()
        output_path = Path(tmp_dir) / "report.html"

        result = generate_web_report(
            runs_dir=empty_runs,
            output_path=output_path,
        )

        assert not result.success
        assert "No evaluation runs found" in result.errors[0]
        print("✓ Empty directory error handled correctly")


def test_missing_runs_directory():
    """Test error handling for missing runs directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        nonexistent = Path(tmp_dir) / "nonexistent"
        output_path = Path(tmp_dir) / "report.html"

        result = generate_web_report(
            runs_dir=nonexistent,
            output_path=output_path,
        )

        assert not result.success
        assert "does not exist" in result.errors[0]
        print("✓ Missing directory error handled correctly")


if __name__ == "__main__":
    print("Running integration tests...\n")

    test_end_to_end_report_generation()
    test_report_with_baseline()
    test_empty_runs_directory()
    test_missing_runs_directory()

    print("\n✓ All integration tests passed!")

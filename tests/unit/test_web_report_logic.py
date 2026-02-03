"""
Unit tests for web report generation logic.
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from generate_web_report import (
    process_runs,
    create_score_distribution_from_dict,
    prepare_table_data,
    prepare_chart_data,
    ReportConfig,
)
from report_utils import calculate_score_distribution


def test_process_runs():
    """Test converting raw results to ProcessedRun objects."""
    # Sample result data
    results = [
        {
            "timestamp": "2026-01-25T01:39:42",
            "scenario_id": "SHIP-MO-Q3",
            "scenario": {"title": "MA vs TM Comparison"},
            "target": {"model_name": "openai/gpt-4-turbo", "provider": "openrouter"},
            "final_scores": {
                "rubric_score": 2,
                "completeness_percentage": 0.71,
                "accuracy_percentage": 1.0
            }
        }
    ]

    processed = process_runs(results)

    assert len(processed) == 1
    assert processed[0].scenario_id == "SHIP-MO-Q3"
    assert processed[0].model_name == "openai/gpt-4-turbo"
    assert processed[0].rubric_score == 2
    assert processed[0].completeness_pct == 71.0
    assert processed[0].accuracy_pct == 100.0
    assert processed[0].is_complete is True
    assert processed[0].is_fake is False


def test_calculate_score_distribution():
    """Test score distribution calculation."""
    results = [
        {
            "final_scores": {
                "rubric_score": 1,
                "completeness_percentage": 1.0,
                "accuracy_percentage": 1.0
            }
        },
        {
            "final_scores": {
                "rubric_score": 2,
                "completeness_percentage": 0.7,
                "accuracy_percentage": 1.0
            }
        },
        {
            "final_scores": {
                "rubric_score": 2,
                "completeness_percentage": 0.8,
                "accuracy_percentage": 1.0
            }
        },
    ]

    stats = calculate_score_distribution(results)

    assert stats["total"] == 3
    assert stats["scored_total"] == 3
    assert stats["score_1_count"] == 1
    assert stats["score_2_count"] == 2
    # Use approximate comparison for floats
    assert abs(stats["score_1_pct"] - 33.33) < 0.1  # ~1/3 * 100
    assert abs(stats["score_2_pct"] - 66.67) < 0.1  # ~2/3 * 100
    assert stats["incomplete_count"] == 0


def test_prepare_table_data_by_model():
    """Test table data preparation grouped by model."""
    results = [
        {
            "scenario_id": "SHIP-MO-Q3",
            "scenario": {"title": "MA vs TM"},
            "target": {"model_name": "model-a"},
            "final_scores": {"rubric_score": 1, "completeness_percentage": 1.0, "accuracy_percentage": 1.0}
        },
        {
            "scenario_id": "SHIP-MO-Q3",
            "scenario": {"title": "MA vs TM"},
            "target": {"model_name": "model-b"},
            "final_scores": {"rubric_score": 2, "completeness_percentage": 0.7, "accuracy_percentage": 1.0}
        },
    ]

    config = ReportConfig(
        group_by_model=True,
        include_baseline=False,
        scenario_filter="SHIP-MO-Q3"
    )

    sections = prepare_table_data(results, config)

    assert len(sections) == 1
    assert sections[0].section_title == "All Models"
    assert len(sections[0].rows) == 3  # Aggregate + 2 individual models

    # Verify aggregate row is first
    assert sections[0].rows[0].label == "All Models"
    assert sections[0].rows[0].css_class == "aggregate-row"

    # Verify individual models follow
    assert sections[0].rows[1].label in ["model-a", "model-b"]
    assert sections[0].rows[2].label in ["model-a", "model-b"]


def test_prepare_chart_data():
    """Test chart data preparation."""
    results = [
        {"final_scores": {"rubric_score": 1, "completeness_percentage": 1.0, "accuracy_percentage": 1.0}},
        {"final_scores": {"rubric_score": 2, "completeness_percentage": 0.7, "accuracy_percentage": 1.0}},
        {"final_scores": {"rubric_score": 2, "completeness_percentage": 0.8, "accuracy_percentage": 1.0}},
    ]

    config = ReportConfig()
    charts = prepare_chart_data(results, config)

    assert len(charts) == 1
    assert charts[0].chart_id == "scoreDistChart"
    assert len(charts[0].labels) == 4  # 4 score categories
    assert len(charts[0].datasets) == 1
    # Chart now uses percentages: 1/3 = 33.33%, 2/3 = 66.67%
    assert abs(charts[0].datasets[0].data[0] - 33.33) < 0.1  # Score 1: ~33.33%
    assert abs(charts[0].datasets[0].data[1] - 66.67) < 0.1  # Score 2: ~66.67%
    assert charts[0].datasets[0].data[2] == 0.0  # Score 3: 0%
    assert charts[0].datasets[0].data[3] == 0.0  # Score 4: 0%


if __name__ == "__main__":
    # Run tests
    test_process_runs()
    print("✓ test_process_runs passed")

    test_calculate_score_distribution()
    print("✓ test_calculate_score_distribution passed")

    test_prepare_table_data_by_model()
    print("✓ test_prepare_table_data_by_model passed")

    test_prepare_chart_data()
    print("✓ test_prepare_chart_data passed")

    print("\n✓ All unit tests passed!")

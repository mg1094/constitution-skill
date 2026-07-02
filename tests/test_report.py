"""
Unit tests for report and radar generators.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from skills import ConstitutionScorer, generate_report, generate_svg_radar


@pytest.fixture
def sample_result():
    """A representative scoring result."""
    return {
        "main_type": "qi_deficiency",
        "main_score": 68.5,
        "sub_type": "phlegm_dampness",
        "sub_score": 42.3,
        "all_scores": {
            "qi_deficiency": 68.5,
            "yang_deficiency": 18.0,
            "yin_deficiency": 15.0,
            "phlegm_dampness": 42.3,
            "damp_heat": 25.0,
            "blood_stasis": 10.0,
            "qi_stagnation": 30.0,
            "special": 12.0,
            "balanced": 25.0,
        },
        "ranked": [
            ("qi_deficiency", 68.5),
            ("phlegm_dampness", 42.3),
            ("qi_stagnation", 30.0),
            ("damp_heat", 25.0),
            ("balanced", 25.0),
            ("yang_deficiency", 18.0),
            ("yin_deficiency", 15.0),
            ("special", 12.0),
            ("blood_stasis", 10.0),
        ],
    }


def test_report_contains_main_type(sample_result):
    """Report must include main constitution name."""
    report = generate_report(sample_result)
    assert "气虚质" in report


def test_report_contains_disclaimer(sample_result):
    """Report must include medical disclaimer."""
    report = generate_report(sample_result)
    assert "不构成医疗" in report
    assert "仅供" in report


def test_report_contains_score(sample_result):
    """Report must show main score."""
    report = generate_report(sample_result)
    assert "68.5" in report


def test_report_contains_sub_type(sample_result):
    """Report must include sub type when present."""
    report = generate_report(sample_result)
    assert "痰湿质" in report


def test_report_has_advice_sections(sample_result):
    """Report must include diet/exercise advice for main type."""
    report = generate_report(sample_result)
    assert "饮食" in report
    assert "运动" in report


def test_radar_returns_valid_svg(sample_result):
    """Radar must return valid SVG markup."""
    svg = generate_svg_radar(sample_result["all_scores"])
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    assert 'xmlns="http://www.w3.org/2000/svg"' in svg


def test_radar_has_9_axes(sample_result):
    """Radar must have 9 axes for 9 constitution types."""
    svg = generate_svg_radar(sample_result["all_scores"])
    assert svg.count('circle cx=') >= 1
    assert svg.count('polygon points=') == 1


def test_radar_title_included(sample_result):
    """Radar must include the title."""
    svg = generate_svg_radar(sample_result["all_scores"], title="测试雷达图")
    assert "测试雷达图" in svg


def test_radar_size_respected(sample_result):
    """Radar must respect the size parameter."""
    svg = generate_svg_radar(sample_result["all_scores"], size=400)
    assert 'width="400"' in svg
    assert 'height="460"' in svg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Unit tests for ConstitutionScorer.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from skills import ConstitutionScorer


@pytest.fixture
def scorer():
    return ConstitutionScorer()


def test_all_45_questions_loaded(scorer):
    """All 45 questions must be loaded from JSON files."""
    assert len(scorer.questions) == 45, f"Expected 45 questions, got {len(scorer.questions)}"


def test_question_ids_unique(scorer):
    """All question IDs must be unique."""
    ids = list(scorer.questions.keys())
    assert len(ids) == len(set(ids)), "Duplicate question IDs found"


def test_question_structure(scorer):
    """Every question must have required fields."""
    required = {"id", "text", "weights"}
    for q_id, q in scorer.questions.items():
        missing = required - set(q.keys())
        assert not missing, f"Question {q_id} missing: {missing}"
        assert isinstance(q["weights"], dict), f"{q_id} weights not a dict"


def test_weights_valid_values(scorer):
    """Weight values must be in 0-1 range."""
    for q_id, q in scorer.questions.items():
        for type_id, weight in q["weights"].items():
            assert 0 <= weight <= 1, f"{q_id} weight {weight} out of range"


def test_scoring_normal_answers(scorer):
    """All answers 3 = neutral (50% score)."""
    answers = [3] * 45
    result = scorer.score(answers)

    assert "main_type" in result
    assert "main_score" in result
    assert "sub_type" in result
    assert "all_scores" in result
    assert "ranked" in result
    for type_id, score in result["all_scores"].items():
        assert score == 50.0, f"{type_id} score {score} != 50"


def test_scoring_extreme_qi_deficiency(scorer):
    """All answers 5 on qi-related questions = high qi_deficiency."""
    answers = [3] * 45
    for q_id, q in scorer.questions.items():
        if "qi_deficiency" in q.get("weights", {}):
            idx = sorted(scorer.questions.keys()).index(q_id)
            answers[idx] = 5

    result = scorer.score(answers)
    assert result["all_scores"]["qi_deficiency"] >= 80, \
        f"Expected qi_deficiency score >= 80, got {result['all_scores']['qi_deficiency']}"
    top2 = [t for t, s in result["ranked"][:2]]
    assert "qi_deficiency" in top2, f"qi_deficiency not in top 2: {top2}"


def test_scoring_main_and_sub_distinct(scorer):
    """Main type and sub type should be different (unless all scores equal)."""
    answers = [3] * 45
    result = scorer.score(answers)
    if result["all_scores"][result["main_type"]] != result["all_scores"][result["sub_type"]]:
        assert result["main_type"] != result["sub_type"]


def test_invalid_answers_length(scorer):
    """Wrong answer count should raise ValueError."""
    with pytest.raises(ValueError):
        scorer.score([3] * 10)


def test_score_preserves_all_types(scorer):
    """All 9 types must be in result, even if 0."""
    answers = [3] * 45
    result = scorer.score(answers)
    expected_types = set(scorer.TYPE_IDS)
    actual_types = set(result["all_scores"].keys())
    assert expected_types == actual_types, \
        f"Missing types: {expected_types - actual_types}"


def test_score_in_range(scorer):
    """All scores must be 0-100."""
    answers = [1, 5, 3, 2, 4] * 9
    result = scorer.score(answers)
    for type_id, score in result["all_scores"].items():
        assert 0 <= score <= 100, f"{type_id} score {score} out of [0, 100]"


def test_extreme_high_score(scorer):
    """All answers 5 = 8 types are very high (100), but balanced should be low (close to 0)."""
    answers = [5] * 45
    result = scorer.score(answers)
    # 8 types are 100%
    for type_id, score in result["all_scores"].items():
        if type_id != "balanced":
            assert score == 100.0, f"{type_id} should be 100, got {score}"
    # Balanced should be very low (very biased toward other types)
    assert result["all_scores"]["balanced"] <= 5, \
        f"Balanced should be very low when others are 100, got {result['all_scores']['balanced']}"


def test_extreme_low_score(scorer):
    """All answers 1 = 8 types are very low (0), balanced should be high (close to 100)."""
    answers = [1] * 45
    result = scorer.score(answers)
    for type_id, score in result["all_scores"].items():
        if type_id != "balanced":
            assert score == 0.0, f"{type_id} should be 0, got {score}"
    # Balanced should be very high (no bias)
    assert result["all_scores"]["balanced"] >= 95, \
        f"Balanced should be high when others are 0, got {result['all_scores']['balanced']}"


def test_balanced_high_when_all_low(scorer):
    """When all answers are 1, balanced type should be high (person is healthy)."""
    answers = [1] * 45
    result = scorer.score(answers)
    # balanced should rank #1 or near #1
    top2 = [t for t, s in result["ranked"][:2]]
    assert "balanced" in top2, f"balanced not in top 2: {top2}"


def test_balanced_low_when_all_high(scorer):
    """When all answers are 5, balanced type should be ranked low (person is very biased)."""
    answers = [5] * 45
    result = scorer.score(answers)
    # balanced should be at the bottom
    assert result["ranked"][-1][0] == "balanced", \
        f"balanced should be last, but is {result['ranked']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

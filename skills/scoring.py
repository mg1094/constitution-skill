"""
Constitution scoring algorithm.

Takes 60 user answers (1-5 each), scores 9 constitution types,
returns main + sub types with recommendations.
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple


class ConstitutionScorer:
    """9-constitution TCM scoring engine."""

    TYPE_IDS = [
        "qi_deficiency", "yang_deficiency", "yin_deficiency",
        "phlegm_dampness", "damp_heat",
        "blood_stasis", "qi_stagnation",
        "special", "balanced",
    ]

    TYPE_NAMES = {
        "qi_deficiency": "气虚质",
        "yang_deficiency": "阳虚质",
        "yin_deficiency": "阴虚质",
        "phlegm_dampness": "痰湿质",
        "damp_heat": "湿热质",
        "blood_stasis": "血瘀质",
        "qi_stagnation": "气郁质",
        "special": "特禀质",
        "balanced": "平和质",
    }

    def __init__(self, questions_dir: str = None):
        """Load question bank."""
        if questions_dir is None:
            questions_dir = Path(__file__).parent.parent / "questions"

        self.questions_dir = Path(questions_dir)
        self.config = self._load_config()
        self.questions = self._load_all_questions()

    def _load_config(self) -> dict:
        import yaml
        config_path = self.questions_dir / "config.json"
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)

    def _load_all_questions(self) -> Dict[str, dict]:
        """Load all question files and return flat dict."""
        all_questions = {}
        for category, info in self.config.get("categories", {}).items():
            file_path = self.questions_dir / info["file"]
            if not file_path.exists():
                continue
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            for q in data.get("questions", []):
                all_questions[q["id"]] = q
        return all_questions

    def score(self, answers: List[int]) -> dict:
        """
        Score a 60-question response.

        Args:
            answers: List of 60 integers (1-5)

        Returns:
            {
                "main_type": "qi_deficiency",
                "main_score": 68.5,
                "sub_type": "yang_deficiency",
                "sub_score": 42.3,
                "all_scores": {"qi_deficiency": 68.5, ...},
                "ranked": [("qi_deficiency", 68.5), ...]
            }
        """
        if len(answers) != len(self.questions):
            raise ValueError(
                f"Expected {len(self.questions)} answers, got {len(answers)}"
            )

        # 1. Accumulate weighted scores per type
        raw_scores = {t: 0.0 for t in self.TYPE_IDS}
        max_possible = {t: 0.0 for t in self.TYPE_IDS}

        for q_id, answer in zip(
            sorted(self.questions.keys()), answers
        ):
            q = self.questions[q_id]
            for type_id, weight in q.get("weights", {}).items():
                # Score: (answer - 1) / 4 maps 1-5 → 0-1
                contribution = (answer - 1) / 4.0 * weight
                raw_scores[type_id] += contribution
                max_possible[type_id] += weight

        # 2. Convert to standard score (0-100)
        # 转化分 = 原始分 / 最大可能分 × 100
        standard_scores = {}
        for type_id in self.TYPE_IDS:
            if max_possible[type_id] > 0:
                standard_scores[type_id] = (
                    raw_scores[type_id]
                    / max_possible[type_id]
                    * 100
                )
            else:
                standard_scores[type_id] = 0.0

        # 3. Special handling for balanced type
        # 平和质是"什么都不偏"的状态
        # 8 种体质得分都高 = 偏颇 → 平和质低
        # 8 种体质得分都低 = 不偏颇 → 平和质高
        # 用其他 8 种体质的平均分反映"偏颇程度"
        other_types = [t for t in self.TYPE_IDS if t != "balanced"]
        other_avg = sum(standard_scores[t] for t in other_types) / len(other_types)
        # 平和质分数 = 100 - 平均偏颇程度
        standard_scores["balanced"] = max(0, 100 - other_avg)

        # 4. Rank
        ranked = sorted(
            standard_scores.items(), key=lambda x: x[1], reverse=True
        )

        # 5. Determine main and sub type
        # Main: highest score
        # Sub: second highest score
        main_type = ranked[0][0]
        main_score = ranked[0][1]

        sub_type = ranked[1][0] if len(ranked) > 1 else None
        sub_score = ranked[1][1] if len(ranked) > 1 else 0

        return {
            "main_type": main_type,
            "main_score": round(main_score, 1),
            "sub_type": sub_type,
            "sub_score": round(sub_score, 1),
            "all_scores": {
                t: round(s, 1) for t, s in standard_scores.items()
            },
            "ranked": [(t, round(s, 1)) for t, s in ranked],
        }


def main():
    """Quick CLI test."""
    import sys
    import os

    # Default to balanced answers
    answers = [3] * 45

    # Test with qi_deficiency skew
    skewed = answers.copy()
    for i, q in enumerate(["E01", "E02", "E05", "E06", "E07"]):
        if q in [qq["id"] for qq in [
            json.load(open("questions/energy.json"))["questions"][i]
            for i in range(8)
        ]]:
            skewed[i] = 5

    scorer = ConstitutionScorer()
    result = scorer.score(skewed)

    print("=" * 50)
    print("中医体质检测结果")
    print("=" * 50)
    print(f"\n主体质: {scorer.TYPE_NAMES[result['main_type']]}")
    print(f"  转化分: {result['main_score']}")
    print(f"\n副体质: {scorer.TYPE_NAMES[result['sub_type']]}")
    print(f"  转化分: {result['sub_score']}")
    print(f"\n所有 9 维得分:")
    for t, s in sorted(
        result["all_scores"].items(), key=lambda x: -x[1]
    ):
        print(f"  {scorer.TYPE_NAMES[t]:6s} {s:6.1f}")
    print("\n⚠️  仅为体质倾向测试，不构成医疗建议。")


if __name__ == "__main__":
    main()

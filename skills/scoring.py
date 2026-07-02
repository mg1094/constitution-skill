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
                "ranked": [("qi_deficiency", 68.5), ...],
                "established": {"qi_deficiency": True, ...},
                "is_balanced": False
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
                # (answer - 1) / 4 maps 1-5 → 0-1
                contribution = (answer - 1) / 4.0 * weight
                raw_scores[type_id] += contribution
                max_possible[type_id] += weight

        # 2. Convert to transformation score (转化分, 0-100)
        # 国标: 转化分 = (原始分 - 题目数) / (题目数 × 4) × 100
        # 等价于: 加权 (answer-1)/4 的均值 × 100，权重统一时与国标一致
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

        # 4. Determine "established" (成立) types per national standard
        # 转化分 ≥ 30 → 该体质倾向成立
        ESTABLISHED_THRESHOLD = 30.0
        established = {
            t: s >= ESTABLISHED_THRESHOLD for t, s in standard_scores.items()
        }

        # 5. Rank all types by score
        ranked = sorted(
            standard_scores.items(), key=lambda x: x[1], reverse=True
        )

        # 6. Determine main and sub type with threshold logic
        # 若存在成立的偏颇体质 → 取分最高的偏颇体质为主体质
        # 若所有偏颇体质均不成立 → 主体质为平和质（无明显偏颇）
        biased_established = [
            (t, s) for t, s in ranked
            if t != "balanced" and established[t]
        ]

        if biased_established:
            main_type, main_score = biased_established[0]
            # 副体质: 下一高的成立体质（可为平和质或另一偏颇体质）
            sub_candidates = [
                (t, s) for t, s in ranked
                if established[t] and t != main_type
            ]
            sub_type, sub_score = (
                sub_candidates[0] if sub_candidates else (None, 0.0)
            )
            is_balanced = False
        else:
            # 无偏颇体质成立 → 平和质
            main_type = "balanced"
            main_score = standard_scores["balanced"]
            # 副体质: 分最高的偏颇倾向（即便未成立，也作为次要倾向提示）
            non_balanced = [(t, s) for t, s in ranked if t != "balanced"]
            sub_type, sub_score = (
                non_balanced[0] if non_balanced else (None, 0.0)
            )
            is_balanced = True

        return {
            "main_type": main_type,
            "main_score": round(main_score, 1),
            "sub_type": sub_type,
            "sub_score": round(sub_score, 1),
            "all_scores": {
                t: round(s, 1) for t, s in standard_scores.items()
            },
            "ranked": [(t, round(s, 1)) for t, s in ranked],
            "established": established,
            "is_balanced": is_balanced,
            "threshold": ESTABLISHED_THRESHOLD,
        }


def main():
    """Quick CLI test."""
    scorer = ConstitutionScorer()

    # 中性答案 + 把气虚类题目全部拉满，演示偏颇判定
    sorted_ids = sorted(scorer.questions.keys())
    answers = [3] * len(sorted_ids)
    for i, q_id in enumerate(sorted_ids):
        if "qi_deficiency" in scorer.questions[q_id].get("weights", {}):
            answers[i] = 5

    result = scorer.score(answers)

    print("=" * 50)
    print("中医体质检测结果")
    print("=" * 50)
    print(f"\n主体质: {scorer.TYPE_NAMES[result['main_type']]}")
    print(f"  转化分: {result['main_score']}")
    print(f"\n副体质: {scorer.TYPE_NAMES[result['sub_type']]}")
    print(f"  转化分: {result['sub_score']}")
    print(f"\n所有 9 维得分 (≥{result['threshold']} 为成立):")
    for t, s in sorted(
        result["all_scores"].items(), key=lambda x: -x[1]
    ):
        mark = "✓" if result["established"][t] else " "
        print(f"  {mark} {scorer.TYPE_NAMES[t]:6s} {s:6.1f}")
    print("\n⚠️  仅为体质倾向测试，不构成医疗建议。")


if __name__ == "__main__":
    main()

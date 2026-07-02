"""
CLI demo for constitution skill.

Run 60-question test with example answers,
print result and generate report.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from skills import ConstitutionScorer, generate_report, generate_svg_radar


def get_demo_answers() -> list:
    """Generate example answers showing qi_deficiency + phlegm_dampness tendency."""
    answers = [3] * 45
    # 气虚相关题加重
    qi_questions = ["E01", "E02", "E05", "E06", "E07"]
    for q_id in qi_questions:
        if q_id in [f"E0{i}" for i in range(1, 9)]:
            idx = [f"E0{i}" for i in range(1, 9)].index(q_id)
            answers[idx] = 5
    # 痰湿相关题加重
    moisture_qs = ["M01", "M02", "M03", "M04"]
    for q_id in moisture_qs:
        if q_id in [f"M{i:02d}" for i in range(1, 11)]:
            idx = [f"M{i:02d}" for i in range(1, 11)].index(q_id)
            answers[idx] = 5
    return answers


def main():
    print("=" * 50)
    print("中医体质检测 · CLI Demo")
    print("=" * 50)
    print()
    print("使用示例答案（气虚+痰湿偏重）...")
    print()

    answers = get_demo_answers()
    scorer = ConstitutionScorer()

    # 评分
    result = scorer.score(answers)
    main = scorer.TYPE_NAMES[result["main_type"]]
    sub = scorer.TYPE_NAMES[result["sub_type"]]

    print(f"主体质: {main} ({result['main_score']})")
    print(f"副体质: {sub} ({result['sub_score']})")
    print()
    print("9 维得分:")
    for t, s in result["ranked"]:
        name = scorer.TYPE_NAMES[t]
        bar = "█" * int(max(0, s) / 4)
        print(f"  {name:6s} {s:6.1f}  {bar}")
    print()

    # 生成报告
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    report = generate_report(result)
    report_path = output_dir / "demo-report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"📄 报告已保存: {report_path}")

    # 生成雷达图
    svg = generate_svg_radar(result["all_scores"], title="中医体质雷达图")
    svg_path = output_dir / "demo-radar.svg"
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"📊 雷达图已保存: {svg_path}")


if __name__ == "__main__":
    main()

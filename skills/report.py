"""
Constitution report generator.
Generates Markdown report from scoring result.
"""

import json
from pathlib import Path

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


def load_constitution_data() -> dict:
    """Load the 9-type constitution data."""
    data_path = Path(__file__).parent.parent / "assets" / "constitution-data.json"
    if not data_path.exists():
        return {}
    with open(data_path, encoding="utf-8") as f:
        return json.load(f)


def generate_report(score_result: dict) -> str:
    """
    Generate a Markdown report from scoring result.

    Args:
        score_result: Output from ConstitutionScorer.score()
    """
    data = load_constitution_data()
    types = data.get("types", {})

    main_type = score_result["main_type"]
    main_data = types.get(main_type, {})
    sub_type = score_result.get("sub_type")
    sub_data = types.get(sub_type, {}) if sub_type else {}
    all_scores = score_result["all_scores"]

    md = f"""# 你的中医体质报告

## 📊 测试概览

| 项 | 值 |
|---|---|
| 测试题数 | 45 |
| 主体质 | **{main_data.get('name', main_type)}** |
| 主体质转化分 | {score_result['main_score']} |
| 副体质 | {sub_data.get('name', sub_type) if sub_type else '—'} |
| 副体质转化分 | {score_result.get('sub_score', 0)} |
| 整体判定 | {"平和质（无明显偏颇）" if score_result.get('is_balanced') else "偏颇体质（需调养）"} |

---

## 🏷️ 你的主要体质

### {main_data.get('emoji', '')} {main_data.get('name', main_type)}

**{main_data.get('tagline', '')}**

#### 典型表现
{generate_features_list(main_data.get('features', []))}

#### 🌿 调养建议

**饮食**：
{generate_list(main_data.get('advice', {}).get('diet', []))}

**避免**：
{generate_list(main_data.get('advice', {}).get('avoid', []))}

**运动**：
{generate_list(main_data.get('advice', {}).get('exercise', []))}

**作息**：
{generate_list(main_data.get('advice', {}).get('lifestyle', []))}

**推荐食谱**：
{generate_list(main_data.get('advice', {}).get('food_recommend', []))}

---

"""

    if sub_data:
        md += f"""## 🌱 你的副体质

### {sub_data.get('emoji', '')} {sub_data.get('name', sub_type)}

**{sub_data.get('tagline', '')}**

**饮食调养**：
{generate_list(sub_data.get('advice', {}).get('diet', []))}

**避免**：
{generate_list(sub_data.get('advice', {}).get('avoid', []))}

**推荐食谱**：
{generate_list(sub_data.get('advice', {}).get('food_recommend', []))}

---

"""

    md += """## 📊 你的 9 维得分全图

> 转化分 ≥ 30 为该体质倾向成立（偏颇）；全部偏颇体质不成立时，主体质为平和质。

| 体质 | 转化分 | 判定 |
|------|------|------|
"""
    sorted_scores = sorted(
        all_scores.items(), key=lambda x: x[1], reverse=True
    )
    threshold = score_result.get("threshold", 30)
    established = score_result.get("established", {})
    for type_id, score in sorted_scores:
        name = TYPE_NAMES.get(type_id, type_id)
        is_est = established.get(type_id, score >= threshold)
        verdict = "✓ 偏颇成立" if is_est else "— 不成立"
        md += f"| {name} | {score} | {verdict} |\n"

    md += """
---

## ⚠️ 免责声明

⚠️  本报告由 AI 生成，**仅供娱乐和健康参考**，**不构成医疗诊断、治疗或预防建议**。
如有健康问题，请咨询专业医生进行诊断和治疗。

---

## 🔄 建议

- 建议每 3-6 个月复测一次
- 体质会随季节、年龄、生活方式变化
- 报告作为养生方向参考，不是医学结论

---

*报告生成于 AI 体质检测系统 · 仅供参考*
"""

    return md


def generate_features_list(features: list) -> str:
    """Generate a bulleted list of features."""
    if not features:
        return "- 暂无数据"
    return "\n".join(f"- {f}" for f in features)


def generate_list(items: list) -> str:
    """Generate a bulleted list."""
    if not items:
        return "- 暂无数据"
    return "\n".join(f"- {item}" for item in items)


if __name__ == "__main__":
    from skills.scoring import ConstitutionScorer
    test_answers = [3] * 45
    skewed = test_answers.copy()
    skewed[0] = 5
    skewed[1] = 5
    skewed[4] = 5
    skewed[5] = 5
    skewed[6] = 5

    scorer = ConstitutionScorer()
    result = scorer.score(skewed)
    report = generate_report(result)
    print(report)

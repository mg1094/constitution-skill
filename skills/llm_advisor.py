"""
LLM 体质解读模块

使用 OpenAI SDK 调用通义千问（兼容 OpenAI 接口），
根据体质评分结果生成个性化解读和调养建议。

配置方式（环境变量）：
    export OPENAI_API_KEY="sk-xxx"          # 通义千问 API Key
    export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
    export OPENAI_MODEL="qwen-plus"         # 或 qwen-max / qwen-turbo

也可以在代码中直接传入参数。
"""

import os
import json
from typing import Optional

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


# 体质中文名映射
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


SYSTEM_PROMPT = """你是一位经验丰富的中医体质辨识专家，擅长根据《中医体质分类与判定》标准解读体质检测结果。

你的任务：
1. 根据用户的 9 大体质得分，解读其体质特征
2. 给出个性化的饮食、运动、起居调养建议
3. 指出需要注意的健康风险
4. 语言通俗易懂，温暖亲切，避免过度医学术语

重要约束：
- 必须在末尾加上免责声明："本报告由 AI 生成，仅供健康参考，不构成医疗诊断或治疗建议。如有不适请咨询专业医生。"
- 不要编造具体药方或剂量
- 不要替代专业医疗建议
- 回答使用中文"""


def build_user_prompt(result: dict) -> str:
    """根据评分结果构建用户 prompt。"""
    main_type = result.get("main_type", "balanced")
    main_score = result.get("main_score", 0)
    sub_type = result.get("sub_type", "")
    sub_score = result.get("sub_score", 0)
    all_scores = result.get("all_scores", {})
    established = result.get("established", {})
    is_balanced = result.get("is_balanced", False)

    # 构建得分表
    score_lines = []
    for type_id, score in sorted(all_scores.items(), key=lambda x: -x[1]):
        name = TYPE_NAMES.get(type_id, type_id)
        status = "✅ 成立" if established.get(type_id) else "❌ 不成立"
        score_lines.append(f"  {name}: {score:.1f} 分 {status}")

    scores_text = "\n".join(score_lines)

    prompt = f"""请根据以下中医体质检测结果，为我生成一份个性化的体质解读报告。

## 我的体质检测结果

**主体质**: {TYPE_NAMES.get(main_type, main_type)}（转化分: {main_score:.1f}）
**副体质**: {TYPE_NAMES.get(sub_type, sub_type)}（转化分: {sub_score:.1f}）
**是否平和体质**: {"是" if is_balanced else "否"}

## 9 大体质完整得分

{scores_text}

## 请生成以下内容

1. **体质总评**（2-3 句话概括我的体质状况）
2. **主要特征解读**（我的主体质有什么典型表现）
3. **饮食调养建议**（宜吃什么、忌吃什么，具体到食材）
4. **运动建议**（适合什么运动、不适合什么、频率和时长）
5. **起居作息建议**（睡眠、季节调养、日常注意事项）
6. **情志调节建议**（心态、情绪管理）
7. **健康风险提醒**（需要注意的潜在问题）
8. **免责声明**

请用 Markdown 格式输出，语言温暖亲切。"""

    return prompt


def generate_llm_report(
    result: dict,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    调用 LLM 生成体质解读报告。

    Args:
        result: ConstitutionScorer.score() 的返回结果
        api_key: API Key（默认从环境变量 OPENAI_API_KEY 读取）
        base_url: API 地址（默认从环境变量 OPENAI_BASE_URL 读取）
        model: 模型名（默认从环境变量 OPENAI_MODEL 读取，或 qwen-plus）

    Returns:
        Markdown 格式的解读报告字符串
    """
    if not HAS_OPENAI:
        return _fallback_report(result)

    # 读取配置
    api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
    base_url = base_url or os.environ.get(
        "OPENAI_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    model = model or os.environ.get("OPENAI_MODEL", "qwen-plus")

    if not api_key:
        return _fallback_report(result)

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)

        user_prompt = build_user_prompt(result)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )

        return response.choices[0].message.content

    except Exception as e:
        # LLM 调用失败时回退到模板报告
        report = _fallback_report(result)
        return f"{report}\n\n---\n\n⚠️ AI 解读生成失败（{e}），以上为基础模板报告。"


def _fallback_report(result: dict) -> str:
    """LLM 不可用时的回退报告（模板生成）。"""
    main_type = result.get("main_type", "balanced")
    main_score = result.get("main_score", 0)
    sub_type = result.get("sub_type", "")
    sub_score = result.get("sub_score", 0)
    is_balanced = result.get("is_balanced", False)

    main_name = TYPE_NAMES.get(main_type, main_type)
    sub_name = TYPE_NAMES.get(sub_type, sub_type)

    # 基础建议数据
    ADVICE = {
        "qi_deficiency": {
            diet: "多吃山药、黄芪、大枣、蜂蜜；少吃生冷、油腻",
            exercise: "散步、太极、八段锦；避免剧烈运动",
            lifestyle: "充足睡眠，午休 30 分钟，避免过度劳累",
        }
        for diet, exercise, lifestyle in [(
            "多吃山药、黄芪、大枣、蜂蜜；少吃生冷、油腻",
            "散步、太极、八段锦；避免剧烈运动",
            "充足睡眠，午休 30 分钟，避免过度劳累",
        )]
    }

    # 简化版建议
    SIMPLE_ADVICE = {
        "qi_deficiency": ("补气：山药、黄芪、大枣", "散步、太极、八段锦", "充足睡眠，午休 30 分钟"),
        "yang_deficiency": ("温阳：生姜、羊肉、韭菜", "慢跑、泡脚、晒太阳", "注意保暖，晚泡脚"),
        "yin_deficiency": ("滋阴：银耳、百合、梨", "瑜伽、太极、冥想", "充足睡眠，多喝水"),
        "phlegm_dampness": ("祛湿：薏苡仁、赤小豆", "有氧运动，出汗排湿", "远离潮湿，不久坐"),
        "damp_heat": ("清热：绿豆、苦瓜、薏苡仁", "游泳、爬山", "戒烟限酒，清淡饮食"),
        "blood_stasis": ("活血：山楂、玫瑰花茶", "有氧运动、瑜伽", "保暖，心情舒畅"),
        "qi_stagnation": ("理气：玫瑰花茶、陈皮", "跑步、瑜伽、跳舞", "多社交，多倾诉"),
        "special": ("固表：黄芪、灵芝", "散步、瑜伽", "避过敏原，戴口罩"),
        "balanced": ("饮食有节，不偏食", "每周运动 3-5 次", "生活规律，心态平和"),
    }

    diet, exercise, lifestyle = SIMPLE_ADVICE.get(
        main_type, ("均衡饮食", "适度运动", "规律作息")
    )

    report = f"""# 🏥 体质解读报告

## 体质总评

您的主体质为 **{main_name}**（转化分: {main_score:.1f}）"""
    if sub_type and sub_type != main_type:
        report += f"""，副体质为 **{sub_name}**（转化分: {sub_score:.1f}）"""
    report += f"""。

{"✅ 恭喜！您的体质较为平和，请继续保持良好的生活习惯。" if is_balanced else "您的体质存在偏颇，建议根据以下建议进行调养。"}

## 主要特征

{main_name} 的典型表现请参考测试结果中的特征列表。

## 🌿 饮食调养

{diet}

## 🏃 运动建议

{exercise}

## 🌙 起居作息

{lifestyle}

---

⚠️ 本报告由 AI 生成，仅供健康参考，不构成医疗诊断或治疗建议。如有不适请咨询专业医生。"""

    return report

# 中医体质检测 Skill

> AI 时代的中医体质测试 · Skill · 45 道题 · 9 大体质 · 雷达图报告

## ✨ 这是什么

基于《中医体质分类与判定》标准的 AI 体质检测工具，
用 45 道题测出用户的 9 大体质倾向（主体质 + 副体质），生成可视化报告和调养建议。

⚠️ **仅供娱乐参考，不构成医疗建议。**

## 🚀 快速开始

### 在 AI Agent 中使用

```yaml
# SKILL.md metadata
name: constitution-test
version: 1.0.0
description: |
  中医九大体质检测工具。
  输入：45 道题的答案（每题 1-5 分）
  输出：主体质 + 副体质 + 调养建议
```

### 调用示例

```python
from scoring import ConstitutionScorer

answers = [3, 2, 5, 1, 4, ...]  # 45 道题的答案
result = ConstitutionScorer.score(answers)
print(result['main_type'])     # 'qi_deficiency'
print(result['sub_type'])      # 'yang_deficiency'
print(result['all_scores'])    # {type: percentage}
```

## 📁 仓库结构

```
constitution-skill/
├── SKILL.md              # 本文件：Skill 描述
├── README.md             # 项目介绍
├── LICENSE                # MIT
├── questions/             # 45 道题库
│   ├── energy.json        # 精力类（气虚，8 题）
│   ├── temperature.json  # 寒热类（阳虚/阴虚，10 题）
│   ├── moisture.json     # 湿气类（痰湿/湿热，10 题）
│   ├── emotion.json       # 情志类（气郁/血瘀，10 题）
│   ├── special.json       # 特禀类（过敏，7 题）
│   └── config.json        # 体质 → 题号映射
├── skills/                # 主代码
│   ├── __init__.py
│   ├── scoring.py         # 评分逻辑
│   ├── report.py          # 报告生成
│   └── radar.py           # 雷达图（SVG）
├── assets/
│   └── constitution-data.json  # 9 体质数据
├── web/
│   └── index.html         # 交互式 H5 界面
├── output/                # 输出示例
│   ├── report-sample.md   # 报告样例
│   └── radar-sample.svg   # 雷达图样例
└── examples/
    └── run-cli.py         # 命令行版本
```

## 🎯 9 大体质

| 体质 ID | 中文名 | 特征 | 关键词 |
|---------|--------|------|--------|
| balanced | 平和质 | 健康 | 面色润泽 |
| qi_deficiency | 气虚质 | 容易累 | 乏力、说话少 |
| yang_deficiency | 阳虚质 | 怕冷 | 手脚冰凉 |
| yin_deficiency | 阴虚质 | 手脚心热 | 干燥 |
| phlegm_dampness | 痰湿质 | 胖、困倦 | 油腻 |
| damp_heat | 湿热质 | 长痘、口苦 | 黏腻 |
| blood_stasis | 血瘀质 | 脸色暗、痛经 | 瘀斑 |
| qi_stagnation | 气郁质 | 心情差 | 叹气 |
| special | 特禀质 | 过敏 | 鼻炎、荨麻疹 |

## 📊 评分逻辑

每题 5 选 1：
- 没有 = 1 分
- 很少 = 2 分
- 有时 = 3 分
- 经常 = 4 分
- 总是 = 5 分

每道题对应 1-2 个体质（权重 0.5-1.0）。

**计算**：
1. 累加每体质的原始得分
2. 转化为转化分 = (原始分 - 题目数) / (题目数 × 4) × 100（国标 ZYYXH/T 157-2009）
3. 转化分 ≥ 30 → 该体质成立
4. 若存在成立的偏颇体质，取最高者为主体质；若全部偏颇体质不成立，主体质为平和质
5. 副体质取下一高的成立体质

## 📐 输出报告（示例）

```markdown
# 你的中医体质报告

## 📊 你的体质画像

雷达图（9 维度）

## 🏷️ 主要体质

**气虚质**（转化分 68）

- 容易疲乏
- 说话没劲
- 容易出汗

## 🌿 调养建议

### 饮食

- 多吃：山药、黄芪、红枣
- 少食：生冷、油腻

### 运动

- 推荐：八段锦、散步
- 避免：剧烈运动

### 作息

- 23:00 前睡觉
- 午休 30 分钟

## ⚠️ 免责声明

本报告由 AI 生成，仅供娱乐参考，
不构成医疗诊断或治疗建议。
如有健康问题，请咨询专业医生。
```

## 🛠️ 二次开发

### 加新题

```bash
# 编辑 questions/your-category.json
# 更新 questions/config.json 中的 mapping
# 运行 tests/test_scoring.py 验证
pytest tests/
```

### 接入 AI Agent

参考 SKILL.md 中的 metadata，按 AI Agent 平台的
skill 规范（如 Dify、Coze、Claude MCP）注册。

## 📜 许可证

MIT License

## ⚠️ 免责声明

本工具为 AI 体质倾向测试，仅供娱乐和健康参考。
**不构成医学诊断、治疗或预防建议。**
如有健康问题，请咨询专业医生。

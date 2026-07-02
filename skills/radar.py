"""
Constitution radar chart generator.
Generates SVG from scoring result.
"""

from typing import List, Dict
import math


def generate_svg_radar(
    scores: Dict[str, float],
    size: int = 600,
    title: str = "中医体质雷达图",
) -> str:
    """
    Generate an SVG radar chart for the 9 constitution types.

    Args:
        scores: Dict of type_id -> score (0-100)
        size: SVG canvas size (square)
        title: Chart title

    Returns:
        SVG string ready to embed
    """
    labels = list(scores.keys())
    n = len(labels)
    cx, cy = size / 2, size / 2
    radius = size * 0.32
    label_radius = size * 0.42

    color_palette = {
        "qi_deficiency": "#06B6D4",
        "yang_deficiency": "#0EA5E9",
        "yin_deficiency": "#84CC16",
        "phlegm_dampness": "#F59E0B",
        "damp_heat": "#EF4444",
        "blood_stasis": "#8B5CF6",
        "qi_stagnation": "#EC4899",
        "special": "#14B8A6",
        "balanced": "#10B981",
    }

    angles = []
    for i in range(n):
        angle = -math.pi / 2 + 2 * math.pi * i / n
        angles.append(angle)

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size + 60}" viewBox="0 0 {size} {size + 60}">',
        '<defs>',
        '<linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">',
        '<stop offset="0%" stop-color="#0F172A"/>',
        '<stop offset="100%" stop-color="#1E293B"/>',
        '</linearGradient>',
        '<linearGradient id="radar" x1="0%" y1="0%" x2="100%" y2="100%">',
        '<stop offset="0%" stop-color="#06B6D4"/>',
        '<stop offset="50%" stop-color="#84CC16"/>',
        '<stop offset="100%" stop-color="#F59E0B"/>',
        '</linearGradient>',
        '</defs>',
        f'<rect width="{size}" height="{size + 60}" fill="url(#bg)"/>',
        f'<text x="{size/2}" y="30" font-family="sans-serif" font-size="20" fill="white" text-anchor="middle" font-weight="bold">{title}</text>',
    ]

    # Grid circles
    for r in [0.25, 0.5, 0.75, 1.0]:
        svg_parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r * radius}" fill="none" stroke="#475569" stroke-width="0.5" stroke-dasharray="2 4" opacity="0.5"/>'
        )

    # Grid lines (axes)
    for angle in angles:
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        svg_parts.append(
            f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="#475569" stroke-width="0.5" opacity="0.5"/>'
        )

    # Score polygon
    points = []
    for i, label in enumerate(labels):
        score = max(0, min(100, scores[label]))
        ratio = score / 100
        x = cx + (radius * ratio) * math.cos(angles[i])
        y = cy + (radius * ratio) * math.sin(angles[i])
        points.append(f"{x},{y}")

    polygon_points = " ".join(points)
    svg_parts.append(
        f'<polygon points="{polygon_points}" fill="url(#radar)" fill-opacity="0.4" stroke="#06B6D4" stroke-width="2"/>'
    )

    # Score dots
    for point in points:
        x, y = point.split(",")
        svg_parts.append(
            f'<circle cx="{x}" cy="{y}" r="4" fill="#06B6D4" stroke="white" stroke-width="1.5"/>'
        )

    # Labels
    label_mapping = {
        "qi_deficiency": "气虚",
        "yang_deficiency": "阳虚",
        "yin_deficiency": "阴虚",
        "phlegm_dampness": "痰湿",
        "damp_heat": "湿热",
        "blood_stasis": "血瘀",
        "qi_stagnation": "气郁",
        "special": "特禀",
        "balanced": "平和",
    }
    for i, label in enumerate(labels):
        x = cx + label_radius * math.cos(angles[i])
        y = cy + label_radius * math.sin(angles[i])
        color = color_palette.get(label, "#06B6D4")
        text = label_mapping.get(label, label)
        # Adjust text alignment based on position
        anchor = "middle"
        if x < cx - 10:
            anchor = "end"
        elif x > cx + 10:
            anchor = "start"
        # Adjust y for vertical centering
        dy = 5
        svg_parts.append(
            f'<text x="{x}" y="{y + dy}" font-family="sans-serif" font-size="14" fill="{color}" text-anchor="{anchor}" font-weight="bold">{text}</text>'
        )

    # Add score markers
    for r in [25, 50, 75]:
        y_pos = cy - r / 100 * radius + 3
        svg_parts.append(
            f'<text x="{cx + 5}" y="{y_pos}" font-family="sans-serif" font-size="10" fill="#94A3B8">{r}</text>'
        )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


if __name__ == "__main__":
    test_scores = {
        "qi_deficiency": 68,
        "yang_deficiency": 42,
        "yin_deficiency": 15,
        "phlegm_dampness": 20,
        "damp_heat": 25,
        "blood_stasis": 10,
        "qi_stagnation": 30,
        "special": 12,
        "balanced": 25,
    }
    svg = generate_svg_radar(test_scores)
    with open("output/radar-sample.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("Radar chart saved to output/radar-sample.svg")

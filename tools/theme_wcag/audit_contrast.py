#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CudaText UI 主题对比度审计（WCAG 2.1）。

只读审计：扫描 app/data/themes/*.cuda-theme-ui，按 doc/DESIGN-TOKENS.md 第 2 节的
判定规则计算前景/背景组合对比度，产出报告与修正建议值。

默认不修改任何主题文件。修正建议写入 tools/theme_wcag/theme_patches.json，
需人工确认后才应用。

兼容 Python 3.8（CudaText 内嵌版本）。
"""

import colorsys
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # 仓库根目录
THEME_DIR = ROOT / "app" / "data" / "themes"        # 源码树中的主题目录
OUT_DIR = Path(__file__).resolve().parent            # tools/theme_wcag

# (前景 token, 背景 token, 最低对比度, 分类, 备注)
# 分类 text=正文文字(>=4.5), graphic=非文本图形(>=3), weak=弱化元素(仅报告)
PAIRS = [
    ("EdTextFont",         "EdTextBg",          4.5, "text",    "编辑器正文"),
    ("EdSelFont",          "EdSelBg",           4.5, "text",    "选区文字"),
    ("EdDisableFont",      "EdDisableBg",       4.5, "text",    "只读区文字"),
    ("EdLinks",            "EdTextBg",          4.5, "text",    "文内链接"),
    ("EdUnprintHexFont",   "EdUnprintBg",       4.5, "text",    "十六进制视图"),
    ("OtherTextFont",      "OtherTextBg",       4.5, "text",    "输出面板文字"),
    ("EdGutterFont",       "EdGutterBg",        4.5, "text",    "行号"),
    ("EdGutterCaretFont",  "EdGutterCaretBg",   4.5, "text",    "当前行行号"),
    ("EdRulerFont",        "EdRulerBg",         4.5, "text",    "标尺数字"),
    ("EdFoldMarkFont",     "EdFoldMarkBg",      4.5, "text",    "折行标记符号"),
    ("EdComboArrow",       "EdComboArrowBg",    3.0, "graphic", "内嵌下拉箭头"),
    ("TabFont",            "TabPassive",        4.5, "text",    "非激活标签文字"),
    ("TabFont",            "TabBg",             4.5, "text",    "标签栏文字"),
    ("TabFontMod",         "TabPassive",        4.5, "text",    "已修改标签文字"),
    ("TabCloseX",          "TabCloseBg",        3.0, "graphic", "标签关闭叉号"),
    ("SideBadgeFont",      "SideBadgeBg",       4.5, "text",    "侧栏徽标"),
    ("TreeFont",           "TreeBg",            4.5, "text",    "代码树节点"),
    ("TreeSelFont",        "TreeSelBg",         4.5, "text",    "代码树选中节点"),
    ("ListFont",           "ListBg",            4.5, "text",    "命令面板/补全列表"),
    ("ListSelFont",        "ListSelBg",         4.5, "text",    "列表选中项"),
    ("ListFontHotkey",     "ListBg",            4.5, "text",    "列表快捷键提示"),
    ("ListCompleteParams", "ListBg",            4.5, "text",    "补全参数提示"),
    ("ButtonFont",         "ButtonBgPassive",   4.5, "text",    "按钮文字"),
    ("ButtonFontDisabled", "ButtonBgDisabled",  3.0, "graphic", "禁用按钮（允许弱化）"),
    ("MenuFont",           "MenuBg",            4.5, "text",    "菜单文字"),
    ("MenuFontHotkey",     "MenuBg",            4.5, "text",    "菜单快捷键"),
    ("StatusFont",         "StatusBg",          4.5, "text",    "状态栏文字"),
    ("EdUnprintFont",      "EdUnprintBg",       3.0, "weak",    "不可打印字符（刻意弱化）"),
    ("EdIndentVLine",      "EdTextBg",          3.0, "graphic", "缩进参考线"),
    ("EdBlockStaple",      "EdTextBg",          3.0, "graphic", "代码块括号连线"),
    ("EdMicromapViewBg",   "EdMicromapBg",      3.0, "graphic", "微缩图视口块"),
    ("EdMicromapOccur",    "EdMicromapBg",      3.0, "graphic", "微缩图命中点"),
    ("ScrollFill",         "ScrollBack",        3.0, "graphic", "滚动条滑块"),
    ("ScrollArrow",        "ScrollBack",        3.0, "graphic", "滚动条箭头"),
]

HEX_RE = __import__("re").compile(r"^#[0-9A-Fa-f]{6}$")


def parse_theme(path):
    """主题文件是 JSON；容错处理 BOM 与 // 整行注释。"""
    lines = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.lstrip().startswith("//"):
            continue
        lines.append(line)
    return json.loads("\n".join(lines))


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(color):
    h = color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(fg, bg):
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def _to_hex(r, g, b):
    return "#%02X%02X%02X" % (
        max(0, min(255, round(r * 255))),
        max(0, min(255, round(g * 255))),
        max(0, min(255, round(b * 255))),
    )


def _rgb(color):
    h = color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _distance(c1, c2):
    """与原色的感知距离，用于在所有可行解里挑改动最小的一个。"""
    a, b = _rgb(c1), _rgb(c2)
    return sum((x - y) ** 2 for x, y in zip(a, b))


def _worst_ratio(cand, constraints):
    return min(contrast(cand, bg) / threshold for bg, threshold in constraints)


def suggest(fg, constraints):
    """求解同时满足全部 (背景, 阈值) 约束、且离原色最近的建议色。"""
    hue, light, sat = colorsys.rgb_to_hls(*_rgb(fg))
    candidates = []

    for sat_scale in (1.0, 0.85, 0.7, 0.5, 0.3, 0.0):
        s = sat * sat_scale
        for step in range(0, 101):
            for direction in (1.0, -1.0):
                new_light = light + direction * step / 100.0
                if new_light < 0.0 or new_light > 1.0:
                    continue
                cand = _to_hex(*colorsys.hls_to_rgb(hue, new_light, s))
                if not HEX_RE.match(cand):
                    continue
                if _worst_ratio(cand, constraints) >= 1.0:
                    candidates.append((_distance(fg, cand), cand))
    if not candidates:
        return None, 0.0
    _, best = min(candidates, key=lambda item: item[0])
    return best, _worst_ratio(best, constraints)


def audit():
    # 只审计基主题；*_wcag 是生成物，纳入会让统计随生成结果漂移
    themes = sorted(
        p for p in THEME_DIR.glob("*.cuda-theme-ui")
        if not p.stem.endswith("_wcag")
    )
    if not themes:
        print("未找到主题文件：%s" % THEME_DIR)
        return 1

    patches = {}
    rows = []
    for path in themes:
        name = path.name.replace(".cuda-theme-ui", "")
        try:
            tokens = parse_theme(path)
        except (ValueError, OSError) as exc:
            print("跳过 %s：解析失败 %s" % (path.name, exc))
            continue

        theme_rows = []
        constraints = {}
        need_fix = {}
        for fg_key, bg_key, threshold, kind, label in PAIRS:
            fg, bg = tokens.get(fg_key, ""), tokens.get(bg_key, "")
            if not fg or not bg:
                continue
            if not HEX_RE.match(fg) or not HEX_RE.match(bg):
                continue
            ratio = contrast(fg, bg)
            ok = ratio >= threshold
            row = {
                "theme": name, "label": label, "kind": kind,
                "fg_token": fg_key, "fg": fg,
                "bg_token": bg_key, "bg": bg,
                "threshold": threshold, "ratio": round(ratio, 2),
                "ok": ok,
            }
            theme_rows.append(row)
            constraints.setdefault(fg_key, []).append((bg, threshold))
            if not ok and kind != "weak":
                need_fix[fg_key] = fg

        theme_patch = {}
        for fg_key, fg in need_fix.items():
            cand, _fit = suggest(fg, constraints[fg_key])
            if cand:
                theme_patch[fg_key] = cand
            for row in theme_rows:
                if (row["fg_token"] == fg_key and not row["ok"]
                        and row["kind"] != "weak"):
                    row["suggest"] = cand
                    row["suggest_ratio"] = (
                        round(contrast(cand, row["bg"]), 2) if cand else None)
        rows.extend(theme_rows)
        if theme_patch:
            patches[name] = theme_patch

    (OUT_DIR / "theme_patches.json").write_text(
        json.dumps(patches, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    total = len(rows)
    failed = [r for r in rows if not r["ok"]]
    hard = [r for r in failed if r["kind"] != "weak"]
    fixable = [r for r in hard if r.get("suggest")]

    lines = [
        "# CudaText UI 主题对比度审计报告",
        "",
        "依据：doc/DESIGN-TOKENS.md 第 2 节判定规则；WCAG 2.1 相对亮度公式。",
        "审计对象：%d 套 UI 主题 × %d 组前景/背景配对。" % (len(themes), len(PAIRS)),
        "",
        "> **口径说明**：本报告由 `tools/theme_wcag/audit_contrast.py` 生成，",
        "> 只审计基主题（`app/data/themes/` 下除 `*_wcag` 之外的 UI 主题）；",
        "> `*_wcag` 是 `apply_patches.py` 的生成物，不参与审计。",
        "",
        "> **应用前必读**：建议值只保证「对比度达标」，不保证满足 DESIGN-TOKENS.md 第 5 节灰阶规范。",
        "> 图形类（缩进线、括号连线、滚动条滑块）与禁用态属于刻意弱化的视觉元素，",
        "> 是否强制拉到 3:1 应人工判断；强行拉高可能让辅助线抢走正文注意力。",
        "",
        "## 汇总",
        "",
        "| 项 | 数量 |",
        "|---|---|",
        "| 有效配对 | %d |" % total,
        "| 未达标 | %d |" % len(failed),
        "| 其中需修正（不含弱化元素） | %d |" % len(hard),
        "| 已给出自动修正建议 | %d |" % len(fixable),
        "",
        "> 空值 Token（如 MenuFont / StatusBg）表示继承系统主题，无法静态计算，已跳过。",
        "> `weak` 类（不可打印字符）为刻意弱化，仅报告不建议改。",
        "",
        "## 按主题汇总",
        "",
        "| 主题 | 有效配对 | 未达标 | 需修正 | 可自动修正 |",
        "|---|---|---|---|---|",
    ]
    for name in sorted(set(r["theme"] for r in rows)):
        sub = [r for r in rows if r["theme"] == name]
        sub_bad = [r for r in sub if not r["ok"]]
        sub_hard = [r for r in sub_bad if r["kind"] != "weak"]
        lines.append("| %s | %d | %d | %d | %d |" % (
            name, len(sub), len(sub_bad), len(sub_hard),
            len([r for r in sub_hard if r.get("suggest")])))
    lines += ["", "## 未达标明细（需修正项）", "",
              "| 主题 | 部位 | 前景 Token | 现值 | 背景 Token | 背景值 | 实测 | 要求 | 建议值 | 建议后 |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(hard, key=lambda x: (x["theme"], x["label"])):
        lines.append("| %s | %s | `%s` | %s | `%s` | %s | %.2f | %.1f | %s | %s |" % (
            r["theme"], r["label"], r["fg_token"], r["fg"], r["bg_token"], r["bg"],
            r["ratio"], r["threshold"], r.get("suggest") or "—",
            ("%.2f" % r["suggest_ratio"]) if r.get("suggest") else "—"))
    lines += ["", "## 弱化元素（仅记录，不建议修改）", ""]
    weak = [r for r in failed if r["kind"] == "weak"]
    if weak:
        lines += ["| 主题 | 部位 | 实测 | 参考值 |", "|---|---|---|---|"]
        for r in weak:
            lines.append("| %s | %s | %.2f | %.1f |" % (
                r["theme"], r["label"], r["ratio"], r["threshold"]))
    else:
        lines.append("无。")
    lines += ["", "## 修正值落盘", "",
              "全部建议值见 `tools/theme_wcag/theme_patches.json`。该脚本**不修改**任何主题文件；",
              "应用方式：`python tools/theme_wcag/apply_patches.py syn sub`，只新增 `*_wcag` 主题副本。", ""]

    report = "\n".join(lines)
    (OUT_DIR / "theme_contrast_report.md").write_text(report, encoding="utf-8")

    print("主题 %d 套，配对 %d 组，未达标 %d（需修正 %d，可自动修正 %d）" % (
        len(themes), total, len(failed), len(hard), len(fixable)))
    print("报告：tools/theme_wcag/theme_contrast_report.md")
    print("建议值：tools/theme_wcag/theme_patches.json")
    return 0


if __name__ == "__main__":
    sys.exit(audit())

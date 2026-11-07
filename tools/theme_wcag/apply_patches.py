#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 theme_patches.json 的建议值生成「可直接切换」的修正主题副本。

安全策略：只新增 `<name>_wcag.*` 主题文件，**不覆盖**任何现有主题。
原主题文件逐行原样保留，仅替换目标 Token 的色值，键名与顺序不变。
可选 `theme_overrides.json` 可覆盖或取消自动建议（值设为 null 表示保留源值）。

用法：
    python tools/theme_wcag/apply_patches.py              # 默认处理 syn / sub
    python tools/theme_wcag/apply_patches.py green navy  # 指定主题

兼容 Python 3.8。
"""

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THEME_DIR = ROOT / "app" / "data" / "themes"
PATCH_FILE = Path(__file__).resolve().parent / "theme_patches.json"
OVERRIDE_FILE = Path(__file__).resolve().parent / "theme_overrides.json"

TOKEN_RE = re.compile(r'^(\s*"([A-Za-z0-9_]+)"\s*:\s*)"#[0-9A-Fa-f]{6}"(.*)$')


def build_theme(name, patch):
    src_ui = THEME_DIR / (name + ".cuda-theme-ui")
    src_syn = THEME_DIR / (name + ".cuda-theme-syntax")
    if not src_ui.is_file():
        print("跳过 %s：找不到 %s" % (name, src_ui.name))
        return False

    out_lines = []
    applied = []
    for line in src_ui.read_text(encoding="utf-8-sig").splitlines(keepends=True):
        m = TOKEN_RE.match(line.rstrip("\r\n"))
        if m and m.group(2) in patch:
            new_val = patch[m.group(2)]
            newline = line.rstrip("\r\n")
            eol = "\r\n" if line.endswith("\r\n") else "\n"
            newline = m.group(1) + '"' + new_val + '"' + m.group(3)
            out_lines.append(newline + eol)
            applied.append((m.group(2), new_val))
        else:
            out_lines.append(line)

    dst_ui = THEME_DIR / (name + "_wcag.cuda-theme-ui")
    text = "".join(out_lines)
    json.loads(text)  # 落盘前校验，避免写出坏 JSON
    dst_ui.write_text(text, encoding="utf-8")

    if src_syn.is_file():
        shutil.copyfile(src_syn, THEME_DIR / (name + "_wcag.cuda-theme-syntax"))
        syn_note = "已复制配套 syntax 主题"
    else:
        syn_note = "无配套 syntax 主题（切换时需手动指定）"

    missing = sorted(set(patch) - set(k for k, _ in applied))
    print("[%s] 应用 %d 项 / 建议 %d 项；%s；产出 %s" % (
        name, len(applied), len(patch), syn_note, dst_ui.name))
    if missing:
        print("  警告：以下 Token 未在源文件中匹配到，未应用：%s" % ", ".join(missing))
    return True


def load_overrides():
    if not OVERRIDE_FILE.is_file():
        return {}
    return json.loads(OVERRIDE_FILE.read_text(encoding="utf-8"))


def effective_patch(name, patches, overrides):
    """自动建议 + 人工覆盖；值为 null 表示撤销该条建议、保留源主题原值。"""
    patch = dict(patches.get(name, {}))
    for key, value in overrides.get(name, {}).items():
        if value is None:
            patch.pop(key, None)
        else:
            patch[key] = value
    return patch


def main(argv):
    if not PATCH_FILE.is_file():
        print("缺少 %s，请先运行 tools/theme_wcag/audit_contrast.py" % PATCH_FILE.name)
        return 1
    patches = json.loads(PATCH_FILE.read_text(encoding="utf-8"))
    overrides = load_overrides()
    names = argv[1:] or ["syn", "sub"]

    ok = True
    for name in names:
        patch = effective_patch(name, patches, overrides)
        if not patch:
            print("跳过 %s：无修正建议" % name)
            continue
        ov_count = len(overrides.get(name, {}))
        try:
            ok = build_theme(name, patch) and ok
        except (OSError, ValueError) as exc:
            print("[%s] 失败：%s" % (name, exc))
            ok = False
        if ov_count:
            print("  已合并 theme_overrides.json 中 %d 条人工覆盖" % ov_count)
    print("\n未改动任何原始主题。回滚方式：删除 app/data/themes/*_wcag.* 四个文件。")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

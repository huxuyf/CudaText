# -*- coding: utf-8 -*-
"""宏的持久化与回放解析（纯逻辑层，不依赖 cudatext，可独立测试）。

CudaText 核心已内建录制：命令 cmd_MacroStart(2810) 切换开始/停止，
停止时通过 on_macro 事件把命令序列以 "\n" 分隔的文本交给插件。
本模块负责把这段文本存成命名宏，以及拆成可回放的动作列表。
"""

import datetime
import json
import os

STORE_FILE = "cuda_macro_manager.json"


def default_data():
    return {"version": 1, "macros": []}


def load(path):
    """读取宏库；文件缺失或损坏时返回空库，不抛异常到 UI。"""
    if not os.path.isfile(path):
        return default_data()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict) or not isinstance(data.get("macros"), list):
            return default_data()
        # 过滤结构不完整的条目，避免坏数据导致后续崩溃
        data["macros"] = [
            m for m in data["macros"]
            if isinstance(m, dict) and isinstance(m.get("name"), str)
            and isinstance(m.get("text"), str)
        ]
        return data
    except (OSError, ValueError) as exc:
        raise ValueError("宏库读取失败：%s" % exc)


def save(path, data):
    """原子写：先写临时文件再替换，避免写一半损坏原库。"""
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def add_macro(data, name, text):
    """同名覆盖，返回 (data, is_new)。name 为空或 text 为空时拒绝。"""
    name = (name or "").strip()
    if not name:
        raise ValueError("宏名称不能为空")
    if not (text or "").strip():
        raise ValueError("宏内容为空")
    entry = {
        "name": name,
        "text": text,
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    is_new = True
    for i, m in enumerate(data["macros"]):
        if m.get("name") == name:
            data["macros"][i] = entry
            is_new = False
            break
    if is_new:
        data["macros"].append(entry)
    return data, is_new


def parse_actions(text):
    """把 on_macro 的文本拆成回放动作。

    返回 list of dict：
      {"type": "cmd",  "code": int, "text": str}
      {"type": "plug", "spec": str}   # 直接交给 PROC_EXEC_PLUGIN
      {"type": "skip", "raw": str}    # 无法解析，回放时跳过并提示
    """
    actions = []
    for raw in (text or "").split("\n"):
        item = raw.strip()
        if not item:
            continue
        if item.startswith("py:"):
            spec = item[3:].strip()
            if spec:
                actions.append({"type": "plug", "spec": spec})
            else:
                actions.append({"type": "skip", "raw": item})
            continue
        code_s, sep, param = item.partition(",")
        try:
            code = int(code_s.strip())
        except ValueError:
            actions.append({"type": "skip", "raw": item})
            continue
        actions.append({"type": "cmd", "code": code,
                        "text": param if sep else ""})
    return actions

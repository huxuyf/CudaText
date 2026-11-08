# -*- coding: utf-8 -*-
"""统一命令面板的逻辑层：纯 Python，不依赖 cudatext，可独立单测。

前缀体系对标 VS Code：
  >      命令（来自 PROC_GET_COMMANDS）
  @      当前文件内符号
  :      跳转到行
  无前缀 文件（已打开 / 最近 / 项目内）

实现要点：核心命令面板无法被插件改写，但 dlg_menu 自带实时 fuzzy 过滤。
把前缀字符写进菜单项标签后，用户输入 ">" 时列表自然只剩命令项，
输入 "@" 只剩符号项，无需接管核心即可获得一步式前缀路由。

兼容 Python 3.8。
"""

import json
import os
import time

KIND_CMD = "cmd"
KIND_SYM = "symbol"
KIND_FILE = "file"
KIND_LINE = "line"

PREFIX_CMD = ">"
PREFIX_SYM = "@"
PREFIX_LINE = ":"

SKIP_DIRS = frozenset((
    ".git", ".svn", ".hg", "node_modules", "__pycache__", ".idea",
    ".vscode", ".venv", "venv", "dist", "build", "site-packages",
    "python38dlls", "target", "vendor",
))
MAX_FILES = 2000
MAX_DEPTH = 6
MAX_COMMANDS = 900
MAX_SYMBOLS = 600
MRU_LIMIT = 80

_KIND_ORDER = {KIND_CMD: 0, KIND_SYM: 1, KIND_FILE: 2, KIND_LINE: 3}


# ---------- MRU（最近使用） ----------

def load_mru(path):
    """读 MRU；文件不存在或损坏时返回空结构，绝不抛异常。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("items"), dict):
            return data
    except Exception:
        pass
    return {"items": {}}


def save_mru(path, data):
    """原子写。MRU 只是增强功能，失败时静默降级，不影响主流程。"""
    try:
        folder = os.path.dirname(path)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
        return True
    except Exception:
        return False


def mru_key(kind, ident):
    return "%s:%s" % (kind, ident)


def bump_mru(data, key, limit=MRU_LIMIT):
    items = data.setdefault("items", {})
    rec = items.get(key) or {"count": 0, "ts": 0}
    rec["count"] = int(rec.get("count", 0)) + 1
    rec["ts"] = int(time.time())
    items[key] = rec
    if len(items) > limit:
        keep = sorted(
            items.items(),
            key=lambda kv: (kv[1].get("ts", 0), kv[1].get("count", 0)),
            reverse=True,
        )[:limit]
        data["items"] = dict(keep)
    return data


def mru_score(data, key):
    rec = data.get("items", {}).get(key)
    if not isinstance(rec, dict):
        return (0, 0)
    return (int(rec.get("count", 0)), int(rec.get("ts", 0)))


def entry_key(item):
    """由条目反推 MRU 键。"""
    kind = item.get("kind")
    if kind == KIND_CMD:
        return mru_key(kind, str(item.get("code")))
    if kind == KIND_SYM:
        return mru_key(kind, item.get("label", "").lstrip(PREFIX_SYM + " "))
    if kind == KIND_FILE:
        return mru_key(kind, item.get("path") or item.get("label"))
    return mru_key(kind, item.get("label"))


# ---------- 路径工具 ----------

def display_file_name(name):
    name = str(name).replace("\\", "/")
    parts = [p for p in name.split("/") if p]
    return parts[-1] if parts else name


def relative_path(path, root):
    try:
        if root:
            a, b = os.path.abspath(path), os.path.abspath(root)
            if os.path.commonpath([a, b]) == b:
                return os.path.relpath(a, b).replace("\\", "/")
    except Exception:
        pass
    return os.path.basename(str(path))


def find_project_root(start_dir, max_up=8):
    """向上找 .git / .cuda-proj 作为项目根；找不到就用起始目录。"""
    if not start_dir or not os.path.isdir(start_dir):
        return ""
    cur = os.path.abspath(start_dir)
    for _ in range(max_up + 1):
        if any(os.path.isdir(os.path.join(cur, m)) for m in (".git", ".hg")):
            return cur
        try:
            if any(n.endswith(".cuda-proj") for n in os.listdir(cur)):
                return cur
        except OSError:
            pass
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.abspath(start_dir)


def scan_files(root, max_files=MAX_FILES, max_depth=MAX_DEPTH):
    """限量递归列文件，跳过依赖/构建目录。返回排序后的绝对路径列表。"""
    if not root or not os.path.isdir(root):
        return []
    root = os.path.abspath(root)
    out = []
    base_depth = root.rstrip(os.sep).count(os.sep)
    for cur, dirs, files in os.walk(root):
        depth = cur.rstrip(os.sep).count(os.sep) - base_depth
        if depth >= max_depth:
            dirs[:] = []
        else:
            dirs[:] = [d for d in dirs
                       if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in files:
            if fn.startswith("."):
                continue
            out.append(os.path.join(cur, fn))
            if len(out) >= max_files:
                return sorted(out)
    return sorted(out)


# ---------- 条目构造 ----------

def normalize_commands(raw, mru=None):
    """把 PROC_GET_COMMANDS 的 list[dict] 转成面板条目。

    openedfile / recentfile 转成文件条目，执行时仍走核心的 cmd code，
    这样切换标签页、重开最近文件都能复用核心行为，无需猜路径。
    """
    mru = mru or {"items": {}}
    out = []
    seen_files = set()
    cmd_count = 0
    for d in raw or []:
        if not isinstance(d, dict):
            continue
        typ = d.get("type", "")
        name = (d.get("name") or "").strip()
        code = d.get("cmd")
        if not name or not isinstance(code, int) or name == "-":
            continue

        if typ in ("openedfile", "recentfile"):
            key = (typ, name)
            if key in seen_files:
                continue
            seen_files.add(key)
            out.append({
                "kind": KIND_FILE,
                "label": display_file_name(name),
                "hint": ("已打开 · " if typ == "openedfile" else "最近 · ") + name,
                "path": name,
                "via_code": True,
                "code": code,
                "mru": mru_score(mru, mru_key(KIND_FILE, name)),
            })
            continue

        if typ not in ("cmd", "lexer", "plugin") or cmd_count >= MAX_COMMANDS:
            continue
        cmd_count += 1
        hint = d.get("key1") or ""
        if typ == "plugin" and d.get("p_module"):
            hint = (hint + " · " if hint else "") + str(d["p_module"])
        out.append({
            "kind": KIND_CMD,
            "label": "%s %s" % (PREFIX_CMD, name),
            "hint": hint,
            "code": code,
            "via_code": False,
            "mru": mru_score(mru, mru_key(KIND_CMD, str(code))),
        })
    return out


def add_symbols(items, syms, mru=None):
    mru = mru or {"items": {}}
    for s in (syms or [])[:MAX_SYMBOLS]:
        if not isinstance(s, dict):
            continue
        nm = (s.get("name") or "").strip()
        if not nm:
            continue
        line = int(s.get("line", 0))
        items.append({
            "kind": KIND_SYM,
            "label": "%s %s" % (PREFIX_SYM, nm),
            "hint": "L%d · %s" % (line + 1, s.get("kind", "")),
            "line": line,
            "mru": mru_score(mru, mru_key(KIND_SYM, nm)),
        })
    return items


def add_files(items, paths, root="", mru=None):
    mru = mru or {"items": {}}
    seen = set(i.get("path") for i in items if i.get("path"))
    for p in paths or []:
        if p in seen:
            continue
        seen.add(p)
        items.append({
            "kind": KIND_FILE,
            "label": relative_path(p, root),
            "hint": os.path.dirname(p),
            "path": p,
            "via_code": False,
            "mru": mru_score(mru, mru_key(KIND_FILE, p)),
        })
    return items


def add_line_item(items, line_count=0):
    hint = "1–%d，选中后输入行号" % line_count if line_count else "选中后输入行号"
    items.append({
        "kind": KIND_LINE,
        "label": "%s 跳转到行…" % PREFIX_LINE,
        "hint": hint,
        "mru": (0, 0),
    })
    return items


def sort_items(items):
    """MRU 优先；同权重按类别、名称聚合，保证前缀过滤后同类相邻。"""
    return sorted(items, key=lambda i: (
        -i.get("mru", (0, 0))[0],
        -i.get("mru", (0, 0))[1],
        _KIND_ORDER.get(i.get("kind"), 9),
        i.get("label", "").lower(),
    ))


def menu_lines(items):
    """生成 dlg_menu 的项；第二部分（\t 后）只作提示。"""
    out = []
    for i in items:
        hint = i.get("hint", "")
        out.append(i["label"] + ("\t" + hint if hint else ""))
    return out


def parse_line_number(text):
    """接受 '128' / ':128' / ' 128 '；非法返回 None。"""
    if text is None:
        return None
    s = str(text).strip()
    if s.startswith(PREFIX_LINE):
        s = s[1:].strip()
    if not s.isdigit():
        return None
    n = int(s)
    return n if n > 0 else None

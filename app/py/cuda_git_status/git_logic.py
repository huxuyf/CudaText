# -*- coding: utf-8 -*-
"""Git 状态查询与 diff 解析（纯逻辑层，不依赖 cudatext，可独立测试）。

设计取舍：
- 一律用参数列表调用 git，不用 shell=True，避免文件名里的特殊字符被解释。
- 所有外部调用带超时；git 缺失 / 非仓库 / 文件未跟踪均返回可判定的结果，
  不抛异常到 UI 层。
- 行号统一为 0-based，与 CudaText 的 PROP_LINE_STATE 对齐。
"""

import os
import re
import subprocess

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# 超过此行数不再逐行写 line-state，避免大文件下 UI 卡顿（推断值，可调）
MAX_LINES = 200000


def run_git(args, cwd, timeout=5):
    """返回 (returncode, stdout)；git 不可用或超时返回 (None, '')。"""
    if not cwd or not os.path.isdir(cwd):
        return None, ""
    try:
        proc = subprocess.run(
            ["git"] + list(args),
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return None, ""
    text = proc.stdout.decode("utf-8", errors="replace")
    return proc.returncode, text


def find_repo_root(file_path):
    """返回文件所在的 Git 仓库根目录；非仓库或未落盘返回 None。"""
    if not file_path or not os.path.isfile(file_path):
        return None
    folder = os.path.dirname(os.path.abspath(file_path))
    code, out = run_git(["rev-parse", "--show-toplevel"], folder)
    if code != 0 or not out.strip():
        return None
    root = out.strip().splitlines()[0]
    return os.path.normpath(root) if os.path.isdir(root) else None


def get_branch(root, timeout=5):
    """返回分支名；detached HEAD 返回短 commit id；查询失败返回 None。"""
    if not root:
        return None
    code, out = run_git(["symbolic-ref", "--quiet", "--short", "HEAD"], root, timeout)
    if code == 0 and out.strip():
        return out.strip().splitlines()[0]
    code, out = run_git(["rev-parse", "--short", "HEAD"], root, timeout)
    if code == 0 and out.strip():
        return out.strip().splitlines()[0]
    return None


def is_tracked(root, rel_path, timeout=5):
    code, _out = run_git(
        ["ls-files", "--error-unmatch", "--", rel_path], root, timeout)
    return code == 0


def parse_diff(diff_text):
    """解析 `git diff --unified=0` 输出。

    返回 (states, summary)：
      states  = {0-based 行号: 'added' | 'changed'}
      summary = {'added': int, 'changed': int, 'deleted': int}

    映射规则：
    - hunk 的新侧有行且旧侧为 0 行 -> 纯新增 -> 'added'
    - hunk 的新侧有行且旧侧也有行 -> 修改   -> 'changed'
    - 纯删除 hunk 在新文件里没有对应行，只计入 summary['deleted']
    """
    states = {}
    deleted = 0
    for line in diff_text.splitlines():
        m = HUNK_RE.match(line)
        if not m:
            continue
        _old_start, old_count_s, new_start, new_count_s = m.groups()
        old_count = int(old_count_s) if old_count_s is not None else 1
        new_start_i = int(new_start)
        new_count = int(new_count_s) if new_count_s is not None else 1

        if new_count == 0:
            # 纯删除 hunk：新文件里没有对应行，只计入删除数
            deleted += old_count
            continue
        kind = "added" if old_count == 0 else "changed"
        for offset in range(new_count):
            line_index = new_start_i - 1 + offset
            if line_index >= 0:
                # 修改优先于新增：同一行同时出现在两个 hunk 时不降级
                if kind == "changed" or line_index not in states:
                    states[line_index] = kind

    summary = {
        "added": sum(1 for v in states.values() if v == "added"),
        "changed": sum(1 for v in states.values() if v == "changed"),
        "deleted": deleted,
    }
    return states, summary


def get_diff_states(file_path):
    """返回 (root, branch, states, summary, note)。

    note 为可直接展示给用户的状态说明；出错时 states 为空 dict。
    """
    root = find_repo_root(file_path)
    if not root:
        return None, None, {}, {"added": 0, "changed": 0, "deleted": 0}, "非 Git 仓库"

    branch = get_branch(root)
    rel = os.path.relpath(os.path.abspath(file_path), root).replace(os.sep, "/")

    if not is_tracked(root, rel):
        return root, branch, {}, {"added": 0, "changed": 0, "deleted": 0}, "未跟踪文件"

    code, out = run_git(
        ["-c", "core.quotepath=false", "diff", "--no-ext-diff",
         "--no-color", "--unified=0", "HEAD", "--", rel],
        root, timeout=10)
    if code is None:
        return root, branch, {}, {"added": 0, "changed": 0, "deleted": 0}, "Git 调用失败或超时"
    if code != 0:
        return root, branch, {}, {"added": 0, "changed": 0, "deleted": 0}, "git diff 返回错误"

    states, summary = parse_diff(out)
    if not states and summary["deleted"] == 0:
        note = "无改动"
    else:
        note = "+%d ~%d -%d" % (
            summary["added"], summary["changed"], summary["deleted"])
    return root, branch, states, summary, note

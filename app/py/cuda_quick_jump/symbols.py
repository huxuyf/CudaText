# -*- coding: utf-8 -*-
"""文件内符号提取（纯逻辑层，不依赖 cudatext，可独立测试）。

按词法器选择模式，重点覆盖 Oracle PL/SQL（许老师的主场景）、Python、
Pascal、Markdown、JavaScript；主模式无结果时用通用模式兜底，
避免文件被识别成错误词法器时「一个符号都找不到」。
"""

import re

MAX_LINES = 200000        # 超过此行数拒绝全文扫描（推断值，可调）
MAX_SYMBOLS = 3000

_SQL_CREATE = re.compile(
    r"^\s*(?:CREATE\s+(?:OR\s+REPLACE\s+)?)"
    r"(PROCEDURE|FUNCTION|PACKAGE(?:\s+BODY)?|TRIGGER|VIEW|TYPE(?:\s+BODY)?)\s+"
    r"([A-Za-z_][A-Za-z0-9_$#]*)", re.I)
_SQL_DECL = re.compile(
    r"^\s*(PROCEDURE|FUNCTION)\s+([A-Za-z_][A-Za-z0-9_$#]*)", re.I)
_PY = re.compile(
    r"^\s*(?:async\s+)?(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", re.I)
_PAS = re.compile(
    r"^\s*(procedure|function|constructor|destructor)\s+"
    r"([A-Za-z_][A-Za-z0-9_.]*)", re.I)
_JS = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?"
    r"(function|class)\s+([A-Za-z_$][A-Za-z0-9_$]*)", re.I)
_JS_ARROW = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*="
    r"\s*(?:\([^)]*\)|[A-Za-z_$][A-Za-z0-9_$]*)\s*=>")
_MD = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

# (正则, 是否「kind 在第 1 组、name 在第 2 组」, 固定 kind)
PATTERN_SETS = {
    "sql": [(_SQL_CREATE, True, None), (_SQL_DECL, True, None)],
    "python": [(_PY, True, None)],
    "pascal": [(_PAS, True, None)],
    "javascript": [(_JS, True, None), (_JS_ARROW, False, "arrow")],
    "markdown": [(_MD, False, "heading")],
    "generic": [(_SQL_CREATE, True, None), (_PY, True, None),
                (_PAS, True, None), (_JS, True, None),
                (_JS_ARROW, False, "arrow")],
}

_COMMENT_PREFIX = {
    "sql": ("--", "/*", "*", "//"),
    "python": ("#", '"""', "'''"),
    "pascal": ("//", "{", "(*"),
    "javascript": ("//", "/*", "*"),
    "markdown": (),
    "generic": ("--", "//", "/*", "*", ";"),
}


def detect_family(lexer):
    """把 CudaText 词法器名映射到模式族。"""
    name = (lexer or "").lower()
    if "sql" in name or "oracle" in name or "pl/" in name:
        return "sql"
    if "python" in name:
        return "python"
    if "pascal" in name or "delphi" in name or "object" in name:
        return "pascal"
    if "markdown" in name:
        return "markdown"
    if "javascript" in name or "typescript" in name or name in ("js", "ts"):
        return "javascript"
    return "generic"


def _scan(lines, family):
    patterns = PATTERN_SETS[family]
    comments = _COMMENT_PREFIX[family]
    found = []
    for index, raw in enumerate(lines):
        stripped = raw.lstrip()
        if comments and stripped.startswith(comments):
            continue
        for regex, kind_in_group1, fixed_kind in patterns:
            m = regex.match(raw)
            if not m:
                continue
            if family == "markdown":
                level = len(m.group(1))
                kind = "H%d" % level
                label = m.group(2).strip()
            elif kind_in_group1:
                kind = m.group(1).upper()
                label = m.group(2)
            else:
                kind = fixed_kind or "symbol"
                label = m.group(1)
            found.append({
                "line": index,          # 0-based，与 set_caret 对齐
                "name": label,
                "kind": kind,
            })
            break
        if len(found) >= MAX_SYMBOLS:
            break
    return found


def extract_symbols(lines, lexer=""):
    """返回符号列表 [{'line':0-based, 'name':str, 'kind':str}]。

    主模式无结果且族不是 generic 时，用通用模式重扫一次。
    """
    family = detect_family(lexer)
    result = _scan(lines, family)
    if not result and family != "generic":
        result = _scan(lines, "generic")
    return result


def parse_target(text):
    """解析统一跳转输入，返回 ('line', int) / ('symbol', str) / ('invalid', str)。

    约定：
      :123      -> 跳到第 123 行（1-based 输入，转成 0-based）
      123       -> 同上
      @name     -> 过滤名为 name 的符号（空则列全部）
      name      -> 按符号名过滤
    """
    value = (text or "").strip()
    if not value:
        return "invalid", "输入为空"
    if value.startswith(":"):
        value = value[1:].strip()
        if not value.isdigit():
            return "invalid", "「:」后必须是行号"
        return "line", int(value)
    if value.isdigit():
        return "line", int(value)
    if value.startswith("@"):
        return "symbol", value[1:].strip()
    return "symbol", value


def filter_symbols(symbols, query):
    """大小写不敏感的包含过滤；空查询返回全部。"""
    if not query:
        return symbols
    needle = query.lower()
    return [s for s in symbols if needle in s["name"].lower()]

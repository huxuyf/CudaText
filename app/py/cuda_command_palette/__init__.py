# -*- coding: utf-8 -*-
"""统一命令面板：> 命令 / @ 文件内符号 / : 行号 / 无前缀 项目文件。

CudaText 的内建命令面板由核心实现，插件无法改写其行为。本插件改用
PROC_GET_COMMANDS 取到同一份命令清单，借助 dlg_menu 的实时过滤，把前缀
字符写进菜单标签：输入 ">" 时列表自然只剩命令项，输入 "@" 只剩符号项，
输入 ":" 只剩行号项，从而实现一步式前缀路由，且完全不触碰核心。

额外能力：最近使用（MRU）置顶、项目内文件搜索、文件列表缓存。

兼容 Python 3.8。
"""

import os
import time

import cudatext as app
from . import palette_logic as L
from . import symbols as S

MRU_FILE = "cuda_command_palette.json"
CACHE_TTL = 300.0          # 项目文件列表缓存 5 分钟


def _log(msg):
    print("[cuda_command_palette] " + str(msg))


class Command:
    _file_cache = {"root": "", "files": [], "ts": 0.0}

    # ---------- 基础读取 ----------

    def _mru_path(self):
        try:
            return os.path.join(app.app_path(app.APP_DIR_SETTINGS), MRU_FILE)
        except Exception:
            return ""

    def _mru(self):
        p = self._mru_path()
        return L.load_mru(p) if p else {"items": {}}

    def _filename(self):
        try:
            return app.ed.get_prop(app.PROP_FN, "") or ""
        except Exception:
            return ""

    def _lexer(self):
        try:
            return app.ed.get_prop(app.PROP_LEXER_CARET, "") or ""
        except Exception:
            return ""

    def _line_count(self):
        try:
            return app.ed.get_line_count()
        except Exception:
            return 0

    def _commands(self):
        try:
            return app.app_proc(app.PROC_GET_COMMANDS, "") or []
        except Exception as exc:
            _log("读取命令清单失败：%s" % exc)
            return []

    def _project_files(self, force=False):
        fn = self._filename()
        root = L.find_project_root(os.path.dirname(fn)) if fn else ""
        cache = self._file_cache
        if (not force and root and root == cache["root"]
                and cache["files"] and time.time() - cache["ts"] < CACHE_TTL):
            return root, cache["files"]
        files = L.scan_files(root)
        self._file_cache = {"root": root, "files": files, "ts": time.time()}
        return root, files

    # ---------- 构造面板 ----------

    def _build_items(self, force=False):
        mru = self._mru()
        count = self._line_count()
        items = L.normalize_commands(self._commands(), mru)

        lines = None
        try:
            if 0 < count <= S.MAX_LINES:
                lines = app.ed.get_text_all().splitlines()
        except Exception as exc:
            _log("读取文档失败：%s" % exc)
        if lines:
            L.add_symbols(items, S.extract_symbols(lines, self._lexer()), mru)

        root, files = self._project_files(force)
        L.add_files(items, files, root, mru)
        L.add_line_item(items, count)
        return L.sort_items(items), mru

    # ---------- 执行 ----------

    def _jump(self, line0, count):
        if line0 < 0 or (count and line0 >= count):
            app.msg_status("命令面板：行号超出范围（1–%d）" % count)
            return
        try:
            app.ed.set_caret(0, line0)
            app.ed.set_prop(app.PROP_LINE_TOP, max(0, line0 - 3))
            app.msg_status("命令面板：第 %d 行" % (line0 + 1))
        except Exception as exc:
            _log("跳转失败：%s" % exc)
            app.msg_status("命令面板：跳转失败，详见 Console")

    def _run(self, item, mru):
        kind = item.get("kind")
        if kind == L.KIND_LINE:
            count = self._line_count()
            text = app.dlg_input("跳转到行号（1–%d）" % count, "")
            if text is None:
                return
            n = L.parse_line_number(text)
            if n is None:
                app.msg_status("命令面板：行号无效")
                return
            self._jump(n - 1, count)
        elif kind == L.KIND_SYM:
            self._jump(int(item.get("line", 0)), self._line_count())
        elif kind == L.KIND_FILE:
            try:
                if item.get("via_code"):
                    app.ed.cmd(item["code"])
                else:
                    app.file_open(item["path"])
            except Exception as exc:
                _log("打开文件失败：%s" % exc)
                app.msg_status("命令面板：打开失败，详见 Console")
        elif kind == L.KIND_CMD:
            try:
                app.ed.cmd(item["code"])
            except Exception as exc:
                _log("执行命令失败：%s" % exc)
                app.msg_status("命令面板：执行失败，详见 Console")
        path = self._mru_path()
        if path:
            L.save_mru(path, L.bump_mru(mru, L.entry_key(item)))

    # ---------- 菜单命令 ----------

    def show(self):
        items, mru = self._build_items()
        lines = L.menu_lines(items)
        caption = ("命令面板：> 命令 | @ 符号 | : 行号 | 无前缀 文件"
                   "（共 %d 项）" % len(lines))
        idx = app.dlg_menu(app.DMENU_LIST | app.DMENU_NO_FULLFILTER,
                           lines, caption=caption, clip=app.CLIP_RIGHT,
                           w=760, h=420)
        if idx is None or idx < 0 or idx >= len(items):
            return
        self._run(items[idx], mru)

    def show_commands(self):
        mru = self._mru()
        items = L.sort_items(
            L.normalize_commands(self._commands(), mru))
        idx = app.dlg_menu(app.DMENU_LIST | app.DMENU_NO_FULLFILTER,
                           L.menu_lines(items), caption="命令面板 · 命令",
                           clip=app.CLIP_RIGHT, w=760, h=420)
        if idx is None or idx < 0 or idx >= len(items):
            return
        self._run(items[idx], mru)

    def show_files(self):
        mru = self._mru()
        root, files = self._project_files()
        items = L.sort_items(L.add_files([], files, root, mru))
        idx = app.dlg_menu(app.DMENU_LIST | app.DMENU_NO_FULLFILTER,
                           L.menu_lines(items),
                           caption="命令面板 · 项目文件（%d 个）" % len(items),
                           clip=app.CLIP_RIGHT, w=760, h=420)
        if idx is None or idx < 0 or idx >= len(items):
            return
        self._run(items[idx], mru)

    def refresh_files(self):
        root, files = self._project_files(force=True)
        app.msg_status("命令面板：已刷新项目文件（%d 个，根目录 %s）" %
                       (len(files), root or "无"))

    def clear_mru(self):
        p = self._mru_path()
        if p and L.save_mru(p, {"items": {}}):
            app.msg_status("命令面板：最近使用记录已清空")
        else:
            app.msg_status("命令面板：清空失败，详见 Console")

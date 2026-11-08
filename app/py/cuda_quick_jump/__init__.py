# -*- coding: utf-8 -*-
"""快速跳转面板：@符号 / :行号 / 关键词，统一在一个输入框里分发。

对标 VS Code 命令面板的前缀路由与 Sublime 的 Goto Anything。
CudaText 的命令面板是核心实现、插件无法改写其行为，因此这里用「独立面板」
补齐这一层，而不是去改核心。

兼容 Python 3.8。
"""

import cudatext as app
from . import symbols


def _log(msg):
    print("[cuda_quick_jump] " + msg)


class Command:
    # ---------- 内部工具 ----------

    @staticmethod
    def _lines():
        """返回 (行文本列表, 行数)；文件过大时返回 (None, 行数)。"""
        try:
            count = app.ed.get_line_count()
            if count > symbols.MAX_LINES:
                return None, count
            return app.ed.get_text_all().splitlines(), count
        except Exception as exc:
            _log("读取文档失败：%s" % exc)
            return None, 0

    @staticmethod
    def _lexer():
        try:
            return app.ed.get_prop(app.PROP_LEXER_CARET, "")
        except Exception as exc:
            _log("读取词法器失败：%s" % exc)
            return ""

    @staticmethod
    def _jump(line0, count):
        if count <= 0:
            app.msg_status("跳转：当前文档不可用")
            return
        if line0 < 0 or line0 >= count:
            app.msg_status("跳转：行号超出范围（1–%d）" % count)
            return
        try:
            app.ed.set_caret(0, line0)
            app.ed.set_prop(app.PROP_LINE_TOP, max(0, line0 - 3))
        except Exception as exc:
            _log("跳转失败：%s" % exc)
            app.msg_status("跳转：设置光标失败，详见 Console")
            return
        app.msg_status("跳转：第 %d 行" % (line0 + 1))

    def _pick_symbol(self, query):
        lines, count = self._lines()
        if lines is None:
            app.msg_status("跳转：文档超过 %d 行，请用「跳转到行」" %
                           symbols.MAX_LINES)
            return
        found = symbols.extract_symbols(lines, self._lexer())
        matched = symbols.filter_symbols(found, query)
        if not matched:
            app.msg_status("跳转：未找到符号%s（共扫描 %d 个）" % (
                "「%s」" % query if query else "", len(found)))
            return
        items = ["%s\tL%d · %s" % (s["name"], s["line"] + 1, s["kind"])
                 for s in matched]
        idx = app.dlg_menu(app.DMENU_LIST | app.DMENU_NO_FULLFILTER,
                           items, caption="文件内符号（可继续输入过滤）",
                           clip=app.CLIP_MIDDLE)
        if idx is None:
            return
        self._jump(matched[idx]["line"], count)

    # ---------- 命令 ----------

    def goto(self):
        _lines, count = self._lines()
        hint = ("输入 @符号名 / :行号 / 关键词\n"
                "例：@init、:128、proc_xxx（当前共 %d 行）" % count)
        text = app.dlg_input(hint, "")
        if text is None:
            return
        kind, value = symbols.parse_target(text)
        if kind == "invalid":
            app.msg_status("跳转：%s" % value)
            return
        if kind == "line":
            self._jump(value - 1, count)
        else:
            self._pick_symbol(value)

    def goto_symbol(self):
        self._pick_symbol("")

    def goto_line(self):
        _lines, count = self._lines()
        text = app.dlg_input("跳转到行号（1–%d）" % count, "")
        if text is None:
            return
        kind, value = symbols.parse_target(":" + text.strip())
        if kind == "invalid":
            app.msg_status("跳转：%s" % value)
            return
        self._jump(value - 1, count)

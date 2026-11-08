# -*- coding: utf-8 -*-
"""宏录制管理：把 CudaText 核心内建的录制结果命名保存、列出、回放、删除。

核心已有 cmd_MacroStart(2810) 与 on_macro 事件，本插件不重复实现录制，
只补齐「保存 / 管理 / 复用」这一层（对标 Sublime 的宏管理器）。

兼容 Python 3.8。
"""

import os

import cudatext as app
import cudatext_cmd as cmd
from . import macro_store


def _log(msg):
    print("[cuda_macro_manager] " + msg)


def _macro_label(m):
    steps = len([x for x in m.get("text", "").split("\n") if x.strip()])
    return "%s\t%d 步 · %s" % (m["name"], steps, m.get("created", ""))


class Command:
    def __init__(self):
        self._last_text = ""      # 最近一次录制（未命名）
        self._last_steps = 0

    @staticmethod
    def _path():
        return os.path.join(
            app.app_path(app.APP_DIR_SETTINGS), macro_store.STORE_FILE)

    def _load(self):
        try:
            return macro_store.load(self._path())
        except ValueError as exc:
            _log(str(exc))
            app.msg_status("宏：%s，本次按空库处理" % exc)
            return macro_store.default_data()

    def _save(self, data):
        try:
            macro_store.save(self._path(), data)
            return True
        except (OSError, ValueError) as exc:
            _log("保存宏库失败：%s" % exc)
            app.msg_status("宏：保存失败，详见 Console")
            return False

    # ---------- 录制 ----------

    def start_stop(self):
        app.ed.cmd(cmd.cmd_MacroStart)
        app.msg_status("宏：已切换录制状态（再次执行即停止并交给管理器）")

    def on_macro(self, ed_self, text):
        """核心停止录制时回调。只存内存 + 轻提示，不弹窗打断工作流。"""
        self._last_text = text or ""
        self._last_steps = len([x for x in self._last_text.split("\n") if x.strip()])
        if self._last_steps:
            app.msg_status("宏：已录制 %d 步，用「宏\保存最近录制」命名保存" %
                           self._last_steps)
        else:
            app.msg_status("宏：本次录制为空，未保存")

    # ---------- 保存 / 回放 ----------

    def save_last(self):
        if not self._last_steps:
            app.msg_status("宏：没有可保存的录制，请先录制")
            return
        name = app.dlg_input("为最近一次录制命名（同名将覆盖）", "宏 1")
        if not name or not name.strip():
            return
        data = self._load()
        try:
            data, is_new = macro_store.add_macro(data, name, self._last_text)
        except ValueError as exc:
            app.msg_status("宏：%s" % exc)
            return
        if self._save(data):
            app.msg_status("宏：已%s「%s」（%d 步）" % (
                "保存" if is_new else "覆盖", name.strip(), self._last_steps))

    def play_last(self):
        if not self._last_steps:
            app.msg_status("宏：没有可回放的录制，请从列表选择或先录制")
            return
        self._play(self._last_text)

    def list(self):
        data = self._load()
        macros = data["macros"]
        items = [_macro_label(m) for m in macros]
        if self._last_steps:
            items.append("（最近录制 · 未保存）\t%d 步" % self._last_steps)
        if not items:
            app.msg_status("宏：库中暂无宏，请先录制并保存")
            return
        idx = app.dlg_menu(app.DMENU_LIST, items,
                           caption="选择宏回放", clip=app.CLIP_RIGHT)
        if idx is None:
            return
        if idx < len(macros):
            self._play(macros[idx]["text"])
        else:
            self._play(self._last_text)

    def _play(self, text):
        actions = macro_store.parse_actions(text)
        if not actions:
            app.msg_status("宏：没有可回放的动作")
            return
        skipped = 0
        for act in actions:
            try:
                if act["type"] == "cmd":
                    app.ed.cmd(act["code"], act["text"])
                elif act["type"] == "plug":
                    app.app_proc(app.PROC_EXEC_PLUGIN, act["spec"])
                else:
                    skipped += 1
                    _log("跳过无法解析的宏项：%s" % act["raw"])
            except Exception as exc:
                skipped += 1
                _log("回放动作失败 %r：%s" % (act, exc))
        total = len(actions)
        if skipped:
            app.msg_status("宏：回放 %d 步，其中 %d 步失败/跳过（详见 Console）" %
                           (total, skipped))
        else:
            app.msg_status("宏：已回放 %d 步" % total)

    # ---------- 管理 ----------

    def delete(self):
        data = self._load()
        macros = data["macros"]
        if not macros:
            app.msg_status("宏：库中暂无宏")
            return
        idx = app.dlg_menu(app.DMENU_LIST,
                           [_macro_label(m) for m in macros],
                           caption="选择要删除的宏")
        if idx is None:
            return
        name = macros[idx]["name"]
        answer = app.msg_box("确认删除宏「%s」？" % name,
                             app.MB_OKCANCEL + app.MB_ICONQUESTION)
        if answer != app.ID_OK:
            return
        del macros[idx]
        if self._save(data):
            app.msg_status("宏：已删除「%s」" % name)

    def show_path(self):
        app.msg_status("宏库：%s" % self._path())

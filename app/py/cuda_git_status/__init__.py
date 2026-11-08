# -*- coding: utf-8 -*-
"""Git 状态插件：状态栏分支显示 + 装订线差异标记。

用 CudaText 原生 LINESTATE_* 实现装订线色块，直接复用主题里的
EdStateChanged / EdStateAdded Token，无需额外图片资源。

设计约束：
- 只清除「本插件设置过」的行状态，不碰核心维护的已修改/已保存状态。
- 打开文件与保存后自动刷新；切换标签只更新状态栏文本（用缓存，不起 git 进程）。
- 所有 git 调用带超时，失败时不弹窗、不中断编辑。

兼容 Python 3.8（CudaText 内嵌版本）。
"""

import cudatext as app
from . import git_logic

CELL_TAG = 21001          # 避开核心状态栏 cell 的 tag 范围 1..20
MAX_MARKS = 5000          # 单次最多标记行数，防止超大 diff 卡 UI


def _log(msg):
    print("[cuda_git_status] " + msg)


class Command:
    def __init__(self):
        self.auto = True
        self._marked = {}   # filename -> set(本插件设置过的 0-based 行号)
        self._info = {}     # filename -> (branch, note)

    # ---------- 内部工具 ----------

    @staticmethod
    def _file_of(ed_self):
        try:
            return ed_self.get_prop(app.PROP_FN, "")
        except Exception as exc:
            _log("读取文件名失败：%s" % exc)
            return ""

    @staticmethod
    def _line_count(ed_self):
        try:
            return ed_self.get_line_count()
        except Exception as exc:
            _log("读取行数失败：%s" % exc)
            return 0

    def _set_cell(self, text):
        """幂等地创建/更新状态栏 cell。核心重建状态栏后会自动补回。"""
        try:
            handle = app.app_proc(app.PROC_GET_MAIN_STATUSBAR, "")
            if not handle:
                return
            idx = app.statusbar_proc(
                handle, app.STATUSBAR_FIND_CELL, value=CELL_TAG)
            if idx is None:
                idx = app.statusbar_proc(
                    handle, app.STATUSBAR_ADD_CELL, index=-1, tag=CELL_TAG)
                if idx is None:
                    _log("状态栏 cell 创建失败")
                    return
                app.statusbar_proc(handle, app.STATUSBAR_SET_CELL_AUTOSIZE,
                                   index=idx, value=True)
                app.statusbar_proc(handle, app.STATUSBAR_SET_CELL_ALIGN,
                                   index=idx, value="C")
                app.statusbar_proc(handle, app.STATUSBAR_SET_CELL_HINT,
                                   index=idx, value="Git 分支与差异（cuda_git_status）")
            app.statusbar_proc(handle, app.STATUSBAR_SET_CELL_TEXT,
                               index=idx, value=text)
        except Exception as exc:
            _log("更新状态栏失败：%s" % exc)

    def _clear_marks(self, ed_self, filename):
        """只把本插件写过的行恢复为 NORMAL，不影响核心的状态标记。"""
        lines = self._marked.pop(filename, set())
        for line in lines:
            try:
                ed_self.set_prop(app.PROP_LINE_STATE,
                                 (line, app.LINESTATE_NORMAL))
            except Exception as exc:
                _log("清除第 %d 行状态失败：%s" % (line + 1, exc))

    @staticmethod
    def _apply_marks(ed_self, states, line_count):
        written = set()
        for line, kind in states.items():
            if line >= line_count or len(written) >= MAX_MARKS:
                continue
            value = (app.LINESTATE_ADDED if kind == "added"
                     else app.LINESTATE_CHANGED)
            try:
                ed_self.set_prop(app.PROP_LINE_STATE, (line, value))
                written.add(line)
            except Exception as exc:
                _log("写入第 %d 行状态失败：%s" % (line + 1, exc))
        try:
            ed_self.action(app.EDACTION_UPDATE)
        except Exception as exc:
            _log("刷新编辑器绘制失败：%s" % exc)
        return written

    # ---------- 命令 ----------

    def refresh(self, ed_self=None, show_msg=False):
        ed_self = ed_self or app.ed
        filename = self._file_of(ed_self)
        if not filename:
            if show_msg:
                app.msg_status("Git：当前文件尚未保存到磁盘")
            return

        root, branch, states, summary, note = git_logic.get_diff_states(filename)
        self._info[filename] = (branch, note)

        self._clear_marks(ed_self, filename)
        line_count = self._line_count(ed_self)
        if states and line_count and line_count <= git_logic.MAX_LINES:
            self._marked[filename] = self._apply_marks(
                ed_self, states, line_count)

        # 非仓库文件不占用状态栏空间，避免出现满屏「非 Git 仓库」
        if note == "非 Git 仓库":
            self._set_cell("Git: —")
        elif branch:
            self._set_cell("Git: %s | %s" % (branch, note))
        else:
            self._set_cell("Git: %s" % note)
        if show_msg:
            app.msg_status("Git：%s，%s（+%d 新增 / ~%d 修改 / -%d 删除）" % (
                branch or "无分支信息", note,
                summary["added"], summary["changed"], summary["deleted"]))

    def clear(self):
        filename = self._file_of(app.ed)
        if not filename:
            return
        self._clear_marks(app.ed, filename)
        self._set_cell("Git: 标记已清除")
        app.msg_status("Git：已清除本插件设置的装订线标记")

    def toggle_auto(self):
        self.auto = not self.auto
        app.msg_status("Git：自动刷新已%s" % ("开启" if self.auto else "关闭"))

    def show_info(self):
        filename = self._file_of(app.ed)
        if not filename:
            app.msg_status("Git：当前文件尚未保存到磁盘")
            return
        branch, note = self._info.get(filename, (None, "未刷新"))
        root = git_logic.find_repo_root(filename)
        app.msg_box(
            "文件：%s\n仓库：%s\n分支：%s\n差异：%s\n自动刷新：%s" % (
                filename, root or "（非 Git 仓库）", branch or "（未知）",
                note, "开启" if self.auto else "关闭"),
            app.MB_OK + app.MB_ICONINFO)

    def remove_cell(self):
        try:
            handle = app.app_proc(app.PROC_GET_MAIN_STATUSBAR, "")
            if handle:
                app.statusbar_proc(handle, app.STATUSBAR_DELETE_CELL,
                                   tag=CELL_TAG)
        except Exception as exc:
            _log("移除状态栏 cell 失败：%s" % exc)

    # ---------- 事件 ----------

    def on_open(self, ed_self):
        if self.auto:
            self.refresh(ed_self)

    def on_save(self, ed_self):
        if self.auto:
            self.refresh(ed_self)

    def on_focus(self, ed_self):
        """切换标签只更新文本，不重新跑 git（避免每次聚焦都起进程）。"""
        filename = self._file_of(ed_self)
        if not filename:
            self._set_cell("Git: —")
            return
        branch, note = self._info.get(filename, (None, "未刷新"))
        self._set_cell("Git: %s | %s" % (branch, note) if branch
                       else "Git: %s" % note)

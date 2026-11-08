import json
import os

from cudatext import *
import cudax_lib as apx
from cudax_lib import get_translation

from .stack_logic import push_closed, remove_path

_ = get_translation(__file__)

CONFIG_JSON = 'cuda_reopen_tab.json'
DEFAULT_MAX_STACK = 20


def _cfg_get(key, default):
    try:
        return apx.get_opt(
            key,
            default,
            lev=apx.CONFIG_LEV_USER_ONLY,
            user_json=CONFIG_JSON,
        )
    except Exception:
        return default


def _cfg_set(key, value):
    try:
        return apx.set_opt(
            key,
            value,
            lev=apx.CONFIG_LEV_USER,
            user_json=CONFIG_JSON,
        )
    except Exception:
        return None


class Command:

    def __init__(self):
        self.exiting = False
        self.pending = {}
        try:
            self.max_stack = int(_cfg_get('max_stack', DEFAULT_MAX_STACK))
        except Exception:
            self.max_stack = DEFAULT_MAX_STACK
        if self.max_stack < 1:
            self.max_stack = DEFAULT_MAX_STACK
        self.stack = self._load_stack()

    def _load_stack(self):
        raw = _cfg_get('closed_stack', '[]')
        try:
            data = json.loads(raw)
        except Exception:
            data = []
        if not isinstance(data, list):
            data = []
        result = [item for item in data if isinstance(item, str) and item]
        if self.max_stack > 0:
            result = result[-self.max_stack:]
        return result

    def _save_stack(self):
        try:
            raw = json.dumps(self.stack, ensure_ascii=False)
        except Exception:
            return
        _cfg_set('closed_stack', raw)

    def _push(self, path):
        self.stack = push_closed(self.stack, path, self.max_stack)
        self._save_stack()

    def _remove(self, path):
        if remove_path(self.stack, path):
            self._save_stack()

    def on_close_pre(self, ed_self):
        if self.exiting:
            return True
        try:
            handle = int(ed_self.get_prop(PROP_HANDLE_SELF))
            path = ed_self.get_prop(PROP_FN)
            if path:
                self.pending[handle] = path
        except Exception:
            pass
        return True

    def on_close(self, ed_self):
        if self.exiting:
            return
        try:
            handle = int(ed_self.get_prop(PROP_HANDLE_SELF))
        except Exception:
            return
        path = self.pending.pop(handle, None)
        if not path:
            try:
                path = ed_self.get_prop(PROP_FN)
            except Exception:
                path = ''
        if path:
            self._push(path)

    def on_exit_pre(self, ed_self):
        self.exiting = True
        self.pending.clear()
        return True

    def _reopen(self, path):
        if not path:
            return False
        if not os.path.isfile(path):
            self._remove(path)
            msg_box(
                _('文件已不存在：\n') + path,
                MB_OK + MB_ICONERROR,
            )
            return False

        try:
            opened = file_open(path)
        except Exception:
            opened = False

        # The entry is consumed by a successful or failed attempt; a failed
        # attempt must not stay in the list forever.
        self._remove(path)

        if not opened:
            msg_box(
                _('无法打开文件：\n') + path,
                MB_OK + MB_ICONERROR,
            )
            return False

        msg_status(_('已重开：') + os.path.basename(path))
        return True

    def reopen_last(self):
        if not self.stack:
            msg_status(_('没有最近关闭的标签'))
            return
        self._reopen(self.stack[-1])

    def reopen_list(self):
        if not self.stack:
            msg_status(_('没有最近关闭的标签'))
            return
        items = []
        for path in reversed(self.stack):
            name = os.path.basename(path)
            items.append(name + '\t' + path)
        index = dlg_menu(
            DMENU_LIST,
            items,
            caption=_('最近关闭的标签'),
        )
        if index is None:
            return
        # Items are shown newest-first, while the stack is oldest-first.
        stack_index = -1 - int(index)
        try:
            path = self.stack[stack_index]
        except Exception:
            return
        self._reopen(path)

    def clear_list(self):
        self.stack = []
        self._save_stack()
        msg_status(_('已清空最近关闭标签列表'))

    def config(self):
        value = dlg_input(
            _('最近关闭标签的最大保留数量：'),
            str(self.max_stack),
        )
        if value is None:
            return
        try:
            count = int(value.strip())
        except Exception:
            msg_box(_('请输入整数。'), MB_OK + MB_ICONERROR)
            return
        if count < 1 or count > 100:
            msg_box(_('数值必须在 1 到 100 之间。'), MB_OK + MB_ICONERROR)
            return
        self.max_stack = count
        _cfg_set('max_stack', count)
        if len(self.stack) > count:
            del self.stack[:len(self.stack) - count]
            self._save_stack()
        msg_status(_('最近关闭标签上限：') + str(count))

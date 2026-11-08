import time

from cudatext import *
import cudax_lib as apx
from cudax_lib import get_translation

_ = get_translation(__file__)

CONFIG_JSON = 'cuda_reload_caret.json'
MAX_RECORDS = 200


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
        self.restore_scroll = bool(_cfg_get('restore_scroll', True))
        self.records = {}
        self.pending_restore = {}

    def _sample(self, ed_self, only_if_missing=False):
        try:
            fn = ed_self.get_prop(PROP_FN)
            if not fn:
                return
            handle = int(ed_self.get_prop(PROP_HANDLE_SELF))
            key = (handle, fn)
            if only_if_missing and key in self.records:
                return
            carets = ed_self.get_carets()
            if not carets:
                return
            x = int(carets[0][0])
            y = int(carets[0][1])
            try:
                top = int(ed_self.get_prop(PROP_LINE_TOP))
            except Exception:
                top = -1
            self.records[key] = {
                'fn': fn,
                'handle': handle,
                'x': x,
                'y': y,
                'top': top,
                'time': time.time(),
            }
            if len(self.records) > MAX_RECORDS:
                old = sorted(
                    self.records.items(),
                    key=lambda item: item[1].get('time', 0),
                )[:len(self.records) - MAX_RECORDS]
                for old_key, _value in old:
                    self.records.pop(old_key, None)
        except Exception:
            # Sampling must never break normal editing.
            pass

    def _find_record(self, handle, fn):
        key = (handle, fn)
        rec = self.records.get(key)
        if rec:
            return key, rec

        # The handle can change after some kinds of reopen; fall back to the
        # newest record with the same filename.
        best_key = None
        best_rec = None
        for key2, rec2 in self.records.items():
            if key2[1] != fn:
                continue
            if best_rec is None or rec2.get('time', 0) > best_rec.get('time', 0):
                best_key = key2
                best_rec = rec2
        if best_rec is not None:
            return best_key, best_rec
        return None, None

    def on_open(self, ed_self):
        self._sample(ed_self, only_if_missing=True)

    def on_caret_slow(self, ed_self):
        self._sample(ed_self)

    def on_scroll(self, ed_self):
        self._sample(ed_self)

    def on_open_reopen(self, ed_self):
        try:
            fn = ed_self.get_prop(PROP_FN)
            handle = int(ed_self.get_prop(PROP_HANDLE_SELF))
            key, rec = self._find_record(handle, fn)
            if rec is None:
                return

            # Consume the record so a second event cannot restore twice.
            self.records.pop(key, None)

            # Caret restore here is the first attempt.  The event order relative
            # to the core's caret reset is not guaranteed, so a second attempt
            # is scheduled below after the event returns.
            try:
                ed_self.set_caret(int(rec['x']), int(rec['y']))
            except Exception:
                pass

            self.pending_restore[handle] = {
                'x': int(rec['x']),
                'y': int(rec['y']),
                'top': int(rec.get('top', -1)),
                'scroll': self.restore_scroll,
            }
            try:
                timer_proc(TIMER_START_ONE, self._apply_restore, 50, str(handle))
            except Exception:
                pass
        except Exception:
            pass

    def _apply_restore(self, tag='', info=''):
        try:
            handle = int(tag)
        except Exception:
            return
        data = self.pending_restore.pop(handle, None)
        if data is None:
            return
        try:
            app_proc(PROC_IDLE, True)
        except Exception:
            pass
        try:
            ed_self = Editor(handle)
            ed_self.set_caret(int(data['x']), int(data['y']))
            if data.get('scroll') and int(data.get('top', -1)) >= 0:
                ed_self.set_prop(PROP_LINE_TOP, int(data['top']))
        except Exception:
            pass

    def toggle_scroll(self):
        self.restore_scroll = not self.restore_scroll
        _cfg_set('restore_scroll', self.restore_scroll)
        state = _('开启') if self.restore_scroll else _('关闭')
        msg_status(_('重载保持光标：恢复滚动位置 = ') + state)

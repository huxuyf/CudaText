import ctypes
from ctypes import wintypes

import cudatext as app
import cudatext_cmd as cmds

WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
GWLP_WNDPROC = -4

TABS_PREFIX = 'aPagesTabs'

_user32 = ctypes.WinDLL('user32')
_kernel32 = ctypes.WinDLL('kernel32')

_IS64 = ctypes.sizeof(ctypes.c_void_p) == 8
_SetWindowLongPtr = _user32.SetWindowLongPtrW if _IS64 else _user32.SetWindowLongW
if _IS64:
    _SetWindowLongPtr.restype = ctypes.c_void_p
    _SetWindowLongPtr.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
else:
    _SetWindowLongPtr.restype = ctypes.c_long
    _SetWindowLongPtr.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]

_LRESULT = ctypes.c_ssize_t
_WNDPROC = ctypes.WINFUNCTYPE(_LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
_ENUM_PROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

_user32.CallWindowProcW.restype = _LRESULT
_user32.CallWindowProcW.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
_user32.DefWindowProcW.restype = _LRESULT
_user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
_user32.SendMessageW.restype = _LRESULT
_user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
_user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.IsWindow.restype = wintypes.BOOL
_user32.IsWindow.argtypes = [wintypes.HWND]
_user32.IsWindowVisible.restype = wintypes.BOOL
_user32.IsWindowVisible.argtypes = [wintypes.HWND]
_user32.GetWindowThreadProcessId.restype = wintypes.DWORD
_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_user32.EnumChildWindows.restype = wintypes.BOOL
_user32.EnumChildWindows.argtypes = [wintypes.HWND, _ENUM_PROC, wintypes.LPARAM]
_user32.EnumWindows.restype = wintypes.BOOL
_user32.EnumWindows.argtypes = [_ENUM_PROC, wintypes.LPARAM]

_kernel32.GetCurrentProcessId.restype = wintypes.DWORD


class Command:
    def __init__(self):
        self._procs = {}
        self._cb = _WNDPROC(self._wndproc)
        self._cb_ptr = ctypes.cast(self._cb, ctypes.c_void_p).value
        self._pending_before = -1
        self._buf = ctypes.create_unicode_buffer(256)

    def on_start2(self, ed_self=None):
        app.timer_proc(app.TIMER_START_ONE, self._init, 500)

    def on_state(self, ed_self, state):
        if state == app.APPSTATE_GROUPS:
            app.timer_proc(app.TIMER_START_ONE, self._init, 200)

    def on_focus(self, ed_self=None):
        # The tabs control may be recreated without APPSTATE_GROUPS. Detect a
        # stale handle cheaply; do NOT run a periodic timer here.
        for hwnd in list(self._procs):
            if not _user32.IsWindow(hwnd):
                self._rescan()
                return

    def on_exit_pre(self, ed_self=None):
        for hwnd in list(self._procs):
            self._restore(hwnd)

    def rescan(self):
        self._init()

    def _init(self, tag='', info=''):
        self._rescan()

    def _find_tabs(self):
        pid = _kernel32.GetCurrentProcessId()
        buf = self._buf
        found = []

        def enum_child(hwnd, lparam):
            _user32.GetWindowTextW(hwnd, buf, 256)
            if buf.value.startswith(TABS_PREFIX):
                found.append(hwnd)
            return True

        child_cb = _ENUM_PROC(enum_child)

        def enum_top(hwnd, lparam):
            p = wintypes.DWORD()
            _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
            if p.value != pid or not _user32.IsWindowVisible(hwnd):
                return True
            _user32.EnumChildWindows(hwnd, child_cb, 0)
            return True

        _user32.EnumWindows(_ENUM_PROC(enum_top), 0)
        return found

    def _rescan(self):
        found = self._find_tabs()
        for hwnd in found:
            self._subclass(hwnd)
        for hwnd in list(self._procs):
            if not _user32.IsWindow(hwnd):
                self._procs.pop(hwnd, None)

    def _subclass(self, hwnd):
        if hwnd in self._procs:
            return
        if _IS64:
            old = _SetWindowLongPtr(hwnd, GWLP_WNDPROC, ctypes.c_void_p(self._cb_ptr))
        else:
            old = _SetWindowLongPtr(hwnd, GWLP_WNDPROC, ctypes.c_long(self._cb_ptr))
        if old:
            self._procs[hwnd] = old

    def _restore(self, hwnd):
        old = self._procs.pop(hwnd, None)
        if old is None:
            return
        if _IS64:
            _SetWindowLongPtr(hwnd, GWLP_WNDPROC, ctypes.c_void_p(old))
        else:
            _SetWindowLongPtr(hwnd, GWLP_WNDPROC, ctypes.c_long(old))

    def _call_old(self, hwnd, msg, wparam, lparam):
        old = self._procs.get(hwnd)
        if old is None:
            return _user32.DefWindowProcW(hwnd, msg, wparam, lparam)
        return _user32.CallWindowProcW(old, hwnd, msg, wparam, lparam)

    def _wndproc(self, hwnd, msg, wparam, lparam):
        try:
            if msg == WM_MBUTTONDOWN:
                self._on_middle(hwnd, lparam)
                return 0
            if msg == WM_MBUTTONUP:
                return 0
        except Exception:
            pass
        return self._call_old(hwnd, msg, wparam, lparam)

    def _on_middle(self, hwnd, lparam):
        try:
            self._pending_before = len(app.ed_handles())
        except Exception:
            self._pending_before = -1
        _user32.SendMessageW(hwnd, WM_LBUTTONDOWN, 1, lparam)
        _user32.SendMessageW(hwnd, WM_LBUTTONUP, 0, lparam)
        app.timer_proc(app.TIMER_START_ONE, self._close_current, 20)

    def _close_current(self, tag='', info=''):
        try:
            after = len(app.ed_handles())
        except Exception:
            after = -1
        before = self._pending_before
        self._pending_before = -1
        if before >= 0 and after != before:
            return
        try:
            app.ed.cmd(cmds.cmd_FileClose)
        except Exception:
            pass

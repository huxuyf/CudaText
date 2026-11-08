from .tabs_list import Command as TabsListCommand
from .reopen_tab import Command as ReopenCommand
from .middle_close import Command as MiddleCloseCommand


class Command:
    def __init__(self):
        self._tabs = TabsListCommand()
        self._reopen = ReopenCommand()
        self._middle = MiddleCloseCommand()

    # ---- tabs_list: commands ----

    def open(self):
        return self._tabs.open()

    def open_filter(self):
        return self._tabs.open_filter()

    def list_config(self):
        return self._tabs.config()

    # ---- tabs_list: dialog and menu callbacks ----

    def filter_change(self, *args, **kwargs):
        return self._tabs.filter_change(*args, **kwargs)

    def list_on_sel(self, *args, **kwargs):
        return self._tabs.list_on_sel(*args, **kwargs)

    def list_on_menu(self, *args, **kwargs):
        return self._tabs.list_on_menu(*args, **kwargs)

    def list_on_click(self, *args, **kwargs):
        return self._tabs.list_on_click(*args, **kwargs)

    def list_on_click_x(self, *args, **kwargs):
        return self._tabs.list_on_click_x(*args, **kwargs)

    def list_mouse_down(self, *args, **kwargs):
        return self._tabs.list_mouse_down(*args, **kwargs)

    def list_mouse_up(self, *args, **kwargs):
        return self._tabs.list_mouse_up(*args, **kwargs)

    def list_mouse_move(self, *args, **kwargs):
        return self._tabs.list_mouse_move(*args, **kwargs)

    def auto_scroll_callback(self, *args, **kwargs):
        return self._tabs.auto_scroll_callback(*args, **kwargs)

    def menu_close_sel(self, *args, **kwargs):
        return self._tabs.menu_close_sel(*args, **kwargs)

    def menu_close_others(self, *args, **kwargs):
        return self._tabs.menu_close_others(*args, **kwargs)

    def menu_copy_file_name(self, *args, **kwargs):
        return self._tabs.menu_copy_file_name(*args, **kwargs)

    def menu_copy_file_path(self, *args, **kwargs):
        return self._tabs.menu_copy_file_path(*args, **kwargs)

    # ---- tabs_list: events ----

    def on_focus(self, ed_self):
        self._middle.on_focus(ed_self)
        return self._tabs.on_focus(ed_self)

    def on_open(self, ed_self):
        return self._tabs.on_open(ed_self)

    def on_tab_move(self, ed_self):
        return self._tabs.on_tab_move(ed_self)

    def on_state_ed(self, ed_self, state):
        return self._tabs.on_state_ed(ed_self, state)

    # ---- reopen_tab: commands ----

    def reopen_last(self):
        return self._reopen.reopen_last()

    def reopen_list(self):
        return self._reopen.reopen_list()

    def clear_list(self):
        return self._reopen.clear_list()

    def reopen_config(self):
        return self._reopen.config()

    # ---- reopen_tab: events ----

    def on_close_pre(self, ed_self):
        return self._reopen.on_close_pre(ed_self)

    def on_close(self, ed_self):
        return self._reopen.on_close(ed_self)

    # ---- middle_close: commands ----

    def rescan(self):
        return self._middle.rescan()

    # ---- middle_close: events ----

    def on_start2(self, ed_self=None):
        return self._middle.on_start2(ed_self)

    def on_state(self, ed_self, state):
        return self._middle.on_state(ed_self, state)

    # ---- command line dispatch ----

    def on_cli(self, param1='', param2=''):
        if param1 == 'tabs':
            return self.open()
        if param1 == 'tabs_filter':
            return self.open_filter()
        if param1 == 'reopen_last':
            return self.reopen_last()
        if param1 == 'reopen_list':
            return self.reopen_list()
        if param1 == 'clear_list':
            return self.clear_list()

    # ---- shared exit ----

    def on_exit_pre(self, ed_self=None):
        self._reopen.on_exit_pre(ed_self)
        self._middle.on_exit_pre(ed_self)
        return True

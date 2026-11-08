import os
import traceback

from cudatext import *
from .expand_core import parse_rules, find_replacement, read_text_file

SECTION = 'cuda_text_expand'
INI_FILE = os.path.join(app_path(APP_DIR_SETTINGS), 'plugins.ini')
FILTER = '文本文件|*.txt|所有文件|*.*'

DEFAULT_CONFIG_TEXT = """\
# 文本展开规则
# 每行一条，格式：触发词=替换文本（以第一个等号分割）
# 空行和以 # 开头的行会被忽略
#
# 输入触发词后按空格即可展开，例如输入 sa 再按空格：
sa=select * from
w=where
ord=order by
"""


class Command:

    def __init__(self):
        self._rules = {}
        self._stamp = None

    # ---------- 配置路径 ----------

    def _plugin_dir(self):
        return os.path.dirname(os.path.abspath(__file__))

    def config_path(self):
        path = ini_read(INI_FILE, SECTION, 'config_file', '')
        if not path:
            return os.path.join(self._plugin_dir(), 'config.txt')
        if not os.path.isabs(path):
            path = os.path.join(self._plugin_dir(), path)
        return os.path.abspath(path)

    # ---------- 规则加载 ----------

    def _load_rules(self):
        path = self.config_path()
        try:
            st = os.stat(path)
        except OSError:
            self._rules = {}
            self._stamp = None
            return self._rules

        stamp = (path, st.st_mtime_ns, st.st_size)
        if stamp != self._stamp:
            try:
                self._rules = parse_rules(read_text_file(path))
                self._stamp = stamp
            except OSError:
                self._rules = {}
                self._stamp = None
        return self._rules

    # ---------- 键盘事件 ----------

    def on_key(self, ed_self, key, state):
        if key != 32 or state:
            return True

        try:
            carets = ed_self.get_carets()
            if len(carets) != 1:
                return True

            x, y, x1, y1 = carets[0]
            if y < 0 or x1 >= 0:
                return True

            rules = self._load_rules()
            if not rules:
                return True

            line = ed_self.get_text_line(y)
            hit = find_replacement(line, x, rules)
            if not hit:
                return True

            start, token, value = hit
            suffix = '' if value.endswith((' ', '\t')) else ' '
            new_text = value + suffix
            x2 = min(x, len(line))

            if not ed_self.replace(start, y, x2, y, new_text):
                return True

            ed_self.set_caret(start + len(new_text), y)
            return False
        except Exception:
            app_log(LOG_CONSOLE_ADD, 'cuda_text_expand 错误:\n' + traceback.format_exc())
            return True

    # ---------- 菜单命令 ----------

    def dlg_config(self):
        cur = self.config_path()
        path = dlg_file(True, cur, os.path.dirname(cur), FILTER, '选择文本展开配置文件')
        if not path:
            return
        ini_write(INI_FILE, SECTION, 'config_file', path)
        self._stamp = None
        msg_status('文本展开：配置文件已设为 ' + path)

    def open_config(self):
        path = self.config_path()
        if not os.path.isfile(path):
            try:
                parent = os.path.dirname(path)
                if parent:
                    os.makedirs(parent, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(DEFAULT_CONFIG_TEXT)
            except OSError as e:
                msg_box('无法创建配置文件：\n' + str(e), MB_OK + MB_ICONERROR)
                return
        file_open(path)

    def reload_config(self):
        self._stamp = None
        path = self.config_path()
        if not os.path.isfile(path):
            msg_status('文本展开：配置文件不存在：' + path)
            return
        rules = self._load_rules()
        msg_status('文本展开：已重新加载 %d 条规则' % len(rules))

    def about(self):
        msg_box(
            '文本展开\n\n'
            '输入触发词后按空格，自动替换为配置的文本。\n'
            '配置文件每行一条：触发词=替换文本（以第一个等号分割）。\n'
            '触发词以空白、中英文标点或符号为分隔符。\n\n'
            '当前配置：%s\n规则数：%d' % (self.config_path(), len(self._load_rules())),
            MB_OK + MB_ICONINFO)

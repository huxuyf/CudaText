import re
from cudatext import *
from cudatext_keys import VK_ENTER

RE_UL = re.compile(r'^([ \t]*)([-*+])([ \t]+)(.*)$')
RE_OL = re.compile(r'^([ \t]*)(\d+)(\.)([ \t]+)(.*)$')
RE_FENCE = re.compile(r'^([ \t]*)(`{3,}|~{3,})([^\n]*)$')


class Command:

    def on_key(self, ed_self, key, state):
        if key != VK_ENTER:
            return
        if state:
            return
        if ed_self.get_prop(PROP_RO):
            return

        carets = ed_self.get_carets()
        if len(carets) != 1:
            return
        x, y, x2, y2 = carets[0]
        if y2 >= 0:
            return

        line = _get_line(ed_self, y)
        if not _is_relevant(ed_self, y, line):
            return
        if not _at_line_end(ed_self, y, x):
            return

        if _handle(ed_self, y, line):
            return False


def _get_line(ed, y):
    if y < 0 or y >= ed.get_line_count():
        return ''
    return ed.get_text_line(y) or ''


def _at_line_end(ed, y, x):
    n = ed.get_line_len(y)
    if n is None:
        n = len(_get_line(ed, y))
    return x >= n


def _is_relevant(ed, y, line):
    if RE_UL.match(line) or RE_OL.match(line) or RE_FENCE.match(line):
        return True
    if line.strip() == '' and y > 0 and RE_FENCE.match(_get_line(ed, y - 1)):
        return True
    return False


def _fence_before(ed, y):
    if y <= 0:
        return 0
    text = ed.get_text_substr(0, 0, 0, y) or ''
    return sum(1 for s in text.splitlines() if RE_FENCE.match(s))


def _in_code_block(ed, y):
    return _fence_before(ed, y) % 2 == 1


def _is_fence_open(ed, y):
    if not RE_FENCE.match(_get_line(ed, y)):
        return False
    return (_fence_before(ed, y) + 1) % 2 == 1


def _fence_mark(ed, y):
    m = RE_FENCE.match(_get_line(ed, y))
    return m.group(2) if m else '```'


def _handle(ed, y, line):
    in_code = _in_code_block(ed, y)

    if in_code:
        if line.strip() == '' and y > 0 and _is_fence_open(ed, y - 1):
            if y + 1 < ed.get_line_count() and RE_FENCE.match(_get_line(ed, y + 1)):
                return False
            mark = _fence_mark(ed, y - 1)
            pos = ed.insert(0, y, '\n' + mark)
            if pos:
                ed.set_caret(0, y)
                return True
        return False

    if RE_FENCE.match(line) and _is_fence_open(ed, y):
        mark = _fence_mark(ed, y)
        x = ed.get_line_len(y)
        if x is None:
            x = len(line)
        pos = ed.insert(x, y, '\n\n' + mark)
        if pos:
            ed.set_caret(0, y + 1)
            return True
        return False

    m = RE_OL.match(line)
    if m:
        indent, num, dot, sep, content = m.groups()
        if content.strip() == '':
            return _clear_item(ed, y)
        return _insert_prefix(ed, y, '%s%d.%s' % (indent, int(num) + 1, sep))

    m = RE_UL.match(line)
    if m:
        indent, bullet, sep, content = m.groups()
        if content.strip() == '':
            return _clear_item(ed, y)
        return _insert_prefix(ed, y, '%s%s%s' % (indent, bullet, sep))

    return False


def _insert_prefix(ed, y, prefix):
    x = ed.get_line_len(y)
    if x is None:
        x = len(_get_line(ed, y))
    pos = ed.insert(x, y, '\n' + prefix)
    if pos is None:
        return False
    ed.set_caret(pos[0], pos[1])
    return True


def _clear_item(ed, y):
    if ed.set_text_line(y, '') is False:
        return False
    ed.set_caret(0, y)
    return True

import os

from cudatext import *

_ = lambda s: s

CONFIG_FN = os.path.join(app_path(APP_DIR_SETTINGS), 'plugins.ini')
CONFIG_SEC = 'column_editor'

SIZE_W = 470

DEF_TEXT = ''
DEF_POS = '0'      # 0: insert at left edge of selection, 1: at right edge
DEF_START = '1'
DEF_STEP = '1'
DEF_WIDTH = '0'
DEF_DELMODE = '0'  # 0: remove range (shift left), 1: replace with spaces

MSG_NO_TARGET = _('Column Editor: select a column block (Alt+mouse drag) or add '
                  'multiple carets (Ctrl+click) on the target lines first.\n'
                  'Operation canceled to avoid changing the whole file.')
MSG_MULTILINE = _('The selection spans whole lines, not a column block.\n'
                  'Use a column selection (Alt+drag) or multiple carets instead.')
MSG_EMPTY_SEL = _('The column selection is empty (zero width), nothing to delete.')


def _tab_size(the_ed):
    try:
        n = int(the_ed.get_prop(PROP_TAB_SIZE))
        if n > 0:
            return n
    except Exception:
        pass
    return 4


def _col_to_char(line, col, tab):
    # convert visual column position (as stored in SelRect) to char position
    if col <= 0:
        return 0
    c = 0
    for i, ch in enumerate(line):
        if c >= col:
            return i
        c += (tab - c % tab) if ch == '\t' else 1
    return len(line)


def get_targets(the_ed):
    # returns list of (line_y, char_x1, char_x2), x2=-1 when caret has no selection
    # raises ValueError with user-friendly message when there is no valid target
    crts = the_ed.get_carets()

    if len(crts) >= 2:
        res = []
        for (x, y, xe, ye) in crts:
            if ye >= 0 and ye != y:
                raise ValueError(MSG_MULTILINE)
            if xe >= 0:
                x1, x2 = min(x, xe), max(x, xe)
            else:
                x1, x2 = x, -1
            item = (y, x1, x2)
            if item not in res:
                res.append(item)
        if not res:
            raise ValueError(MSG_NO_TARGET)
        return res

    if the_ed.get_sel_mode() == SEL_COLUMN:
        x1c, y1, x2c, y2 = the_ed.get_sel_rect()
        # a collapsed/leftover column mode can be single-line and zero-width,
        # which is not a real column block - don't touch the document then
        if (y2 <= y1) and (x2c <= x1c):
            raise ValueError(MSG_NO_TARGET)
        tab = _tab_size(the_ed)
        res = []
        for y in range(y1, y2 + 1):
            line = the_ed.get_text_line(y)
            res.append((y, _col_to_char(line, x1c, tab), _col_to_char(line, x2c, tab)))
        return res

    raise ValueError(MSG_NO_TARGET)


def describe_targets(targets):
    lines = sorted(set(y for (y, x1, x2) in targets))
    if len(lines) == 1:
        return _('Target: 1 line (line {})').format(lines[0] + 1)
    return _('Target: {} lines (lines {}-{})').format(
        len(lines), lines[0] + 1, lines[-1] + 1)


def apply_insert_text(the_ed, text, at_right=False):
    targets = get_targets(the_ed)
    n = 0
    for (y, x1, x2) in sorted(targets, key=lambda t: (t[0], t[1]), reverse=True):
        x = x2 if (at_right and x2 >= 0) else x1
        line = the_ed.get_text_line(y)
        if x > len(line):
            x = len(line)
        the_ed.insert(x, y, text)
        n += 1
    return n


def apply_insert_numbers(the_ed, start, step, width):
    targets = sorted(get_targets(the_ed), key=lambda t: (t[0], t[1]))
    values = []
    for i, (y, x1, x2) in enumerate(targets):
        s = str(start + i * step)
        if width > 0:
            if s.startswith('-'):
                s = '-' + s[1:].zfill(width)
            else:
                s = s.zfill(width)
        values.append((y, x1, s))

    n = 0
    for (y, x1, s) in reversed(sorted(values, key=lambda t: (t[0], t[1]))):
        line = the_ed.get_text_line(y)
        x = x1 if x1 <= len(line) else len(line)
        the_ed.insert(x, y, s)
        n += 1
    return n


def apply_delete(the_ed, mode):
    # mode 0: remove range and shift the rest left; mode 1: replace range with spaces
    targets = sorted(get_targets(the_ed), key=lambda t: (t[0], t[1]), reverse=True)
    n = 0
    for (y, x1, x2) in targets:
        if x2 < 0:
            continue
        line_len = the_ed.get_line_len(y)
        a = min(x1, line_len)
        b = min(x2, line_len)
        if b <= a:
            continue
        the_ed.delete(a, y, b, y)
        if mode == 1:
            the_ed.insert(a, y, ' ' * (b - a))
        n += 1
    if n == 0:
        raise ValueError(MSG_EMPTY_SEL)
    return n


def _get_targets_by_dialog(the_ed):
    try:
        return get_targets(the_ed), None
    except ValueError as e:
        return None, str(e)


def _ini_int(key, default):
    try:
        return int(ini_read(CONFIG_FN, CONFIG_SEC, key, default))
    except Exception:
        return int(default)


def _dlg_insert_text():
    targets, err = _get_targets_by_dialog(ed)
    if targets is None:
        msg_box(err, MB_OK + MB_ICONERROR)
        return

    c1 = chr(1)
    op_text = ini_read(CONFIG_FN, CONFIG_SEC, 'text', DEF_TEXT)
    op_pos = ini_read(CONFIG_FN, CONFIG_SEC, 'pos', DEF_POS)
    if op_pos not in ('0', '1'):
        op_pos = DEF_POS

    text = '\n'.join([
        c1.join(['type=label', 'pos=6,6,450,0', 'cap=' + _('Text to insert into each selected line:')]),
        c1.join(['type=edit', 'pos=6,26,455,0', 'val=' + op_text]),
        c1.join(['type=label', 'pos=6,56,450,0', 'cap=' + _('Insert position:')]),
        c1.join(['type=combo_ro', 'pos=6,76,455,0',
                 'items=' + '\t'.join([_('Left edge of selection'), _('Right edge of selection')]),
                 'val=' + op_pos]),
        c1.join(['type=label', 'pos=6,110,455,0', 'cap=' + describe_targets(targets)]),
        c1.join(['type=button', 'pos=270,136,370,0', 'cap=' + _('Insert'), 'ex0=1']),
        c1.join(['type=button', 'pos=376,136,455,0', 'cap=' + _('Cancel')]),
    ])

    res = dlg_custom(_('Column Editor: insert text'), SIZE_W, 180, text)
    if res is None:
        return
    btn, vals = res
    if btn != 5:
        return

    new_text = vals[1]
    new_pos = vals[3]
    ini_write(CONFIG_FN, CONFIG_SEC, 'text', new_text)
    ini_write(CONFIG_FN, CONFIG_SEC, 'pos', new_pos)

    if not new_text:
        msg_box(_('Enter the text to insert.'), MB_OK + MB_ICONERROR)
        return

    try:
        n = apply_insert_text(ed, new_text, at_right=(new_pos == '1'))
    except ValueError as e:
        msg_box(str(e), MB_OK + MB_ICONERROR)
        return
    msg_status(_('Column Editor: text inserted into {} line(s)').format(n))


def _dlg_insert_numbers():
    targets, err = _get_targets_by_dialog(ed)
    if targets is None:
        msg_box(err, MB_OK + MB_ICONERROR)
        return

    c1 = chr(1)
    op_start = ini_read(CONFIG_FN, CONFIG_SEC, 'num_start', DEF_START)
    op_step = ini_read(CONFIG_FN, CONFIG_SEC, 'num_step', DEF_STEP)
    op_width = ini_read(CONFIG_FN, CONFIG_SEC, 'num_width', DEF_WIDTH)

    text = '\n'.join([
        c1.join(['type=label', 'pos=6,6,450,0', 'cap=' + _('Start value:')]),
        c1.join(['type=spinedit', 'pos=6,26,120,0', 'ex0=-1000000', 'ex1=1000000', 'ex2=1', 'val=' + op_start]),
        c1.join(['type=label', 'pos=6,58,450,0', 'cap=' + _('Step (can be negative):')]),
        c1.join(['type=spinedit', 'pos=6,78,120,0', 'ex0=-1000000', 'ex1=1000000', 'ex2=1', 'val=' + op_step]),
        c1.join(['type=label', 'pos=6,110,450,0', 'cap=' + _('Zero-pad width (0 = no padding):')]),
        c1.join(['type=spinedit', 'pos=6,130,120,0', 'ex0=0', 'ex1=30', 'ex2=1', 'val=' + op_width]),
        c1.join(['type=label', 'pos=6,166,455,0', 'cap=' + describe_targets(targets)]),
        c1.join(['type=button', 'pos=270,192,370,0', 'cap=' + _('Insert'), 'ex0=1']),
        c1.join(['type=button', 'pos=376,192,455,0', 'cap=' + _('Cancel')]),
    ])

    res = dlg_custom(_('Column Editor: insert numbers'), SIZE_W, 240, text)
    if res is None:
        return
    btn, vals = res
    if btn != 7:
        return

    try:
        start = int(vals[1])
        step = int(vals[3])
        width = max(0, min(30, int(vals[5])))
    except ValueError:
        msg_box(_('Start, step and width must be integers.'), MB_OK + MB_ICONERROR)
        return

    ini_write(CONFIG_FN, CONFIG_SEC, 'num_start', str(start))
    ini_write(CONFIG_FN, CONFIG_SEC, 'num_step', str(step))
    ini_write(CONFIG_FN, CONFIG_SEC, 'num_width', str(width))

    try:
        n = apply_insert_numbers(ed, start, step, width)
    except ValueError as e:
        msg_box(str(e), MB_OK + MB_ICONERROR)
        return
    msg_status(_('Column Editor: numbers inserted into {} line(s)').format(n))


def _dlg_delete():
    targets, err = _get_targets_by_dialog(ed)
    if targets is None:
        msg_box(err, MB_OK + MB_ICONERROR)
        return

    c1 = chr(1)
    op_mode = ini_read(CONFIG_FN, CONFIG_SEC, 'delmode', DEF_DELMODE)
    if op_mode not in ('0', '1'):
        op_mode = DEF_DELMODE

    text = '\n'.join([
        c1.join(['type=label', 'pos=6,6,455,0', 'cap=' + describe_targets(targets)]),
        c1.join(['type=label', 'pos=6,34,450,0', 'cap=' + _('Mode:')]),
        c1.join(['type=combo_ro', 'pos=6,54,455,0',
                 'items=' + '\t'.join([_('Remove range (shift left)'), _('Replace with spaces')]),
                 'val=' + op_mode]),
        c1.join(['type=button', 'pos=270,92,370,0', 'cap=' + _('Delete'), 'ex0=1']),
        c1.join(['type=button', 'pos=376,92,455,0', 'cap=' + _('Cancel')]),
    ])

    res = dlg_custom(_('Column Editor: delete content'), SIZE_W, 140, text)
    if res is None:
        return
    btn, vals = res
    if btn != 3:
        return

    mode = vals[2]
    ini_write(CONFIG_FN, CONFIG_SEC, 'delmode', mode)

    try:
        n = apply_delete(ed, 1 if mode == '1' else 0)
    except ValueError as e:
        msg_box(str(e), MB_OK + MB_ICONERROR)
        return
    msg_status(_('Column Editor: content removed from {} line(s)').format(n))


class Command:
    def dlg_insert_text(self):
        _dlg_insert_text()

    def dlg_insert_numbers(self):
        _dlg_insert_numbers()

    def dlg_delete(self):
        _dlg_delete()


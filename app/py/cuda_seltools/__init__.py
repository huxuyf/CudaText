import bisect

from cudatext import *
import cudax_lib as apx
from cudax_lib import get_translation

from .logic import transform

_ = get_translation(__file__)

CONFIG_JSON = 'cuda_seltools.json'
OUTPUT_REPLACE = 'replace'
OUTPUT_CLIPBOARD = 'clipboard'


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


def _line_starts(text):
    starts = [0]
    pos = 0
    while True:
        pos = text.find('\n', pos)
        if pos < 0:
            break
        pos += 1
        starts.append(pos)
    return starts


def _pos_to_offset(starts, x, y):
    if y < 0:
        return 0
    if y >= len(starts):
        return starts[-1] + x if starts else 0
    return starts[y] + x


def _offset_to_pos(starts, offset):
    if not starts:
        return (0, 0)
    line = bisect.bisect_right(starts, offset) - 1
    if line < 0:
        line = 0
    return (offset - starts[line], line)


class Command:

    def __init__(self):
        mode = _cfg_get('output_mode', OUTPUT_REPLACE)
        if mode not in (OUTPUT_REPLACE, OUTPUT_CLIPBOARD):
            mode = OUTPUT_REPLACE
        self.output_mode = mode

    def _collect_selections(self):
        text = ed.get_text_all()
        starts = _line_starts(text)
        result = []
        try:
            carets = ed.get_carets()
        except Exception:
            return result

        for posx, posy, endx, endy in carets:
            if endx < 0 or endy < 0:
                continue
            off1 = _pos_to_offset(starts, int(posx), int(posy))
            off2 = _pos_to_offset(starts, int(endx), int(endy))
            start = min(off1, off2)
            end = max(off1, off2)
            if end <= start:
                continue
            sx, sy = _offset_to_pos(starts, start)
            ex, ey = _offset_to_pos(starts, end)
            result.append({
                'start': start,
                'end': end,
                'sx': sx,
                'sy': sy,
                'ex': ex,
                'ey': ey,
                'text': text[start:end],
            })

        # Merge overlapping selections, otherwise bottom-up replacement corrupts
        # the text of the upper range.
        result.sort(key=lambda item: item['start'])
        merged = []
        for item in result:
            if merged and item['start'] <= merged[-1]['end']:
                last = merged[-1]
                if item['end'] > last['end']:
                    last['end'] = item['end']
                    last['ex'], last['ey'] = _offset_to_pos(starts, last['end'])
                    last['text'] = text[last['start']:last['end']]
            else:
                merged.append(item)
        return merged

    def _single_selection(self):
        """Return the only selection without reading the whole document."""
        try:
            carets = ed.get_carets()
        except Exception:
            return None
        if len(carets) != 1:
            return None
        x1, y1, x2, y2 = carets[0]
        if x2 < 0 or y2 < 0:
            return None
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        if (x2, y2) < (x1, y1):
            x1, y1, x2, y2 = x2, y2, x1, y1
        if (x1, y1) == (x2, y2):
            return None
        return {
            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
            'text': ed.get_text_substr(x1, y1, x2, y2),
        }

    @staticmethod
    def _end_pos(x1, y1, text):
        parts = text.split('\n')
        if len(parts) == 1:
            return (x1 + len(text), y1)
        return (len(parts[-1]), y1 + len(parts) - 1)

    def _run_single(self, kind, item):
        try:
            new = transform(kind, item['text'])
        except Exception as e:
            msg_box(
                _('无法转换选中文本：\n') + str(e),
                MB_OK + MB_ICONERROR,
            )
            return

        if self.output_mode == OUTPUT_CLIPBOARD:
            app_proc(PROC_SET_CLIP, new)
            msg_status(_('已复制转换结果到剪贴板'))
            return

        try:
            ed.action(EDACTION_UNDOGROUP_BEGIN)
            try:
                ed.replace(item['x1'], item['y1'], item['x2'], item['y2'], new)
            finally:
                ed.action(EDACTION_UNDOGROUP_END)
            x, y = self._end_pos(item['x1'], item['y1'], new)
            ed.set_caret(x, y, -1, -1, CARET_SET_ONE)
            msg_status(_('已处理 1 处选区'))
        except Exception as e:
            msg_box(
                _('无法替换选中文本：\n') + str(e),
                MB_OK + MB_ICONERROR,
            )

    def _run(self, kind):
        if ed.get_sel_mode() == SEL_COLUMN:
            msg_status(_('不支持列选择模式，请改用普通选择'))
            return

        one = self._single_selection()
        if one is not None:
            self._run_single(kind, one)
            return

        selections = self._collect_selections()
        if not selections:
            msg_status(_('请先选中文本'))
            return

        # Transform everything before touching the document, so a failure in
        # one caret does not leave a partially transformed document.
        try:
            for item in selections:
                item['new'] = transform(kind, item['text'])
        except Exception as e:
            msg_box(
                _('无法转换选中文本：\n') + str(e),
                MB_OK + MB_ICONERROR,
            )
            return

        if self.output_mode == OUTPUT_CLIPBOARD:
            text = '\n'.join(item['new'] for item in selections)
            app_proc(PROC_SET_CLIP, text)
            msg_status(_('已复制转换结果到剪贴板'))
            return

        try:
            self._replace_selections(selections)
            msg_status(
                _('已处理 %d 处选区') % len(selections)
            )
        except Exception as e:
            msg_box(
                _('无法替换选中文本：\n') + str(e),
                MB_OK + MB_ICONERROR,
            )

    def _replace_selections(self, selections):
        ed.action(EDACTION_UNDOGROUP_BEGIN)
        try:
            # Replace from the bottom of the document to the top, so earlier
            # replacements do not invalidate the coordinates of later ones.
            ordered = sorted(selections, key=lambda item: item['start'], reverse=True)
            for item in ordered:
                ed.replace(
                    item['sx'],
                    item['sy'],
                    item['ex'],
                    item['ey'],
                    item['new'],
                )

            final_text = ed.get_text_all()
            final_starts = _line_starts(final_text)

            # Compute final caret offsets from the original offsets plus the
            # length delta of all selections before each one.
            delta = 0
            targets = []
            for item in sorted(selections, key=lambda value: value['start']):
                target = item['start'] + delta + len(item['new'])
                targets.append(target)
                delta += len(item['new']) - (item['end'] - item['start'])

            positions = [_offset_to_pos(final_starts, offset) for offset in targets]
            if positions:
                ed.set_caret(
                    positions[0][0],
                    positions[0][1],
                    -1,
                    -1,
                    CARET_SET_ONE,
                )
                for x, y in positions[1:]:
                    ed.set_caret(x, y, -1, -1, CARET_ADD)
        finally:
            ed.action(EDACTION_UNDOGROUP_END)

    def b64_encode(self):
        self._run('b64_encode')

    def b64_decode(self):
        self._run('b64_decode')

    def url_encode(self):
        self._run('url_encode')

    def url_decode(self):
        self._run('url_decode')

    def evaluate(self):
        self._run('eval')

    def toggle_output(self):
        if self.output_mode == OUTPUT_REPLACE:
            self.output_mode = OUTPUT_CLIPBOARD
        else:
            self.output_mode = OUTPUT_REPLACE
        _cfg_set('output_mode', self.output_mode)
        display = _('替换') if self.output_mode == OUTPUT_REPLACE else _('剪贴板')
        msg_status(_('选中文本工具输出模式：') + display)

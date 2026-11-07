import cudatext as app
from cudatext import ed, PROP_RO


class Command:
    def join_lines(self):
        if ed is None or ed.get_prop(PROP_RO):
            return

        count = ed.get_line_count()
        if count < 2:
            app.msg_status('Nothing to join: document has only one line')
            return

        carets = ed.get_carets()
        if not carets:
            return

        # Process bottom-up, so line indexes of upper carets do not shift.
        lines = sorted({y1 for (x1, y1, x2, y2) in carets}, reverse=True)
        joined = 0
        app.ed.action(app.EDACTION_UNDOGROUP_BEGIN)
        try:
            for y in lines:
                if 0 <= y < count - 1:
                    # Delete from end of line y to start of line y+1: removes only the EOL.
                    ed.delete(ed.get_line_len(y), y, 0, y + 1)
                    joined += 1
        finally:
            app.ed.action(app.EDACTION_UNDOGROUP_END)

        if joined:
            app.msg_status('Joined line with next line')
        else:
            app.msg_status('Nothing to join: caret is on the last line')

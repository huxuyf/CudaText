def push_closed(stack, path, max_count):
    """Push a path onto a LIFO stack, moving duplicates to the top."""
    if not path:
        return stack
    if path in stack:
        stack.remove(path)
    stack.append(path)
    if max_count > 0 and len(stack) > max_count:
        del stack[:len(stack) - max_count]
    return stack


def remove_path(stack, path):
    """Remove a path from the stack; returns True if it was present."""
    try:
        stack.remove(path)
        return True
    except ValueError:
        return False

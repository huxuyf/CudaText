import ast
import base64
import binascii
import operator
import urllib.parse

MAX_EXPR_LEN = 500
MAX_POW_EXPONENT = 1000
MAX_RESULT_BITS = 33220  # 约 1 万位十进制，防止嵌套幂/乘法把 UI 卡死

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def b64_encode(text):
    return base64.b64encode(text.encode('utf-8')).decode('ascii')


def b64_decode(text):
    compact = ''.join(text.split())
    if not compact:
        raise ValueError('Base64 内容为空')
    compact += '=' * (-len(compact) % 4)
    try:
        data = base64.b64decode(compact, validate=True)
    except (binascii.Error, ValueError):
        try:
            data = base64.b64decode(compact, altchars=b'-_', validate=True)
        except Exception:
            raise ValueError('Base64 内容无效')
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError('Base64 结果不是有效的 UTF-8 文本')
    if '\x00' in text:
        raise ValueError('Base64 结果包含 NUL 字符')
    return text


def url_encode(text):
    return urllib.parse.quote_plus(text, safe='')


def url_decode(text):
    return urllib.parse.unquote_plus(text)


def eval_expr(text):
    expression = text.strip()
    if not expression:
        raise ValueError('表达式为空')
    if len(expression) > MAX_EXPR_LEN:
        raise ValueError('表达式过长')
    try:
        tree = ast.parse(expression, mode='eval')
    except SyntaxError:
        raise ValueError('表达式语法无效')

    value = _eval_node(tree.body)
    if isinstance(value, float):
        if value != value or value in (float('inf'), float('-inf')):
            raise ValueError('结果不是有限数字')
        if value.is_integer():
            return str(int(value))
    return str(value)


def _eval_node(node):
    if isinstance(node, ast.Constant):
        if type(node.value) in (int, float):
            return node.value
        raise ValueError('仅允许数字常量')

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BIN_OPS:
            raise ValueError('不支持的运算符')
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_POW_EXPONENT:
            raise ValueError('指数过大')
        if isinstance(node.op, ast.Pow) and isinstance(left, int):
            if left.bit_length() * max(1, abs(right)) > MAX_RESULT_BITS:
                raise ValueError('结果过大')
        try:
            value = _BIN_OPS[op_type](left, right)
        except ZeroDivisionError:
            raise ValueError('除数为零')
        except (OverflowError, ValueError):
            raise ValueError('算术结果无效')
        if isinstance(value, int) and value.bit_length() > MAX_RESULT_BITS:
            raise ValueError('结果过大')
        return value

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPS:
            raise ValueError('不支持的一元运算符')
        return _UNARY_OPS[op_type](_eval_node(node.operand))

    # Explicitly reject names, calls, attributes, subscripts, comparisons,
    # strings, and anything else that is not a pure arithmetic expression.
    raise ValueError('仅允许算术表达式')


def transform(kind, text):
    if kind == 'b64_encode':
        return b64_encode(text)
    if kind == 'b64_decode':
        return b64_decode(text)
    if kind == 'url_encode':
        return url_encode(text)
    if kind == 'url_decode':
        return url_decode(text)
    if kind == 'eval':
        return eval_expr(text)
    raise ValueError('未知的转换类型')

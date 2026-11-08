"""纯逻辑实现，不依赖 CudaText API，便于单独测试。"""


def read_text_file(path):
    """读取配置文本，兼容 UTF-8（含 BOM）与 Windows 常见的 GBK 编码。"""
    with open(path, 'rb') as f:
        data = f.read()
    for enc in ('utf-8-sig', 'gbk'):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode('utf-8', errors='replace')


def is_token_char(ch):
    """触发词允许的字符：字母、数字、下划线。"""
    return ch.isalnum() or ch == '_'


def find_token_start(line, x):
    """从 x 向前扫描，返回分隔符之后第一个字符的位置。"""
    i = min(x, len(line))
    while i > 0 and is_token_char(line[i - 1]):
        i -= 1
    return i


def has_cjk(text):
    """判断文本是否含中日韩字符。"""
    for ch in text:
        o = ord(ch)
        if (0x3040 <= o <= 0x30FF or
                0x3400 <= o <= 0x4DBF or
                0x4E00 <= o <= 0x9FFF or
                0xAC00 <= o <= 0xD7AF or
                0xF900 <= o <= 0xFAFF or
                0x20000 <= o <= 0x2FA1F):
            return True
    return False


def parse_rules(text):
    """解析配置文件：每行一条，以第一个等号分割。"""
    rules = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.lstrip().startswith('#'):
            continue
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        if not key:
            continue
        rules[key] = value
    return rules


def find_replacement(line, x, rules, skip_cjk=True):
    """返回 (起始列, 触发词, 替换文本)，未命中返回 None。"""
    start = find_token_start(line, x)
    token = line[start:x]
    if not token:
        return None
    if skip_cjk and has_cjk(token):
        return None
    value = rules.get(token)
    if value is None:
        return None
    return start, token, value

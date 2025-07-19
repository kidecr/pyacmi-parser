import re

FLOAT_PATTERN = re.compile(r'^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$')
def to_float(s: str, default: float = None) -> float:
    s = s.strip()
    if not s:
        return default
    if FLOAT_PATTERN.match(s):
        return float(s)
    return default
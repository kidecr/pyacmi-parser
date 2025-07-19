from acmiparse.cutils import _c_to_float, _c_parse_body
from math import nan
from typing import Tuple

def to_float(value: str, default: float = nan):
    return _c_to_float(value, default)

def parse_body(id: int, body: str) -> Tuple['ACMIObjectCoordinates', 'ACMIEvent', 'ACMIObjectProperties']:
    return _c_parse_body(id, body)

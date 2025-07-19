# parser_fast.pyx

import re
from math import nan
from .model import ACMIPropertyRegistry, ACMIObjectCoordinates, ACMIEvent, ACMIObjectProperties, ACMIObject
# 预先编译正则表达式
cdef regex_FLOAT_PATTERN = re.compile(r'^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$')

# ---------- 工具函数 ----------
cpdef public float _c_to_float(str s, float default):
    s = s.strip()
    if not s:
        return default
    if regex_FLOAT_PATTERN.match(s):
        try:
            return float(s)
        except:
            return default
    return default

cdef inline tuple _c_parse_key_value(str kv):
    cdef int idx = kv.find('=')
    if idx == -1:
        return (kv.strip(), None)
    return (kv[:idx].strip(), kv[idx+1:].strip())

cdef public object __c_parse_body(int id, str body):
    cdef object coords = None  # type: ACMIObjectCoordinates
    cdef object event = None   # type: ACMIEvent
    cdef object props = None   # type: ACMIObjectProperties

    cdef list parts
    cdef int n
    cdef float val

    for kv in body.split(','):
        k, v = _c_parse_key_value(kv)
        if not k:
            continue

        if k == 'T':
            coords = ACMIObjectCoordinates(object_id=id)
            parts = [x.strip() for x in v.split('|')]
            n = len(parts)
            if n == 3:
                coords.longitude = _c_to_float(parts[0], nan)
                coords.latitude  = _c_to_float(parts[1], nan)
                coords.altitude  = _c_to_float(parts[2], nan)
            elif n == 5:
                coords.longitude = _c_to_float(parts[0], nan)
                coords.latitude  = _c_to_float(parts[1], nan)
                coords.altitude  = _c_to_float(parts[2], nan)
                coords.u         = _c_to_float(parts[3], nan)
                coords.v         = _c_to_float(parts[4], nan)
            elif n == 6:
                coords.longitude = _c_to_float(parts[0], nan)
                coords.latitude  = _c_to_float(parts[1], nan)
                coords.altitude  = _c_to_float(parts[2], nan)
                coords.roll      = _c_to_float(parts[3], nan)
                coords.pitch     = _c_to_float(parts[4], nan)
                coords.yaw       = _c_to_float(parts[5], nan)
            elif n == 9:
                coords.longitude = _c_to_float(parts[0], nan)
                coords.latitude  = _c_to_float(parts[1], nan)
                coords.altitude  = _c_to_float(parts[2], nan)
                coords.roll      = _c_to_float(parts[3], nan)
                coords.pitch     = _c_to_float(parts[4], nan)
                coords.yaw       = _c_to_float(parts[5], nan)
                coords.u         = _c_to_float(parts[6], nan)
                coords.v         = _c_to_float(parts[7], nan)
                coords.heading   = _c_to_float(parts[8], nan)
            else:
                # logger.warning(f"无法解析坐标: {v}")
                pass

        elif k == 'Event':
            event = ACMIEvent(object_id=id)
            parts = [x.strip() for x in v.split('|')]
            n = len(parts)
            if n > 0:
                event.event_type = parts[0]
            if n > 2:
                event.object_ids = [int(x, 16) for x in parts[1:-1] if x]
            if n > 1:
                event.event_text = parts[-1]
            else:
                event.event_text = ''

        else:
            if not props:
                props = ACMIObjectProperties()
            if k in ACMIPropertyRegistry.OBJECT_PROPERTIES_ALLOWED_TEXT_KEYS:
                if not props.text_properties:
                    props.text_properties = {}
                props.text_properties[k] = v
            elif k in ACMIPropertyRegistry.OBJECT_PROPERTIES_ALLOWED_NUMERIC_KEYS:
                if not props.numeric_properties:
                    props.numeric_properties = {}
                props.numeric_properties[k] = _c_to_float(v, nan)
            else:
                if not props.text_properties:
                    props.text_properties = {}
                props.text_properties[k] = v

    return coords, event, props


cpdef public object _c_parse_body(int id, str body):
    return __c_parse_body(id, body)

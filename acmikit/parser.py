from dataclasses import dataclass
from typing import Dict, List, Optional
import re
from typing import Iterator, TextIO, Any, Dict, Tuple
from .reader import AcmiFileReader
from .model import *

@dataclass
class _HeaderParsed:
    header: "ACMIHeader"

@dataclass
class _GlobalProp:
    key: str
    value: str

@dataclass
class _FrameBegin:
    time_offset: float

@dataclass
class _ObjectSpawn:
    time_offset: float
    obj_id: int
    coords: "ACMIObjectCoordinates"
    props: "ACMIObjectProperties"

@dataclass
class _ObjectUpdate:
    time_offset: float
    obj_id: int
    coords: Optional["ACMIObjectCoordinates"]  # 可能只改属性
    props: Optional["ACMIObjectProperties"]    # 可能只改坐标

@dataclass
class _ObjectRemove:
    time_offset: float
    obj_id: int

@dataclass
class _EventInjected:
    time_offset: float
    event: "ACMIEvent"


class ACMIParser:
    # ---------- 正则 ----------
    _RE_HEADER   = re.compile(r'^(FileType|FileVersion)=(.*)$')
    _RE_FRAME    = re.compile(r'^#([0-9.+-]+)\s*$')
    _RE_REMOVE   = re.compile(r'^-([0-9a-fA-F]+)\s*$')
    _RE_COMMENT  = re.compile(r'^\s*//')
    _RE_UPDATE   = re.compile(r'^([0-9a-fA-F]+),(.*)$')
    _RE_SPLIT    = re.compile(r'(?<!\\),')

    def __init__(self, fp: TextIO):
        self._fp = fp
        self._time = 0.0

    # ---------- 对外 API ----------
    def events(self) -> Iterator[Any]:
        header_done = False
        header = ACMIHeader()

        for raw in self._fp:
            raw = raw.rstrip('\n\r')
            if not raw or self._RE_COMMENT.match(raw):
                continue

            # ---- 解析文件头两行 ----
            if not header_done:
                m = self._RE_HEADER.match(raw)
                if m:
                    key, val = m.groups()
                    if key == 'FileType':
                        header.file_type = val
                    elif key == 'FileVersion':
                        header.file_version = val
                    continue
                else:
                    yield _HeaderParsed(header)
                    header_done = True  # 后面不再收 header

            # ---- 时间帧 ----
            m = self._RE_FRAME.match(raw)
            if m:
                self._time = float(m.group(1))
                yield _FrameBegin(self._time)
                continue

            # ---- 移除对象 ----
            m = self._RE_REMOVE.match(raw)
            if m:
                yield _ObjectRemove(self._time, int(m.group(1), 16))
                continue

            # ---- 属性更新 ----
            m = self._RE_UPDATE.match(raw)
            if m:
                oid_hex, body = m.groups()
                oid = int(oid_hex, 16)
                coords, props = self._parse_body(body)
                if oid == 0:
                    # 全局属性
                    for k, v in props.text_properties.items():
                        yield _GlobalProp(k, str(v))
                    for k, v in props.numeric_properties.items():
                        yield _GlobalProp(k, str(v))
                else:
                    # 判断是不是首次出现
                    if oid not in self._first_seen:
                        self._first_seen.add(oid)
                        yield _ObjectSpawn(self._time, oid, coords, props)
                    else:
                        yield _ObjectUpdate(self._time, oid, coords, props)
                continue

            # ---- 事件行（Event=...） ----
            if 'Event=' in raw:
                ev = self._parse_event(raw)
                yield _EventInjected(self._time, ev)

    # ---------- 内部工具 ----------
    _first_seen: set = set()   # 记录已出现的对象

    def _parse_body(self, body: str) -> Tuple[ACMIObjectCoordinates, ACMIObjectProperties]:
        coords = ACMIObjectCoordinates(object_id=0)
        props  = ACMIObjectProperties()
        for kv in self._split_props(body):
            k, v = kv.split('=', 1)
            k = k.strip()
            v = v.strip()
            # --- T 特殊处理 ---
            if k == 'T':
                parts = v.split('|')
                coords.longitude  = float(parts[0]) if parts[0] else None
                coords.latitude   = float(parts[1]) if parts[1] else None
                coords.altitude   = float(parts[2]) if parts[2] else None
                coords.roll       = float(parts[3]) if len(parts) > 3 and parts[3] else None
                coords.pitch      = float(parts[4]) if len(parts) > 4 and parts[4] else None
                coords.yaw        = float(parts[5]) if len(parts) > 5 and parts[5] else None
                coords.u          = float(parts[6]) if len(parts) > 6 and parts[6] else None
                coords.v          = float(parts[7]) if len(parts) > 7 and parts[7] else None
                coords.heading    = float(parts[8]) if len(parts) > 8 and parts[8] else None
            else:
                # 放入 props
                try:
                    num_val = float(v)
                    props.numeric_properties = props.numeric_properties or {}
                    props.numeric_properties[k] = num_val
                except ValueError:
                    props.text_properties = props.text_properties or {}
                    props.text_properties[k] = v
        return coords, props



    @staticmethod
    def _split_props(body: str) -> List[str]:
        return ACMIParser._RE_SPLIT.split(body)

    def _parse_event(self, raw: str) -> ACMIEvent:
        # 简单实现：假设整行就是 "Event=type|id1|id2|text"
        _, rest = raw.split('=', 1)
        segments = rest.split('|')
        ev_type = segments[0]
        ids = [int(x, 16) for x in segments[1:-1] if x.strip()]
        text = segments[-1] if len(segments) > 1 else ''
        return ACMIEvent(object_id=0, event_type=ev_type, object_ids=ids, event_text=text)
    

# ---------- 填充器 ----------
class ACMILoader:
    """
    逐事件地把 .acmi 流填充到 ACMIFile / ACMIFrame。
    用法：
        for frame in ACMILoader.from_file('demo.acmi'):
            do_something(frame)
    """
    def __init__(self, fp: TextIO):
        self._parser = ACMIParser(fp)
        self._reset()

    # ---------- 内部状态 ----------
    def _reset(self):
        self._file = ACMIFile(
            header=ACMIHeader(),
            global_properties=ACMIGlobalProperties(),
            frames=[]
        )
        self._current_frame: Optional[ACMIFrame] = None
        self._obj_table: Dict[int, ACMIObject] = {}  # 当前帧存活对象

    # ---------- 生成器 ----------
    def frames(self) -> Iterator[ACMIFrame]:
        """每完成一帧就 yield；文件结束后 yield 最后一帧（如果有）"""
        for ev in self._parser.events():
            self._handle(ev)
            # 当收到 FrameBegin 时，说明上一帧已完整
            if isinstance(ev, _FrameBegin):
                if self._current_frame is not None:
                    yield self._current_frame
                self._obj_table.clear()  # 开始新帧
        # 文件结束：如果最后一帧没触发 FrameBegin，也 yield
        if self._current_frame is not None:
            yield self._current_frame

    # ---------- 事件分发 ----------
    def _handle(self, ev):
        if isinstance(ev, _HeaderParsed):
            self._file.header = ev.header

        elif isinstance(ev, _GlobalProp):
            # 根据 key 决定放入 text 还是 numeric
            try:
                val = float(ev.value)
                self._file.global_properties.numeric_properties = \
                    self._file.global_properties.numeric_properties or {}
                self._file.global_properties.numeric_properties[ev.key] = val
            except ValueError:
                self._file.global_properties.text_properties = \
                    self._file.global_properties.text_properties or {}
                self._file.global_properties.text_properties[ev.key] = ev.value

        elif isinstance(ev, _FrameBegin):
            self._current_frame = ACMIFrame(timestamp=ev.time_offset, objects=[])

        elif isinstance(ev, _ObjectSpawn):
            obj = ACMIObject(
                object_id=ev.obj_id,
                time_offset=ev.time_offset,
                object_coordinates=ev.coords,
                object_properties=ev.props
            )
            self._obj_table[ev.obj_id] = obj

        elif isinstance(ev, _ObjectUpdate):
            # 取出旧对象或新建
            obj = self._obj_table.get(ev.obj_id)
            if obj is None:  # 容错：漏掉 Spawn
                obj = ACMIObject(object_id=ev.obj_id, time_offset=ev.time_offset)
                self._obj_table[ev.obj_id] = obj
            # 合并坐标和属性
            if ev.coords:
                obj.object_coordinates = ev.coords
            if ev.props:
                obj.object_properties = ev.props

        elif isinstance(ev, _ObjectRemove):
            self._obj_table.pop(ev.obj_id, None)

        elif isinstance(ev, _EventInjected):
            # 目前只给 object_id=0 的事件，后续可扩展
            pass  # 需要时把 ev.event 挂到对应对象上

        # 每收到任何对象变动，实时写回当前帧
        if self._current_frame is not None:
            self._current_frame.objects = list(self._obj_table.values())

    # ---------- 快捷构造 ----------
    @classmethod
    def from_file(cls, path: str) -> Iterator[ACMIFrame]:
        with open(path, 'rt', encoding='utf-8') as fp:
            yield from cls(fp).frames()
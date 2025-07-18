from dataclasses import dataclass
from typing import Dict, List, Optional
import re
import logging
from typing import Iterator, TextIO, Any, Dict, Tuple
from .reader import ACMIFileReader
from .model import *
from .utils import *

logger = logging.getLogger(__name__)

@dataclass
class _HeaderParsed:
    header: ACMIHeader

@dataclass
class _GlobalProp:
    obj_id: int
    key: str
    value: str

@dataclass
class _FrameBegin:
    time_offset: float

@dataclass
class _ObjectUpdate:
    obj_id: int
    coords: Optional[ACMIObjectCoordinates]  # 可能只改坐标
    event: Optional[ACMIEvent]               # 可能只发生事件
    props: Optional[ACMIObjectProperties]    # 可能只改属性

@dataclass
class _ObjectRemove:
    obj_id: int




class ACMIParser:
    # ---------- 正则 ----------
    _RE_HEADER   = re.compile(r'^(FileType|FileVersion)=(.*)$') # 解析文件头
    _RE_FRAME    = re.compile(r'^#\s*([0-9.+-]+)\s*$')             # 解析#时间帧
    _RE_REMOVE   = re.compile(r'^-([0-9a-fA-F]+)\s*$')          # 解析-对象移除
    _RE_COMMENT  = re.compile(r'^\s*//')                        # 忽略注释行
    _RE_UPDATE   = re.compile(r'^([0-9a-fA-F]+),(.*)$')         # 解析对象更新
    _RE_SPLIT    = re.compile(r'(?<!\\),')                      # 忽略属性分隔符','但忽略'\,'防止误分割
    
    _first_seen: set = set()   # 记录已出现的对象

    def __init__(self, file: str, encoding: str = 'utf-8-sig'):
        self.reader = ACMIFileReader(file_path=file, encoding=encoding)
        self._time = 0.0

    # ---------- 对外 API ----------
    def events(self) -> Iterator[Any]:
        header_done = False
        global_prop_done = False
        header = ACMIHeader()

        for raw in self.reader.read_lines():
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
                    yield _HeaderParsed(header) # 发送文件头
                    header_done = True  # 后面不再收 header
                    
            if not global_prop_done:
                m = self._RE_UPDATE.match(raw)
                if m:
                    oid_hex, body = m.groups()
                    oid = int(oid_hex, 16)
                    k, v = self._parse_global_props(body)
                    if k in ACMIPropertyRegistry.GLOBAL_PROPERTIES_ALLOWED_TEXT_KEYS + ACMIPropertyRegistry.GLOBAL_PROPERTIES_ALLOWED_NUMERIC_KEYS:
                        yield _GlobalProp(oid, k, v)
                        continue
                    else:
                        global_prop_done = True # 全局属性解析完毕

            # ---- 属性更新 ----
            m = self._RE_UPDATE.match(raw)
            if m:
                oid_hex, body = m.groups()
                oid = int(oid_hex, 16)
                
                coords, event, props = self._parse_body(oid, body)
                yield _ObjectUpdate(oid, coords, event, props)
                continue
            
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

    # ---------- 内部工具 ----------
    def _parse_body(self, id, body: str) -> Tuple[ACMIObjectCoordinates, ACMIEvent, ACMIObjectProperties]:
        coords = None 
        props  = None 
        event  = None 
        for kv in self._split_props(body):
            k, v = kv.split('=', 1)
            k = k.strip()
            v = v.strip()
            # --- T 特殊处理 ---
            if k == 'T':
                coords = ACMIObjectCoordinates(object_id=id)
                parts = v.split('|')
                if len(parts) == 3:
                    coords.longitude = to_float(parts[0])  # 经度
                    coords.latitude  = to_float(parts[1])  # 纬度
                    coords.altitude  = to_float(parts[2])  # 高度
                elif len(parts) == 5:
                    coords.longitude = to_float(parts[0])  # 经度
                    coords.latitude  = to_float(parts[1])  # 纬度
                    coords.altitude  = to_float(parts[2])  # 高度
                    coords.u         = to_float(parts[3])  # U
                    coords.v         = to_float(parts[4])  # V
                elif len(parts) == 6:
                    coords.longitude = to_float(parts[0])  # 经度
                    coords.latitude  = to_float(parts[1])  # 纬度
                    coords.altitude  = to_float(parts[2])  # 高度
                    coords.roll      = to_float(parts[3])  # Roll
                    coords.pitch     = to_float(parts[4])  # Pitch
                    coords.yaw       = to_float(parts[5])  # Yaw
                elif len(parts) == 9:
                    coords.longitude = to_float(parts[0])  # 经度
                    coords.latitude  = to_float(parts[1])  # 纬度
                    coords.altitude  = to_float(parts[2])  # 高度
                    coords.roll      = to_float(parts[3])  # Roll
                    coords.pitch     = to_float(parts[4])  # Pitch
                    coords.yaw       = to_float(parts[5])  # Yaw
                    coords.u         = to_float(parts[6])  # U
                    coords.v         = to_float(parts[7])  # V
                    coords.heading   = to_float(parts[8])  # Heading
                else:
                    logger.warning(f"无法解析坐标: {v}")
            elif k == 'Event':
                event = ACMIEvent(object_id=id)
                parts = v.split('|')
                event.event_type = parts[0]
                event.object_ids = [int(x, 16) for x in parts[1:-1] if x.strip()] if len(parts) > 2 else []
                event.event_text = parts[-1] if len(parts) > 1 else ''
            else:
                props = ACMIObjectProperties() if not props else props
                if k in ACMIPropertyRegistry.OBJECT_PROPERTIES_ALLOWED_TEXT_KEYS:       # 字符串属性较少，出现频率更高，放前面
                    props.text_properties = props.text_properties or {}
                    props.text_properties[k] = v
                elif k in ACMIPropertyRegistry.OBJECT_PROPERTIES_ALLOWED_NUMERIC_KEYS:
                    num_val = float(v)
                    props.numeric_properties = props.numeric_properties or {}
                    props.numeric_properties[k] = num_val
                else:
                    props.text_properties = props.text_properties or {}
                    props.text_properties[k] = v
        return coords, event, props

    @staticmethod
    def _split_props(body: str) -> List[str]:
        return ACMIParser._RE_SPLIT.split(body)

    def _parse_global_props(self, body: str) -> Tuple[str, str]:
        k, v = body.split('=', 1)
        return k.strip(), v.strip()
        
    

# ---------- 填充器 ----------
class ACMILoader:
    """
    逐事件地把 .acmi 流填充到 ACMIFile / ACMIFrame。
    用法：
        for frame in ACMILoader.from_file('demo.acmi'):
            do_something(frame)
    """
    def __init__(self, file_path: str, encoding: str = 'utf-8-sig'):
        self._parser = ACMIParser(file=file_path, encoding=encoding)
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
        self.timestamp = 0

    # ---------- 生成器 ----------
    def load(self) -> ACMIFile:
        """每完成一帧就 yield；文件结束后 yield 最后一帧（如果有）"""
        for ev in self._parser.events():
            self._handle(ev)
        # 文件结束：如果最后一帧没触发 FrameBegin，也 yield
        if self._current_frame is not None:
            self._file.frames.append(self._current_frame)
        
        return self._file

    # ---------- 事件分发 ----------
    def _handle(self, ev):
        if isinstance(ev, _HeaderParsed):
            self._file.header = ev.header

        elif isinstance(ev, _GlobalProp):
            # 根据 key 决定放入 text 还是 numeric
            if ev.key in ACMIPropertyRegistry.GLOBAL_PROPERTIES_ALLOWED_TEXT_KEYS:
                self._file.global_properties.text_properties = self._file.global_properties.text_properties or {}
                self._file.global_properties.text_properties[ev.key] = ev.value
            elif ev.key in ACMIPropertyRegistry.GLOBAL_PROPERTIES_ALLOWED_NUMERIC_KEYS:
                self._file.global_properties.numeric_properties = self._file.global_properties.numeric_properties or {}
                self._file.global_properties.numeric_properties[ev.key] = float(ev.value)
            else:
                self._file.global_properties.text_properties = self._file.global_properties.text_properties or {}
                self._file.global_properties.text_properties[ev.key] = ev.value

        elif isinstance(ev, _FrameBegin):
            self.timestamp = ev.time_offset
            if self._current_frame: # 上一帧已经填完，则加入文件
                self._file.frames.append(self._current_frame)
                self._obj_table.clear()
            self._current_frame = ACMIFrame(timestamp=ev.time_offset, objects=[])
            # print(f"开始处理帧 {self._current_frame}")

        elif isinstance(ev, _ObjectUpdate):
            # 取出旧对象或新建
            obj = ACMIObject(object_id=ev.obj_id, time_offset=self.timestamp)
            # 合并坐标和属性
            if ev.coords:
                obj.object_coordinates = ev.coords
            if ev.props:
                obj.object_properties = ev.props
            if ev.event:
                obj.object_events = ev.event
            if self._current_frame:
                self._current_frame.objects.append(obj)
            # print(f'add object {self._current_frame}')

        elif isinstance(ev, _ObjectRemove):
            self._obj_table.pop(ev.obj_id, None)


    @staticmethod
    def load_file(file_path: str, encoding: str = 'utf-8-sig') -> ACMIFile:
        loader = ACMILoader(file_path, encoding)
        return loader.load()

def load_acmi(file_path: str, encoding: str = 'utf-8-sig') -> ACMIFile:
    return ACMILoader.load_file(file_path, encoding)
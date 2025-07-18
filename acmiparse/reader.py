import os
import re
import logging
from typing import List, Dict, Optional, Generator, Union, BinaryIO
from zipfile import ZipFile, is_zipfile
# from .model import ACMIHeader, ACMIObject, ACMIFrame, ACMIFile

logger = logging.getLogger(__name__)

class ACMIFileReader:
    def __init__(self, file_path: str, encoding: str = 'utf-8-sig'):
        self.file_path = file_path
        self.encoding = encoding
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            raise FileNotFoundError(f"文件不存在: {file_path}")
        if is_zipfile(file_path):
            self.zip_file = True
        elif self.file_path.lower().endswith('.acmi'):
            self.zip_file = False
        else:
            logger.error(f"不支持的文件格式:{self.file_extension}")
            raise ValueError(f"不支持的文件格式:{self.file_extension}")

    def _open_compressed(self) -> Generator[str, None, None]:
        """尝试从压缩包中读取.acmi文件"""
        try:
            with ZipFile(self.file_path) as z:
                for name in z.namelist():
                    if name.lower().endswith('.acmi'):
                        with z.open(name) as f:
                            yield from self._read_lines(f)
                        return
            raise FileNotFoundError("压缩包中未找到.acmi文件")
        except Exception as e:
            logger.error(f"解压失败: {e}")
            raise

    def _read_lines(self, file: Union[BinaryIO, None] = None) -> Generator[str, None, None]:
        """通用读取逻辑"""
        if file:
            for line in file:
                yield line.decode(self.encoding).rstrip('\r\n')
        else:
            try:
                with open(self.file_path, 'r', encoding=self.encoding) as f:
                    for line in f:
                        yield line.rstrip('\r\n')
            except FileNotFoundError:
                logger.error(f"文件不存在: {self.file_path}")
                raise
            except Exception as e:
                logger.error(f"读取文件失败: {e}")
                raise

    def read_lines(self) -> Generator[str, None, None]:
        """读取文件行，自动处理压缩文件"""
        if self.zip_file:
            return self._open_compressed()
        else:
            return self._read_lines()

# class AcmiParser:
#     def __init__(self, reader: 'AcmiFileReader'):
#         self.reader = reader
#         self.metadata = ACMIMetadata()
#         self.frames: Dict[float, ACMIFrame] = {}  # 时间戳 -> 帧
#         self.current_time_offset: Optional[float] = None  # 当前帧时间
#         self.objects: Dict[str, ACMIObject] = {}  # ID -> 当前状态

#     def parse(self) -> ACMIFile:
#         """主解析函数"""
#         metadata: bool = True
#         for line in self.reader.read_lines():
#             if not line:
#                 continue
#             if line.startswith('//'):
#                 continue  # 跳过注释
#             if metadata:
#                 self._parse_metadata(line)
#             elif line.startswith('#'):
#                 metadata = False # 暂时认为遇到#行则元数据解析完毕
#                 self._parse_time_marker(line)
#             elif line.startswith('-'):
#                 self._parse_object_removal(line)
#             else:
#                 self._parse_object_update(line)

#         # 将临时对象状态按时间合并到帧中
#         self._flush_objects_to_frames()

#         return ACMIFile(
#             metadata=self.metadata,
#             frames=sorted(self.frames.values(), key=lambda f: f.timestamp)
#         )

#     def _parse_metadata(self, line: str):
#         """解析元数据行"""
#         line = line[1:].strip()
#         if '=' in line:
#             key, value = line.split('=', 1)
#             key = key.strip()
#             value = value.strip()
#             if key == 'FileType':
#                 self.metadata.file_type = value
#             elif key == 'FileVersion':
#                 self.metadata.file_version = value
#             elif key == 'ReferenceTime':
#                 self.metadata.reference_time = value
#             elif key == 'RecordingTime':
#                 self.metadata.recording_time = value
#             elif key == 'DataSource':
#                 self.metadata.data_source = value
#             elif key == 'DataRecorder':
#                 self.metadata.data_recorder = value
#             elif key == 'Author':
#                 self.metadata.author = value
#             elif key == 'ReferenceLatitude':
#                 self.metadata.reference_latitude = float(value)
#             elif key == 'ReferenceLongitude':
#                 self.metadata.reference_longitude = float(value)
#             else:
#                 self.metadata.other_properties[key] = value

#     def _parse_time_marker(self, line: str):
#         """解析时间戳行"""
#         match = re.match(r'#(\d+\.?\d*)', line)
#         if match:
#             self.current_time_offset = float(match.group(1))
#         else:
#             logger.warning(f"无法解析时间戳: {line}")

#     def _parse_object_update(self, line: str):
#         """解析对象更新"""
#         if self.current_time_offset is None:
#             logger.warning(f"未定义时间戳，忽略对象更新: {line}")
#             return

#         parts = line.split(',', 1)
#         object_id = int(parts[0], 16) # 对象ID为无前缀16进制

#         # 拆分属性
#         props = {}
#         if len(parts) > 1:
#             for item in parts[1].split(','):
#                 if '=' in item:
#                     k, v = item.split('=', 1)
#                     props[k.strip()] = v.strip()

#         # 解析嵌套属性
#         lat, lon, alt, U, V, Roll, Pitch, Yaw, Heading = None
#         if 'T' in props:
#             coords = props['T'].split('|')
#             if len(coords) == 3:
#                 lon = float(coords[0])  # 经度
#                 lat = float(coords[1])  # 纬度
#                 alt = float(coords[2])  # 高度
#             elif len(coords) == 5:
#                 lon = float(coords[0])  # 经度
#                 lat = float(coords[1])  # 纬度
#                 alt = float(coords[2])  # 高度
#                 U = float(coords[3])  # U
#                 V = float(coords[4])  # V
#             elif len(coords) == 6:
#                 lon = float(coords[0])  # 经度
#                 lat = float(coords[1])  # 纬度
#                 alt = float(coords[2])  # 高度
#                 Roll = float(coords[3])  # Roll
#                 Pitch = float(coords[4])  # Pitch
#                 Yaw = float(coords[5])  # Yaw
#             elif len(coords) == 9:
#                 lon = float(coords[0])  # 经度
#                 lat = float(coords[1])  # 纬度
#                 alt = float(coords[2])  # 高度
#                 Roll = float(coords[3])  # Roll
#                 Pitch = float(coords[4])  # Pitch
#                 Yaw = float(coords[5])  # Yaw
#                 U = float(coords[6])  # U
#                 V = float(coords[7])  # V
#                 Heading = float(coords[8])  # Heading
#             else:
#                 logger.warning(f"无法解析坐标: {props['T']}")
#         # 构建对象
#         obj = ACMIObject(
#             object_id=object_id,
#             time_offset=self.current_time_offset,
#             latitude=lat,
#             longitude=lon,
#             altitude=alt,
#             pitch=float(props.get('Pitch', None)) if 'Pitch' in props else None,
#             yaw=float(props.get('Yaw', None)) if 'Yaw' in props else None,
#             roll=float(props.get('Roll', None)) if 'Roll' in props else None,
#             velocity=float(props.get('Velocity', None)) if 'Velocity' in props else None,
#             type_=props.get('Type'),
#             name=props.get('Name'),
#             callsign=props.get('Callsign'),
#             shape=props.get('Shape'),
#             width=float(props.get('Width')) if 'Width' in props else None,
#             height=float(props.get('Height')) if 'Height' in props else None,
#             radius=float(props.get('Radius')) if 'Radius' in props else None,
#             other_properties={k: v for k, v in props.items() if k not in ['T', 'Pitch', 'Yaw', 'Roll', 'Velocity', 'Type', 'Name', 'Callsign', 'Shape', 'Width', 'Height', 'Radius']}
#         )

#         # 更新对象状态
#         self.objects[object_id] = obj

#     def _parse_object_removal(self, line: str):
#         """解析对象移除"""
#         if self.current_time_offset is None:
#             logger.warning(f"未定义时间戳，忽略对象移除: {line}")
#             return
#         object_id = line[1:].strip()
#         if object_id in self.objects:
#             del self.objects[object_id]

#     def _flush_objects_to_frames(self):
#         """将临时对象状态写入帧"""
#         for time_offset, frame in self.frames.items():
#             frame.objects.clear()
#         for obj in self.objects.values():
#             time_offset = obj.time_offset
#             if time_offset not in self.frames:
#                 self.frames[time_offset] = ACMIFrame(timestamp=time_offset, objects=[])
#             self.frames[obj.time_offset].objects.append(obj)
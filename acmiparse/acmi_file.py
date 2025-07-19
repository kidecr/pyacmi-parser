# acmi_file.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Iterable, Any
from collections import defaultdict
import csv
import io
from .model import *

import pandas as pd  # 可选依赖，仅用于 to_df

# ---------- 基础工具 ----------
@dataclass(slots=True)
class FrameObjectRef:
    """定位对象：第几帧、帧内第几个"""
    frame_index: int
    object_index: int


@dataclass(slots=True, frozen=True)
class IdView:
    """
    轻量级代理，代表“某个 object_id 的全部出现记录”
    支持属性式列访问、切片、导出 csv/df
    """
    _id: int
    _file: ACMIFile

    # ---------- 魔法方法 ----------
    def __getattr__(self, col: str) -> List[Any]:
        """支持 obj.altitude 形式"""
        if col in self._file.columns:
            return self._file._column_for_id(self._id, col)
        raise AttributeError(col)

    def __getitem__(self, item):
        return self._file.id_objects(self._id)[item]

    def __iter__(self):
        return iter(self._file.id_objects(self._id))

    def __len__(self):
        return self._file.id_count(self._id)

    # ---------- 导出 ----------
    def to_csv(self, *, delimiter: str = ',', include_header: bool = True) -> str:
        return self._file._id_to_csv([self._id], delimiter=delimiter,
                                     include_header=include_header)

    def to_df(self) -> pd.DataFrame:
        return self._file._id_to_df([self._id])


class ObjectCollection:
    """dict-like 代理，支持 acmi.objects[12345] / acmi.objects[:]"""
    def __init__(self, file: ACMIFile):
        self._file = file

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [o for frame in self._file.frames for o in frame.objects][key]
        if isinstance(key, int):
            return IdView(key, self._file)
        raise TypeError('key must be int or slice')

    def __iter__(self):
        return (o for frame in self._file.frames for o in frame.objects)

    def __len__(self):
        return sum(len(f.objects) for f in self._file.frames)


# ---------- 主文件模型 ----------
@dataclass
class ACMIFile:
    header: 'ACMIHeader'
    global_properties: 'ACMIGlobalProperties'
    frames: List['ACMIFrame']

    # ---------- 内部 ----------
    _id_index: Dict[int, List[FrameObjectRef]] = field(
        init=False, repr=False, default_factory=lambda: defaultdict(list)
    )
    _index_built: bool = field(init=False, repr=False, default=False)

    # ---------- 公开属性 ----------
    @property
    def ids(self) -> List[int]:
        """全部出现过的 object_id(升序去重)"""
        self._ensure_index()
        return sorted(self._id_index)

    @property
    def objects(self) -> ObjectCollection:
        """dict-like 代理"""
        return ObjectCollection(self)

    @property
    def columns(self) -> List[str]:
        """所有可用扁平列名，按字母序"""
        try:
            obj = next(iter(self.objects))
        except StopIteration:
            return []
        return self._auto_columns([obj])

    # ---------- 函数式接口(保留向后兼容) ----------
    def id_all(self) -> List[int]:
        return self.ids

    def id_count(self, object_id: int) -> int:
        self._ensure_index()
        return len(self._id_index.get(object_id, []))

    def id_objects(self, object_id: int) -> List['ACMIObject']:
        self._ensure_index()
        return [self._get_obj(ref) for ref in self._id_index.get(object_id, [])]

    def id_column(self, object_id: int, col: str) -> List[Any]:
        return self._column_for_id(object_id, col)

    def id_to_csv(
        self,
        object_ids: Iterable[int] | None = None,
        columns: Iterable[str] | None = None,
        *,
        delimiter: str = ',',
        include_header: bool = True,
    ) -> str:
        """指定 ID(或全部)导出 CSV"""
        if object_ids is None:
            object_ids = self.ids
        rows = [o for oid in object_ids for o in self.id_objects(oid)]
        if not rows:
            return ''

        columns = list(columns) if columns else self._auto_columns(rows)
        table = [[self._deep_get(o, c) for c in columns] for o in rows]

        buf = io.StringIO()
        writer = csv.writer(buf, delimiter=delimiter)
        if include_header:
            writer.writerow(columns)
        writer.writerows(table)
        return buf.getvalue()

    def id_to_df(
        self,
        object_ids: Iterable[int] | None = None,
        columns: Iterable[str] | None = None,
    ) -> pd.DataFrame:
        csv_str = self.id_to_csv(object_ids, columns, delimiter=',')
        return pd.read_csv(io.StringIO(csv_str))

    # ---------- 内部辅助 ----------
    def _ensure_index(self) -> None:
        if self._index_built:
            return
        self._build_id_index()
        self._index_built = True

    def _build_id_index(self) -> None:
        self._id_index.clear()
        for f_idx, frame in enumerate(self.frames):
            for o_idx, obj in enumerate(frame.objects):
                self._id_index[obj.object_id].append(
                    FrameObjectRef(f_idx, o_idx)
                )

    def _get_obj(self, ref: FrameObjectRef) -> 'ACMIObject':
        return self.frames[ref.frame_index].objects[ref.object_index]

    def _column_for_id(self, oid: int, col: str) -> List[Any]:
        return self.id_column(oid, col)

    def _id_to_csv(self, ids, **kw):
        return self.id_to_csv(ids, **kw)

    def _id_to_df(self, ids):
        return self.id_to_df(ids)

    @staticmethod
    def _deep_get(obj: Any, path: str) -> Any:
        for part in path.split('.'):
            obj = getattr(obj, part, None)
        return obj

    @staticmethod
    def _auto_columns(rows: List['ACMIObject']) -> List[str]:
        cols = set()
        for obj in rows:
            for f in obj.__dataclass_fields__:
                val = getattr(obj, f)
                if val is None:
                    continue
                if hasattr(val, '__dataclass_fields__'):
                    for sub in val.__dataclass_fields__:
                        cols.add(f"{f}.{sub}")
                else:
                    cols.add(f)
        return sorted(cols)
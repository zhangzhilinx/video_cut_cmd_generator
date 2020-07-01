import json
from typing import Iterable, List

import jsonschema

from core import Moment


class ModelData:
    """Core data class of program

    Thread unsafe
    """

    schema = {
        'type': 'object',
        'required': ['src_filename', 'src_path_dir', 'intervals'],
        'properties': {
            'src_filename': {'type': 'string'},
            'src_path_dir': {'type': 'string'},
            'dst_path_dir': {'type': 'string'},
            # 'src_duration': {'type': 'integer', 'minimum': 0},
            # 'src_size': {'type': 'integer', 'minimum': 0},
            'intervals': {
                'type': 'array',
                'items': {
                    'type': 'array',
                    'minItems': 2,
                    'maxItems': 2,
                    'items': {
                        'type': 'array',
                        'minItems': 3,
                        'maxItems': 3,
                        'items': {'type': 'integer', 'minimum': 0}
                    },
                }
            }
        }
    }

    def __init__(self, kv: dict = None, check=True):
        if isinstance(kv, dict) \
                and (not check or self.validate(kv)):
            self._kv = kv
        else:
            self._kv = {
                'src_filename': '',
                'src_path_dir': '',
                'dst_path_dir': '',
                # 'src_duration': 0,
                # 'src_size': 0,
                'intervals': []
            }

    @classmethod
    def validate(cls, kv: dict) -> bool:
        try:
            if not isinstance(kv, dict):
                return False
            # 验证JSON数据是否合法
            jsonschema.validate(instance=kv,
                                schema=cls.schema)
            # 验证时间是否合法
            for interval in kv['intervals']:
                begin, end = interval
                begin = Moment.from_list(begin)
                end = Moment.from_list(end)
                if begin is None \
                        or end is None \
                        or begin > end:
                    return False
            return True
        except jsonschema.ValidationError:
            return False
        except:
            return False

    @classmethod
    def from_json(cls, str_json, *args, **kwargs):
        if 'encoding' not in kwargs:
            kwargs['encoding'] = 'utf8'
        try:
            kv = json.loads(str_json, *args, **kwargs)
            if cls.validate(kv):
                return ModelData(kv, check=False)
            else:
                return None
        except:
            # TODO JSON解析失败
            return None

    def to_json(self, *args, **kwargs):
        if 'ensure_ascii' not in kwargs:
            kwargs['ensure_ascii'] = False
        return json.dumps(
            self._kv,
            # indent=2,
            *args,
            **kwargs,
        )

    @property
    def src_filename(self) -> str:
        return self._kv.get('src_filename', '')

    @src_filename.setter
    def src_filename(self, value: str):
        if isinstance(value, str):
            self._kv['src_filename'] = value

    @property
    def src_path_dir(self) -> str:
        return self._kv.get('src_path_dir', '')

    @src_path_dir.setter
    def src_path_dir(self, value: str):
        if isinstance(value, str):
            self._kv['src_path_dir'] = value

    @property
    def dst_path_dir(self) -> str:
        return self._kv.get('dst_path_dir', '')

    @dst_path_dir.setter
    def dst_path_dir(self, value: str):
        if isinstance(value, str):
            self._kv['dst_path_dir'] = value

    # @property
    # def src_duration(self) -> int:
    #     return self._kv.get('src_duration', 0)
    #
    # @src_duration.setter
    # def src_duration(self, value: int):
    #     if isinstance(value, int) and value >= 0:
    #         self._kv['src_duration'] = value
    #
    # @property
    # def src_size(self) -> int:
    #     return self._kv.get('src_size', 0)
    #
    # @src_size.setter
    # def src_size(self, value: int):
    #     if isinstance(value, int) and value >= 0:
    #         self._kv['src_duration'] = value

    def intervals_iter(self) -> Iterable[List[List[int]]]:
        return iter(self._kv.get('intervals', []))

    def intervals_size(self) -> int:
        return len(self._kv.get('intervals', ()))

    def clear_intervals(self) -> None:
        self._kv.get('intervals', []).clear()

    def get_interval(self, row: int, col: int = -1):
        row = self._kv['intervals'][row]
        if col == -1:
            row_0, row_1 = row[0], row[1]
            return [Moment(row_0[0], row_0[1].row_0[2]),
                    Moment(row_1[0], row_1[1].row_1[2])]
        else:
            row_x = row[0 if col == 0 else 1]
            return Moment(row_x[0], row_x[1], row_x[2])

    def get_interval_unwrap(self, row: int, col: int = -1):
        row = self._kv['intervals'][row]
        if col == -1:
            return [row[0], row[1]]
        else:
            return row[0 if col == 0 else 1]

    def add_interval(self, begin: Moment = None, end: Moment = None) -> bool:
        intervals = self._kv['intervals']
        if intervals is not None:
            intervals.append([
                [begin.hour, begin.mins, begin.secs],
                [end.hour, end.mins, end.secs]
            ])
            return True
        return False

    def del_interval(self, index: int = 0) -> bool:
        intervals = self._kv['intervals']
        if intervals and 0 <= index < len(intervals):
            del intervals[index]
            return True
        return False

    def set_interval(self, index: int = 0, begin: Moment = None, end: Moment = None) -> bool:
        intervals = self._kv['intervals']
        if intervals and 0 <= index < len(intervals):
            interval = intervals[index]
            if begin is not None:
                interval[0] = [begin.hour, begin.mins, begin.secs]
            if end is not None:
                interval[1] = [end.hour, end.mins, end.secs]
            return True
        return False

    def move_interval(self, index: int = 0, offset: int = 0) -> bool:
        intervals = self._kv['intervals']
        if intervals \
                and 0 <= index < len(intervals) \
                and 0 <= index + offset < len(intervals):
            interval = intervals[index]
            if offset > 0:
                for i in range(index, index + offset):
                    intervals[i] = intervals[i + 1]
                intervals[index + offset] = interval
            elif offset < 0:
                for i in range(index, index + offset, -1):
                    intervals[i] = intervals[i - 1]
                intervals[index + offset] = interval
            return True
        return False

    def insert_interval(self, index: int = 0, begin: Moment = None, end: Moment = None) -> bool:
        intervals = self._kv['intervals']
        if intervals:
            intervals.insert(index,
                             [
                                 [begin.hour, begin.mins, begin.secs],
                                 [end.hour, end.mins, end.secs]
                             ])
            return True
        return False

import re
from typing import Union


# TODO 采用decimal方式，使得在诸如'0.45'*gb + '0.1'*mb这类的运算也能保留较高精度
# TODO 重载运算符
#      实现自由加减、除法、系数乘除（系数可是整型、浮点、字符串、高精度）、比较等便捷操作
# TODO bytes(*1000) / bibytes(*1024)
class BytesMeasure(object):
    EXP_SPLIT = re.compile(r'(\d*\.?\d+)([a-z]+)')
    # SHORT = ('b', 'kib', 'mib', 'gib', 'tib', 'pib', 'eib', 'zib', 'yib')
    SHORT = ('b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb')

    # MIDDLE = tuple([_ + 'ytes' for _ in SHORT])
    # LONG = ('bytes', 'kilobytes', 'megabytes', 'gigabytes', 'terabytes',
    #         'petabytes', 'exabytes', 'zettabytes')

    def __init__(self, bytes_val: Union[int, str] = 0, system: int = 1024):
        super(BytesMeasure, self).__init__()

        if isinstance(bytes_val, int):
            self._bytes_num = bytes_val
        else:
            self._bytes_num = self.bytes_str2int(bytes_val, system)
        self._system = system

    @classmethod
    def bytes_str2int(cls, bytes_str: str, system: int = 1024):
        groups = cls.EXP_SPLIT.match(bytes_str.lower()).groups()
        assert groups is not None
        n, m = groups
        i = cls.SHORT.index(m)  # 找不到对应单位时抛出ValueError异常
        if '.' in n:
            raise NotImplementedError()
        n = float(n) if '.' in n else int(n)
        return n * (1024 ** i)

    def simplify(self):
        raise NotImplementedError()


if __name__ == '__main__':
    pass
    # b, kb, mb, gb, tb, pb, eb, zb, yb = tuple(
    #     map(
    #         BytesMeasure,
    #         ('1b', '1kb', '1mb', '1gb', '1tb', '1pb', '1eb', '1zb', '1yb')
    #     )
    # )
    # B, KB, MB, GB, TB, PB, EB, ZB, YB = b, kb, mb, gb, tb, pb, eb, zb, yb
    # x = 1 * b + 32 * kb + 46 * mb

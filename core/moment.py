from functools import reduce, total_ordering


@total_ordering
class Moment:
    def __init__(self, hour: int = 0, mins: int = 0, secs: int = 0):
        self.hour = hour
        self.mins = mins
        self.secs = secs

    def __add__(self, other):
        x, y = self.to_secs(), other.to_secs()
        z = x + y
        secs = z % 60
        z //= 60
        mins = z % 60
        z //= 60
        hour = z
        return Moment(hour, mins, secs)

    def __sub__(self, other):
        x, y = self.to_secs(), other.to_secs()
        z = x - y if x > y else 0
        secs = z % 60
        z //= 60
        mins = z % 60
        z //= 60
        hour = z
        return Moment(hour, mins, secs)

    def __lt__(self, other):
        return self.to_secs() < other.to_secs()

    def __eq__(self, other):
        return self.to_secs() == other.to_secs()

    @staticmethod
    def validate(hour: int, mins: int, secs: int) -> bool:
        return hour >= 0 and 0 <= mins <= 59 and 0 <= secs <= 59

    @classmethod
    def from_args(cls, hour: int, mins: int, secs: int):
        return Moment(hour, mins, secs) \
            if cls.validate(hour, mins, secs) \
            else None

    @classmethod
    def from_list(cls, lst):
        return cls.from_args(*lst) \
            if len(lst) == 3 \
            else None

    @classmethod
    def from_secs(cls, secs: int):
        z = secs
        secs = z % 60
        z //= 60
        mins = z % 60
        z //= 60
        hour = z
        return Moment(hour, mins, secs)

    def to_secs(self) -> int:
        return reduce(
            lambda x, y: x * 60 + y,
            (self.hour, self.mins, self.secs)
        )

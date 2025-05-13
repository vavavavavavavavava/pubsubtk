from enum import StrEnum, auto


class AutoNamedTopic(StrEnum):
    """
    - メンバー名を auto() で name.lower() に
    - __new__ で {ClassName}.{value} に自動変換
    - str() や比較でそのまま使える
    """

    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

    def __new__(cls, value):
        # ここでクラス名プレフィックスを追加
        full = f"{cls.__name__}.{value}"
        obj = str.__new__(cls, full)
        obj._value_ = full
        return obj

    def __str__(self):
        return self.value


class DefaultNavigateTopic(AutoNamedTopic):
    SWITCH_CONTAINER = auto()
    OPEN_SUBWINDOW = auto()
    CLOSE_SUBWINDOW = auto()
    CLOSE_ALL_SUBWINDOWS = auto()


class DefaultUpdateTopic(AutoNamedTopic):
    STATE_CHANGED = auto()
    STATE_ADDED = auto()

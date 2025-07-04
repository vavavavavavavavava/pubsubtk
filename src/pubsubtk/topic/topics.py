# topics.py - PubSub トピック列挙型の定義

"""
src/pubsubtk/topic/topics.py

アプリケーションで使用する PubSub トピック列挙型を提供します。
"""

from enum import StrEnum, auto


class AutoNamedTopic(StrEnum):
    """
    Enumメンバー名を自動で小文字化し、クラス名のプレフィックス付き文字列を値とする列挙型。

    - メンバー値は "ClassName.member" 形式の文字列
    - str()や比較でそのまま利用可能
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
    """
    標準的な画面遷移・ウィンドウ操作用のPubSubトピック列挙型。
    """

    SWITCH_CONTAINER = auto()
    SWITCH_SLOT = auto()
    OPEN_SUBWINDOW = auto()
    CLOSE_SUBWINDOW = auto()
    CLOSE_ALL_SUBWINDOWS = auto()


class DefaultUpdateTopic(AutoNamedTopic):
    """
    標準的な状態更新通知用のPubSubトピック列挙型。
    """

    UPDATE_STATE = auto()
    ADD_TO_LIST = auto()
    ADD_TO_DICT = auto()
    REPLACE_STATE = auto()
    STATE_CHANGED = auto()
    STATE_ADDED = auto()
    STATE_UPDATED = auto()
    DICT_ADDED = auto()


class DefaultProcessorTopic(AutoNamedTopic):
    """
    標準的なプロセッサ管理のPubSubトピック列挙型。
    """

    REGISTER_PROCESSOR = auto()
    DELETE_PROCESSOR = auto()


class DefaultUndoTopic(AutoNamedTopic):
    """
    Undo/Redo機能用のPubSubトピック列挙型。
    """

    ENABLE_UNDO_REDO = auto()
    DISABLE_UNDO_REDO = auto()
    UNDO = auto()
    REDO = auto()
    STATUS_CHANGED = auto()
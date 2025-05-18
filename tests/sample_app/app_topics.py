from enum import auto

from pubsubtk import AutoNamedTopic


class TaskTopic(AutoNamedTopic):
    """タスク操作用のカスタムトピック"""

    ADD_TASK = auto()
    TOGGLE_TASK = auto()
    SELECT_TASK = auto()
    DELETE_TASK = auto()
